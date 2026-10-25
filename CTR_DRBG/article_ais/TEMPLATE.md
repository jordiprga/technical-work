# Typesetting source

The manuscript uses the original `iacrtrans` class, version0.94 (class date2023-11-08), configured as `journal=tosc,preprint,floatrow,nohyperxmp`. The class supplies the ToSC page geometry, Latin Modern fonts, headings, running title and theorem styles. Tables use booktabs and width-aware tabularx columns; captions follow the journal class. Algorithms use algorithmicx and a native floatrow environment. No journal volume or publication metadata is supplied in preprint mode.

- Upstream: [Cryptosaurus/iacrtrans](https://github.com/Cryptosaurus/iacrtrans).
- Pinned revision: `e986305aa61ffa7aa28a65ddcec3c938c489d132`.
- Class source: [iacrtrans.cls](https://raw.githubusercontent.com/Cryptosaurus/iacrtrans/e986305aa61ffa7aa28a65ddcec3c938c489d132/iacrtrans.cls).
- Class documentation: [iacrdoc.tex](https://github.com/Cryptosaurus/iacrtrans/blob/e986305aa61ffa7aa28a65ddcec3c938c489d132/iacrdoc.tex).
- SHA256 of the unmodified class: `12dc0fb78d2e5a3c35d3b20218d699d5005fb9dfe584a424a683ffc416ea26d0`.
- License: upstream CC0 public-domain dedication, retained in the file header.
- Retrieved:2026-10-25.

The newer `iacrj` package is also intended for the IACR journals. This manuscript uses the established ToSC `iacrtrans` layout; it does not claim that this is the only available IACR class. Reproduction requires the accompanying class file and the packages requested by the source.

The temporary Jordi wrapper enables contextual review notes while preserving the clean article's result numbering. Font, margin and title overrides from the previous generic article template have been removed.
