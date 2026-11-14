"""Meaningful rejection cases for untrusted file content and explicit alphabets."""
import hashlib
import io

import numpy as np
import pytest

from entropy_oracle.data import load_discrete_bytes, load_discrete_file


def npy_bytes(array):
    stream = io.BytesIO()
    np.save(stream, array, allow_pickle=True)
    return stream.getvalue()


@pytest.mark.parametrize("dtype,values,code", [
    ("uint8", [0, 1, 255], "u1"),
    ("uint16le", [0, 256, 65535], "<u2"),
    ("uint32le", [0, 65536, 2**32-1], "<u4"),
])
def test_raw_binary_endian_and_provenance(dtype, values, code):
    payload = np.array(values, dtype=code).tobytes()
    result = load_discrete_bytes(payload, r"C:\private\capture.BIN", max(values)+1, dtype=dtype)
    np.testing.assert_array_equal(result.x, values)
    assert result.x.dtype == np.int64
    assert result.alphabet_size == max(values)+1
    assert result.oracle_probs is None
    assert result.metadata["source"] == "file"
    assert result.metadata["stationary"] is None
    assert result.metadata["filename"] == "capture.BIN"
    assert result.metadata["sha256"] == hashlib.sha256(payload).hexdigest()
    assert result.metadata["dtype"] == dtype
    assert result.metadata["n"] == len(values)


def test_explicit_binary_little_endian():
    result = load_discrete_bytes(b"\x01\x02\x00\x01", "x.bin", 65536, dtype="uint16le")
    np.testing.assert_array_equal(result.x, [513, 256])


def test_binary_byte_length_must_match_declared_dtype():
    with pytest.raises(ValueError, match="byte length"):
        load_discrete_bytes(b"\x01\x02\x03", "x.bin", 65536, dtype="uint16le")


@pytest.mark.parametrize("payload", [
    b"0,1,2\n", b"0\n1\n2\n", b"0 1 2\n", b"0\t1\t2", b"0.0,1e0,2.000", b'"0","1","2"',
    b"\xef\xbb\xbf0\n1\n2\n", b"\n0\n\n1\n2\n",
])
def test_text_sequences(payload):
    result = load_discrete_bytes(payload, "values.csv", 3)
    np.testing.assert_array_equal(result.x, [0, 1, 2])
    assert result.metadata["sha256"] == hashlib.sha256(payload).hexdigest()


def test_exact_text_integers_do_not_round_through_float():
    result = load_discrete_bytes(b"9007199254740993\n9007199254740992", "exact.txt", 2**54)
    np.testing.assert_array_equal(result.x, [9007199254740993, 9007199254740992])
    with pytest.raises(ValueError, match="integers"):
        load_discrete_bytes(b"0.99999999999999999999999999999999999999", "exact.txt", 2)


@pytest.mark.parametrize("payload", [b"0 1\n1 0", b"0,1\n1,0", b"0,1\n2", b"0,,1", b"0,1,", b"0\n,\n1"])
def test_reject_multicolumn_ragged_and_missing_text(payload):
    with pytest.raises(ValueError):
        load_discrete_bytes(payload, "bad.txt", 3)


@pytest.mark.parametrize("payload", [b"-1", b"2", b"0.5", b"NaN", b"inf", b"-inf", b"abc", b"\xff", b"0\x00"])
def test_reject_invalid_text_symbols(payload):
    with pytest.raises(ValueError):
        load_discrete_bytes(payload, "bad.csv", 2)


@pytest.mark.parametrize("shape", [(3,), (1, 3), (3, 1)])
def test_npy_one_dimensional_or_single_row_column(shape):
    values = np.array([0, 2, 1], dtype=np.uint16).reshape(shape)
    result = load_discrete_bytes(npy_bytes(values), "sample.npy", 3)
    np.testing.assert_array_equal(result.x, [0, 2, 1])
    assert result.metadata["dtype"] == "uint16"


