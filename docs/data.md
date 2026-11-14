# Loading real discrete observations

Real inputs must already be discretized, with symbols in `0, ..., A-1`. Declare the physical or acquisition alphabet size `A` explicitly. The loader never infers it from the largest observed symbol, relabels symbols, fits quantization thresholds, estimates normalization parameters, or reorders observations. For example, a sequence containing only symbol `3` with declared `A=256` remains a 256-symbol source containing observations of `3`.

```python
from entropy_oracle.data import load_discrete_file, load_discrete_bytes

source = load_discrete_file("capture.bin", alphabet_size=256, dtype="uint8")
print(source.x, source.metadata["sha256"])

# A browser upload supplies bytes directly; it need not be written to disk.
source = load_discrete_bytes(uploaded_bytes, "capture.npy", alphabet_size=16)
```

The return value is the same `SourceData` structure used by the synthetic generators. `x` is a one-dimensional `numpy.int64` array in original chronological order. `oracle_probs` is `None`: measured samples alone do not supply a theoretical optimum. Stationarity is explicitly unknown (`metadata["stationary"] is None`).

## Accepted formats

| Format | Interpretation |
|---|---|
| `.bin`, `dtype="uint8"` | One unsigned 8-bit symbol per byte |
| `.bin`, `dtype="uint16le"` | One unsigned little-endian 16-bit symbol per two bytes |
| `.bin`, `dtype="uint32le"` | One unsigned little-endian 32-bit symbol per four bytes |
| `.npy` | Uncompressed NumPy array with its own numeric dtype; `allow_pickle=False` |
| `.csv`, `.txt` | UTF-8, optional BOM, numeric values separated by commas or whitespace |

Text and NumPy data must be one-dimensional, a single row, or a single column. Multiple columns, ragged rows, and missing values are refused. Integral decimal or scientific notation is accepted, for example `2.000` and `2e0`; `0.99999999999999999999` is rejected instead of being rounded to an integer. Integer text is parsed exactly, including values larger than 2^53. Integral real NumPy values and booleans are accepted; strings, objects, structured records, complex numbers, NaN, infinity, fractional values, negative values, and symbols outside the declared alphabet are rejected. The `dtype` argument affects raw binary input only.

NPY headers are checked before array loading: unsupported shapes and dtypes, shape/payload mismatches, appended arrays, and trailing data are refused. This prevents a tiny malformed header from requesting an enormous allocation. Object arrays never invoke pickle deserialization. Raw binary byte counts must be divisible by the selected symbol width. Input filenames are reduced to their basename, including Windows-style paths, before entering metadata.

## Reproducibility and resource bounds

Metadata records `source="file"`, basename `filename`, `format`, interpreted `dtype`, `n`, `byte_count`, `alphabet_size`, and the SHA-256 digest of the **original input bytes**. The digest consequently changes if the textual formatting changes, even when the observations are numerically equal. Absolute paths are not retained.

Both APIs default to `max_bytes=64*1024*1024`. The path API reads one explicitly supplied regular file with a bounded read; the bytes API also checks the true byte size of memoryviews. The limit bounds input size, not peak training memory: converting raw bytes to `int64`, constructing temporal windows, and evaluating large alphabets can require much more memory. Downstream model limits must be considered separately. The loader performs no network access, sidecar lookup, implicit extraction, or writes.

Real data should be evaluated with a declared acquisition protocol, temporal split, and appropriate dependence assumptions. An uploaded file does not establish IID sampling, stationarity, physical source health, or a conservative entropy lower bound.
