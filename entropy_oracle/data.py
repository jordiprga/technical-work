"""Explicit, lossless ingestion of already-discretized observation sequences.

No alphabet is inferred, symbols are never relabeled, and no quantization or
normalization is fitted to the observations. This module performs no I/O except
reading the one path explicitly supplied to :func:`load_discrete_file`.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import math
import operator
from pathlib import Path
import stat

import numpy as np

from .sources import SourceData

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
_BINARY_DTYPES = {
    "uint8": np.dtype("u1"),
    "uint16le": np.dtype("<u2"),
    "uint32le": np.dtype("<u4"),
}
_INT64_LIMIT = 1 << 63


def _integer_parameter(value, name, *, maximum=None):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an explicitly declared positive integer")
    try:
        result = operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an explicitly declared positive integer") from exc
    if result < 1 or (maximum is not None and result > maximum):
        suffix = f" and at most {maximum}" if maximum is not None else ""
        raise ValueError(f"{name} must be positive{suffix}")
    return int(result)


def _validate_alphabet(alphabet_size):
    # Stored values use int64; A=2**63 still permits its largest representable
    # nonnegative integer as a symbol. Downstream models may impose smaller A.
    return _integer_parameter(alphabet_size, "alphabet_size", maximum=_INT64_LIMIT)


def _vector_shape(shape):
    if len(shape) == 1:
        return
    if len(shape) == 2 and 1 in shape:
        return
    raise ValueError("Expected a one-dimensional sequence or one row/column; multicolumn data are not accepted")


def _validated_symbols(array, alphabet_size):
    _vector_shape(array.shape)
    if not array.size:
        raise ValueError("The sequence is empty")
    if array.dtype.kind not in "biuf":
        raise ValueError("Symbols must have a real numeric dtype; object, string, structured and complex arrays are refused")
    if array.dtype.kind == "f":
        if not np.isfinite(array).all():
            raise ValueError("Symbols must be finite")
        if not np.equal(array, np.floor(array)).all():
            raise ValueError("Symbols must be integers; no implicit quantization is performed")
    minimum = array.min().item()
    maximum = array.max().item()
    if minimum < 0:
        raise ValueError("Symbols must be nonnegative")
    if maximum >= alphabet_size:
        raise ValueError(f"Symbol {maximum} lies outside the declared alphabet [0, {alphabet_size})")
    if maximum >= _INT64_LIMIT:
        raise ValueError("Symbols must fit a signed 64-bit integer")
    return np.asarray(array, dtype=np.int64).reshape(-1).copy()


def _read_npy(payload):
    """Check the uncompressed allocation size before asking NumPy to load it."""
    stream = io.BytesIO(payload)
    try:
        version = np.lib.format.read_magic(stream)
        if version == (1, 0):
            shape, _, dtype = np.lib.format.read_array_header_1_0(stream, max_header_size=10_000)
        elif version in {(2, 0), (3, 0)}:
            # Numeric, unstructured dtype headers contain only ASCII, so their
            # v3 UTF-8 header is also correctly decoded by the public v2 reader.
            shape, _, dtype = np.lib.format.read_array_header_2_0(stream, max_header_size=10_000)
        else:
            raise ValueError(f"Unsupported NPY format version {version}")
    except (ValueError, TypeError, EOFError, OverflowError) as exc:
        raise ValueError(f"Invalid NPY header: {exc}") from exc
    _vector_shape(shape)
    if dtype.hasobject or dtype.kind not in "biuf":
        raise ValueError("NPY object, string, structured and complex arrays are refused; pickle loading is disabled")
    count = math.prod(shape)
    if count < 1:
        raise ValueError("The sequence is empty")
    expected_bytes = count * dtype.itemsize
    if expected_bytes != len(payload) - stream.tell():
        raise ValueError("NPY payload size does not match its declared shape and dtype (truncated or trailing data)")
    try:
        array = np.load(io.BytesIO(payload), allow_pickle=False, max_header_size=10_000)
    except (ValueError, TypeError, EOFError, OverflowError) as exc:
        raise ValueError(f"Invalid NPY data: {exc}") from exc
    return array, str(array.dtype)


def _read_text(payload, alphabet_size):
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Text observations must be valid UTF-8") from exc
    if not text.strip():
        raise ValueError("The sequence is empty")
    if "\x00" in text:
        raise ValueError("Text observations cannot contain NUL bytes")
    try:
        if "," in text:
            rows = [row for row in csv.reader(io.StringIO(text), skipinitialspace=True, strict=True)
                    if row and not (len(row) == 1 and not row[0].strip())]
        else:
            rows = [line.split() for line in text.splitlines() if line.strip()]
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV data: {exc}") from exc
    if not rows:
        raise ValueError("The sequence is empty")
    columns = len(rows[0])
    if any(len(row) != columns for row in rows):
        raise ValueError("Ragged or multicolumn data are not accepted")
    if len(rows) > 1 and columns > 1:
        raise ValueError("Expected one row or one column of symbols; multicolumn data are not accepted")
    symbols = np.empty(len(rows) * columns, dtype=np.int64)
    index = 0
    for row in rows:
        for token in row:
            token = token.strip()
            if not token:
                raise ValueError("Missing numeric symbol in text observations")
            try:
                # Decimal avoids rounding 2**53+1 to 2**53 and never silently
                # turns a near-integer decimal into an integer. Scientific
                # notation and decimal notation are accepted when exact.
                value = Decimal(token)
            except InvalidOperation as exc:
                raise ValueError(f"Invalid numeric symbol at position {index}") from exc
            if not value.is_finite():
                raise ValueError("Symbols must be finite")
            if value != value.to_integral_value():
                raise ValueError("Symbols must be integers; no implicit quantization is performed")
            if value < 0 or value >= alphabet_size:
                raise ValueError(f"Symbol at position {index} lies outside the declared alphabet [0, {alphabet_size})")
            symbols[index] = int(value)
            index += 1
    return symbols, "int64"


def load_discrete_bytes(payload, filename, alphabet_size, dtype="uint8", max_bytes=DEFAULT_MAX_BYTES):
    """Load an explicitly labeled sequence from bytes, including UI uploads.

    Supported suffixes are ``.bin``, ``.npy``, ``.csv`` and ``.txt``. ``dtype``
    chooses raw binary interpretation only: uint8, uint16le or uint32le. NPY
    retains its declared numeric interpretation; text is parsed exactly.
    ``alphabet_size`` is required, even when all observed symbols are identical.
    """
    alphabet_size = _validate_alphabet(alphabet_size)
    max_bytes = _integer_parameter(max_bytes, "max_bytes")
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("payload must be bytes, bytearray or memoryview")
    payload_size = payload.nbytes if isinstance(payload, memoryview) else len(payload)
    if payload_size > max_bytes:
        raise ValueError(f"Input exceeds max_bytes={max_bytes}")
    if payload_size == 0:
        raise ValueError("The sequence is empty")
    payload = bytes(payload)
    if not isinstance(filename, (str, Path)):
        raise TypeError("filename must be a string or Path")
    basename = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
    extension = Path(basename).suffix.lower()
    if extension not in {".bin", ".npy", ".csv", ".txt"}:
        raise ValueError("Unsupported file format; expected .bin, .npy, .csv or .txt")
    if dtype not in _BINARY_DTYPES:
        raise ValueError(f"Unsupported binary dtype {dtype!r}; choose {list(_BINARY_DTYPES)}")
    if extension == ".bin":
        binary_dtype = _BINARY_DTYPES[dtype]
        if len(payload) % binary_dtype.itemsize:
            raise ValueError(f"Binary byte length must be a multiple of {binary_dtype.itemsize} for {dtype}")
        array = np.frombuffer(payload, dtype=binary_dtype)
        actual_dtype = dtype
    elif extension == ".npy":
        array, actual_dtype = _read_npy(payload)
    else:
        array, actual_dtype = _read_text(payload, alphabet_size)
    symbols = _validated_symbols(array, alphabet_size)
    digest = hashlib.sha256(payload).hexdigest()
    metadata = {
        "source": "file",
        "filename": basename,
        "format": extension[1:],
        "dtype": actual_dtype,
        "n": int(symbols.size),
        "byte_count": len(payload),
        "sha256": digest,
        "alphabet_size": alphabet_size,
        "stationary": None,
        "oracle_scope": "Unknown real-data source; no theoretical oracle is asserted",
        "preprocessing": "None: original symbols and chronological order retained",
    }
    return SourceData(x=symbols, alphabet_size=alphabet_size, oracle_probs=None, metadata=metadata)


def load_discrete_file(path, alphabet_size, dtype="uint8", max_bytes=DEFAULT_MAX_BYTES):
    """Read one regular local file with a bounded read and original-byte digest."""
    alphabet_size = _validate_alphabet(alphabet_size)
    max_bytes = _integer_parameter(max_bytes, "max_bytes")
    path = Path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Input must be a regular file")
    if info.st_size > max_bytes:
        raise ValueError(f"Input exceeds max_bytes={max_bytes}")
    with path.open("rb") as handle:
        payload = handle.read(max_bytes + 1)
    return load_discrete_bytes(payload, path.name, alphabet_size=alphabet_size,
                               dtype=dtype, max_bytes=max_bytes)
