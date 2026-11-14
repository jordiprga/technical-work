"""Versioned requirement profiles. Standards text is deliberately not embedded."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import CryptoSureError, exact_keys, parse_json, read_bounded, text_field

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


def identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise CryptoSureError(f"Invalid identifier at {where}")
    return value


def validate_profile(profile: Any) -> dict[str, Any]:
    exact_keys(profile, {"schema_version", "id", "version", "title", "standard", "limitations", "requirements"},
               {"schema_version", "id", "version", "title", "standard", "limitations", "requirements"}, "profile")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise CryptoSureError("Unsupported profile schema_version")
    identifier(profile["id"], "profile.id")
    text_field(profile["version"], "profile.version", 128)
    text_field(profile["title"], "profile.title")
    text_field(profile["limitations"], "profile.limitations")
    standard = profile["standard"]
    exact_keys(standard, {"family", "edition", "source_url"}, {"family", "edition", "source_url"}, "standard")
    for key, value in standard.items():
        text_field(value, f"standard.{key}")
    requirements = profile["requirements"]
    if not isinstance(requirements, list) or not 1 <= len(requirements) <= 1000:
        raise CryptoSureError("requirements must contain 1..1000 entries")
    requirement_ids: set[str] = set()
    check_ids: set[str] = set()
    for requirement in requirements:
        exact_keys(requirement, {"id", "title", "clause", "human_review", "artifacts", "checks"},
                   {"id", "title", "clause", "human_review", "artifacts", "checks"}, "requirement")
        rid = identifier(requirement["id"], "requirement.id")
        if rid in requirement_ids:
            raise CryptoSureError(f"Duplicate requirement id: {rid}")
        requirement_ids.add(rid)
        text_field(requirement["title"], f"{rid}.title")
        text_field(requirement["clause"], f"{rid}.clause")
        if type(requirement["human_review"]) is not bool:
            raise CryptoSureError(f"{rid}.human_review must be boolean")
        artifacts = requirement["artifacts"]
        if not isinstance(artifacts, list) or len(artifacts) > 100:
            raise CryptoSureError(f"{rid}.artifacts must be a list <= 100 entries")
        for aid in artifacts:
            identifier(aid, f"{rid}.artifacts")
        if len(set(artifacts)) != len(artifacts):
            raise CryptoSureError(f"Duplicate artifact reference in {rid}")
        checks = requirement["checks"]
        if not isinstance(checks, list) or len(checks) > 100:
            raise CryptoSureError(f"{rid}.checks must be a list <= 100 entries")
        if not artifacts and not checks:
            raise CryptoSureError(f"Empty requirement: {rid}")
        if not checks and not requirement["human_review"]:
            raise CryptoSureError(f"{rid}: no automatic checks requires human_review=true")
        for check in checks:
            exact_keys(check, {"id", "type", "artifact", "parameters"},
                       {"id", "type", "artifact", "parameters"}, f"{rid}.check")
            cid = identifier(check["id"], "check.id")
            if cid in check_ids:
                raise CryptoSureError(f"Duplicate global check id: {cid}")
            check_ids.add(cid)
            if len(check_ids) > 4096:
                raise CryptoSureError("Profile exceeds 4096 checks")
            identifier(check["type"], f"{cid}.type")
            identifier(check["artifact"], f"{cid}.artifact")
            if not isinstance(check["parameters"], dict):
                raise CryptoSureError(f"{cid}.parameters must be an object")
    return profile


def load_profile(path: Path) -> dict[str, Any]:
    return validate_profile(parse_json(read_bounded(path)))
