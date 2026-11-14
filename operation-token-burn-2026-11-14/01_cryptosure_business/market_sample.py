#!/usr/bin/env python3
"""Recount a manual public-record sample; never extrapolates a TAM."""
import csv
import json
from collections import Counter
from pathlib import Path

BASE = "https://csrc.nist.gov/projects/cryptographic-module-validation-program/entropy-validations/"

# Transcribed from the two public NIST result pages on 2026-11-14.
# No private data, contact persons, email addresses or product documents.
EARLY = [
    (1,"NetApp","2022-08-29"),(2,"WISeKey","2022-10-11"),(3,"Cisco","2022-10-11"),
    (4,"Cisco","2022-10-21"),(5,"Western Digital","2022-10-21"),(6,"Broadcom","2022-10-21"),
    (7,"HPE","2022-12-02"),(8,"Red Hat","2022-12-02"),(9,"IBM","2022-12-16"),
    (10,"DocuSign","2022-12-16"),(11,"STMicroelectronics","2022-12-16"),
    (12,"Western Digital","2023-01-05"),(13,"Western Digital","2023-01-05"),
    (14,"Apple","2023-01-19"),(15,"Apple","2023-01-19"),(16,"F5","2023-01-25"),
    (17,"RigSec","2023-01-26"),(18,"Nuvoton","2023-01-27"),(19,"SUSE","2023-02-13"),
    (20,"SUSE","2023-02-13"),(21,"Information Security Corporation","2023-02-17"),
    (22,"SUSE","2023-03-08"),(23,"Ciena","2023-03-15"),(24,"KeyPair Consulting","2023-03-17"),
    (25,"Silvus","2023-03-20"),(26,"Nokia","2023-03-21"),(27,"AMD","2023-03-22"),
    (28,"SUSE","2023-03-22"),(29,"SUSE","2023-03-22"),(30,"SUSE","2023-03-30"),
    (31,"SUSE","2023-03-30"),
]
RECENT = [
    (338,"Samsung","2026-07-07"),(339,"IBM","2026-07-09"),(340,"Chainguard","2026-07-10"),
    (341,"Ciena","2026-07-15"),(342,"Ranix","2026-07-16"),(343,"KIOXIA","2026-07-17"),
    (344,"Dell BSAFE","2026-07-17"),(345,"Arista","2026-07-24"),(346,"Alibaba Cloud","2026-07-24"),
    (347,"Amazon Web Services","2026-08-06"),(348,"HPE Juniper","2026-08-06"),
    (349,"CAE","2026-08-17"),(350,"Samsung","2026-08-18"),(351,"Qualcomm","2026-08-19"),
    (352,"Google","2026-08-19"),(353,"Google","2026-08-21"),(354,"Ctrl IQ","2026-08-26"),
    (355,"IBM","2026-08-28"),(356,"Infoblox","2026-09-02"),(357,"HP Inc.","2026-09-08"),
    (358,"Qualcomm","2026-09-09"),(359,"SAP","2026-09-09"),(360,"DINAMO","2026-09-09"),
    (361,"Arista","2026-09-16"),(362,"SAP","2026-09-24"),(363,"Toshiba","2026-10-02"),
    (364,"Beijing JN TASS","2026-10-08"),(365,"Intel","2026-10-09"),(366,"Red Hat","2026-10-09"),
    (367,"Ciena","2026-10-15"),(368,"Samsung","2026-10-28"),
]


def summarize(rows):
    counts = Counter(row[1] for row in rows)
    return {"records": len(rows), "normalized_vendor_labels": len(counts),
            "records_per_label": dict(sorted(counts.items())),
            "labels_with_multiple_records": sum(n > 1 for n in counts.values()),
            "date_min": min(row[2] for row in rows), "date_max": max(row[2] for row in rows)}


def main():
    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    rows = []
    for window, data, page in (("early", EARLY, 1), ("recent", RECENT, 2)):
        for number, vendor, date in data:
            rows.append({"sample_window": window, "certificate_id": f"E{number}",
                         "vendor_label_normalized": vendor, "validation_date": date,
                         "source_url": f"{BASE}search?ipp=250&page={page}",
                         "certificate_url": f"{BASE}certificate/{number}",
                         "consulted_date": "2026-11-14"})
    with (out / "esv_manual_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {"method": "two selected contiguous ID windows, not random or exhaustive; manual transcription",
              "displayed_total_records": 363, "early": summarize(EARLY), "recent": summarize(RECENT),
              "combined": summarize(EARLY + RECENT),
              "limitation": "Normalized vendor labels are neither corporate groups nor independent purchasing centers; no TAM extrapolation."}
    (out / "market_sample_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: {"records": value["records"], "labels": value["normalized_vendor_labels"]}
                      for key, value in result.items() if key in ("early", "recent", "combined")}, indent=2))


if __name__ == "__main__":
    main()
