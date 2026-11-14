"""Deterministic human and spreadsheet views derived from the result object."""

from __future__ import annotations

import csv
import io
import re
from typing import Any


def md(value: Any) -> str:
    text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;").replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", text)


def csv_safe(value: Any) -> str:
    text = str(value)
    # A CSV opened in a spreadsheet must not turn untrusted titles into formulas.
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def render_markdown(run: dict[str, Any]) -> bytes:
    lines = ["# CryptoSure — informe de evidencia", "",
             "**DEMOSTRADOR. No constituye certificación, validación ni decisión de conformidad.**", "",
             f"Perfil: {md(run['profile_id'])} / {md(run['profile_version'])}",
             f"Ejecución UTC: {md(run['created_at'])}",
             f"Resultado técnico: **{run['overall_status']}**", "",
             "PASS sólo indica que los checks implementados aprobaron sobre los bytes incluidos.",
             "REVIEW requiere evaluación humana. BLOCKED señala evidencia ausente, inválida o plugin desconocido.",
             "FAIL señala al menos una comprobación fallida. Ningún estado sustituye al laboratorio u organismo.", "",
             "La verificación de hashes demuestra consistencia con un root digest confiable, no autoría, verdad o adecuación.",
             "El root.sha256 dentro del mismo bundle no es por sí solo un ancla de confianza externa.", "",
             "## Matriz de requisitos", "",
             "| Requisito | Cláusula de referencia | Estado | Checks | Evidencias |",
             "|---|---|---|---|---|"]
    for row in run["requirements"]:
        checks = ", ".join(f"{check['id']}:{check['status']}" for check in row["checks"])
        artifacts = ", ".join(row["artifact_ids"])
        lines.append(f"| {md(row['id'])}: {md(row['title'])} | {md(row['clause'])} | {row['status']} | {md(checks)} | {md(artifacts)} |")
    lines += ["", "## Detalle de comprobaciones", ""]
    for row in run["requirements"]:
        for check in row["checks"]:
            lines += [f"- {md(check['id'])}: **{check['status']}**. {md(check['detail'])}"]
        for issue in row["issues"]:
            lines += [f"- {md(row['id'])}: {md(issue)}"]
    lines += ["", "## Límites del perfil", "", md(run["limitations"]), "",
              "## Proveniencia", "", f"- Tool version: {md(run['tool']['version'])}",
              f"- Tool source SHA-256: `{run['tool']['source_sha256']}`",
              f"- Profile SHA-256: `{run['profile_sha256']}`",
              f"- Git: {md(run['git'])}", ""]
    return "\n".join(lines).encode("utf-8")


def render_csv(run: dict[str, Any]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["requirement_id", "title", "clause", "status", "human_review",
                     "check_id", "check_type", "check_status", "artifact_id", "artifact_sha256"])
    for row in run["requirements"]:
        checks = row["checks"] or [{"id": "", "type": "", "status": "", "artifact": ""}]
        for check in checks:
            aid = check["artifact"]
            digest = run["artifacts"].get(aid, {}).get("sha256", "")
            writer.writerow([csv_safe(value) for value in [row["id"], row["title"], row["clause"],
                             row["status"], row["human_review"], check["id"], check["type"],
                             check["status"], aid, digest]])
        referenced = {check["artifact"] for check in row["checks"]}
        for aid in sorted(set(row["artifact_ids"]) - referenced):
            writer.writerow([csv_safe(value) for value in [row["id"], row["title"], row["clause"],
                             row["status"], row["human_review"], "", "", "", aid,
                             run["artifacts"].get(aid, {}).get("sha256", "")]])
    return stream.getvalue().encode("utf-8")