def test_npy_integral_floats_and_boolean_allowed():
    for values in (np.array([0.0, 1.0]), np.array([False, True])):
        result = load_discrete_bytes(npy_bytes(values), "sample.npy", 2)
        np.testing.assert_array_equal(result.x, [0, 1])


@pytest.mark.parametrize("values", [
    np.array([{"payload": "not unpickled"}], dtype=object),
    np.array(["0", "1"]), np.array([1+0j]),
    np.array([(0,)], dtype=[("value", "i4")]),
    np.array([0.1]), np.array([np.nan]), np.array([np.inf]),
    np.array([-1]), np.array([2]), np.array([2**63], dtype=np.uint64),
    np.array([[0, 1], [1, 0]]), np.array([[[1]]]), np.array(1), np.array([]),
])
def test_reject_unsafe_npy_shapes_dtypes_and_values(values):
    with pytest.raises(ValueError):
        load_discrete_bytes(npy_bytes(values), "bad.npy", 2)


def test_npy_declared_shape_checked_before_allocating():
    stream = io.BytesIO()
    np.lib.format.write_array_header_1_0(stream, {"descr": "<u8", "fortran_order": False, "shape": (2**50,)})
    with pytest.raises(ValueError, match="payload size"):
        load_discrete_bytes(stream.getvalue(), "huge.npy", 2)


def test_npy_truncation_and_trailing_content_rejected():
    payload = npy_bytes(np.array([0, 1], dtype=np.uint8))
    for malformed in (payload[:-1], payload+b"trailing"):
        with pytest.raises(ValueError, match="payload size"):
            load_discrete_bytes(malformed, "bad.npy", 2)


@pytest.mark.parametrize("alphabet", [None, 0, -1, 2.0, "2", True, 2**63+1])
def test_alphabet_must_be_explicit_positive_integer(alphabet):
    with pytest.raises(ValueError, match="alphabet_size"):
        load_discrete_bytes(b"0", "x.txt", alphabet)


def test_alphabet_not_inferred_or_symbols_relabelled():
    result = load_discrete_bytes(b"3\n3\n3", "constant.txt", 256)
    np.testing.assert_array_equal(result.x, [3, 3, 3])
    assert result.alphabet_size == 256
    with pytest.raises(TypeError):
        load_discrete_bytes(b"0", "x.txt")
    with pytest.raises(ValueError, match="outside"):
        load_discrete_bytes(b"3\n3", "constant.txt", 2)


@pytest.mark.parametrize("payload", [b"", b" \n\t"])
def test_empty_inputs_rejected(payload):
    with pytest.raises(ValueError, match="empty"):
        load_discrete_bytes(payload, "x.txt", 2)


def test_size_limit_for_bytes_and_files(tmp_path):
    with pytest.raises(ValueError, match="max_bytes"):
        load_discrete_bytes(b"\x00\x01\x00", "x.bin", 2, max_bytes=2)
    path = tmp_path/"capture.bin"
    path.write_bytes(b"\x00\x01\x00")
    with pytest.raises(ValueError, match="max_bytes"):
        load_discrete_file(path, 2, max_bytes=2)
    result = load_discrete_file(path, 2, max_bytes=3)
    np.testing.assert_array_equal(result.x, [0, 1, 0])
    assert result.metadata["filename"] == "capture.bin"
    assert str(tmp_path) not in str(result.metadata)


def test_no_directory_or_unknown_format(tmp_path):
    with pytest.raises(ValueError, match="regular file"):
        load_discrete_file(tmp_path, 2)
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_discrete_bytes(b"0", "x.exe", 2)
    with pytest.raises(ValueError, match="dtype"):
        load_discrete_bytes(b"0", "x.bin", 256, dtype="int64")


def test_memoryview_byte_size_used_not_element_count():
    payload = memoryview(np.array([0, 1], dtype=np.uint32))
    with pytest.raises(ValueError, match="max_bytes"):
        load_discrete_bytes(payload, "x.bin", 2, dtype="uint32le", max_bytes=2)
