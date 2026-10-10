#!/usr/bin/env python3
"""Validate, publish, and snapshot project-planner locale catalogs."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from string import Formatter
from typing import Any


GENERATOR = "project-planner/localization"
VERSION = 1
LOCALES_DIR = Path(__file__).resolve().parent / "locales"
MESSAGE_KEYS = frozenset(
    """unit none list_separator no_description no_deliverable plan_title title summary
workload_unit capacity capacity_unknown capacity_unknown_short workload_note scheduling_note assumptions
risks requirements requirement source coverage requirement_mapping schedule task type start finish workload
dependencies resources status task_details description deliverable acceptance pr_scope estimate_basis
resource_locks scheduled blocked blocked_reason chart_title chart_desc chart_caption axis_caption legend_task
legend_milestone legend_external legend_blocked blocked_label blocked_count schedule_span arrow_note
empty_requirements close completion_blocked completion kind_task kind_milestone kind_external""".split()
)
# Renderer-facing format fields are a frozen protocol contract. Historical
# snapshots validate against this map rather than mutable source catalogs.
TEMPLATE_PLACEHOLDERS: dict[str, tuple[tuple[str, str], ...]] = {
    "blocked_reason": (("items", ""),),
    "chart_desc": (("title", ""),),
    "chart_caption": (("unit", ""),),
    "blocked_label": (("items", ""),),
    "blocked_count": (("count", ""),),
    "schedule_span": (("finish", ""),),
    "completion_blocked": (("finish", ""),),
    "completion": (("finish", ""),),
}
_REPRESENTATIVE_FORMAT_VALUES = {
    "items": "an external task",
    "title": "Example project",
    "unit": "relative work units",
    "count": 2,
    "finish": "T+2",
}
BUILTIN_LANGUAGES = ("en", "zh-CN")
SOURCE_HASH_KEYS = frozenset(("en", "zh-CN", "context"))
REVIEW_PHASES = ("before", "read", "after")
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,8}$")
_ALNUM_RE = re.compile(r"^[A-Za-z0-9]+$")
_REGION_RE = re.compile(r"^(?:[A-Za-z]{2}|[0-9]{3})$")
_SCRIPT_RE = re.compile(r"^[A-Za-z]{4}$")
_EXTLANG_RE = re.compile(r"^[A-Za-z]{3}$")
_VARIANT_RE = re.compile(r"^(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3})$")
_EXTENSION_SINGLETON_RE = re.compile(r"^[0-9A-WY-Za-wy-z]$")
_PRIVATE_SINGLETON_RE = re.compile(r"^[Xx]$")
_SUBTAG_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FIELD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# RFC 5646's fixed set of 26 grandfathered tags. Values are IANA
# Preferred-Value entries, or the tag itself when no replacement exists.
# Verified against the registry dated 2026-09-17; no runtime network lookup.
_GRANDFATHERED_TAGS = {
    "art-lojban": "jbo",
    "cel-gaulish": "cel-gaulish",
    "en-gb-oed": "en-GB-oxendict",
    "i-ami": "ami",
    "i-bnn": "bnn",
    "i-default": "i-default",
    "i-enochian": "i-enochian",
    "i-hak": "hak",
    "i-klingon": "tlh",
    "i-lux": "lb",
    "i-mingo": "i-mingo",
    "i-navajo": "nv",
    "i-pwn": "pwn",
    "i-tao": "tao",
    "i-tay": "tay",
    "i-tsu": "tsu",
    "no-bok": "nb",
    "no-nyn": "nn",
    "sgn-be-fr": "sfb",
    "sgn-be-nl": "vgt",
    "sgn-ch-de": "sgg",
    "zh-guoyu": "cmn",
    "zh-hakka": "hak",
    "zh-min": "zh-min",
    "zh-min-nan": "nan",
    "zh-xiang": "hsn",
}


class LocalizationError(ValueError):
    """An input, evidence, or filesystem error suitable for a CLI message."""


def _canonicalize_bcp47(value: str) -> str:
    """Normalize BCP 47 syntax, casing, and the fixed grandfathered aliases."""
    if not value or value != value.strip() or not value.isascii():
        raise LocalizationError("language must be a non-empty ASCII BCP 47 tag")
    grandfathered = _GRANDFATHERED_TAGS.get(value.lower())
    if grandfathered is not None:
        return grandfathered

    parts = value.split("-")
    if any(not part for part in parts):
        raise LocalizationError(f"invalid BCP 47 language tag: {value!r}")

    # Private-use-only tags are valid BCP 47 tags and remain path-safe.
    if _PRIVATE_SINGLETON_RE.fullmatch(parts[0]):
        if len(parts) < 2 or any(not _SUBTAG_RE.fullmatch(part) for part in parts[1:]):
            raise LocalizationError(f"invalid BCP 47 private-use tag: {value!r}")
        return "-".join(["x", *(part.lower() for part in parts[1:])])

    language = parts[0]
    if not _LANGUAGE_RE.fullmatch(language):
        raise LocalizationError(f"invalid BCP 47 language subtag: {language!r}")
    canonical = [language.lower()]
    index = 1

    # Extlangs are syntactically available only after 2- or 3-letter language
    # subtags. Registry canonical aliases are deliberately not inferred here.
    if len(language) <= 3:
        extlangs = 0
        while (index < len(parts) and extlangs < 3
               and _EXTLANG_RE.fullmatch(parts[index])):
            canonical.append(parts[index].lower())
            index += 1
            extlangs += 1

    if index < len(parts) and _SCRIPT_RE.fullmatch(parts[index]):
        canonical.append(parts[index].title())
        index += 1

    if index < len(parts) and _REGION_RE.fullmatch(parts[index]):
        part = parts[index]
        canonical.append(part.upper() if part.isalpha() else part)
        index += 1

    variants: set[str] = set()
    while index < len(parts) and _VARIANT_RE.fullmatch(parts[index]):
        variant = parts[index].lower()
        if variant in variants:
            raise LocalizationError(f"duplicate BCP 47 variant subtag: {variant!r}")
        variants.add(variant)
        canonical.append(variant)
        index += 1

    extension_singletons: set[str] = set()
    while index < len(parts) and _EXTENSION_SINGLETON_RE.fullmatch(parts[index]):
        singleton = parts[index].lower()
        if singleton in extension_singletons:
            raise LocalizationError(f"duplicate BCP 47 extension singleton: {singleton!r}")
        extension_singletons.add(singleton)
        canonical.append(singleton)
        index += 1
        start = index
        while index < len(parts) and 2 <= len(parts[index]) <= 8 and _ALNUM_RE.fullmatch(parts[index]):
            canonical.append(parts[index].lower())
            index += 1
        if index == start:
            raise LocalizationError(f"BCP 47 extension {singleton!r} requires a value")

    if index < len(parts) and _PRIVATE_SINGLETON_RE.fullmatch(parts[index]):
        canonical.append("x")
        index += 1
        start = index
        while index < len(parts) and _SUBTAG_RE.fullmatch(parts[index]):
            canonical.append(parts[index].lower())
            index += 1
        if index == start:
            raise LocalizationError("BCP 47 private-use extension requires a value")

    if index != len(parts):
        raise LocalizationError(f"invalid BCP 47 language tag: {value!r}")
    return "-".join(canonical)


def normalize_language(language: str) -> str:
    """Return a path-safe normalized tag, not full IANA registry validation."""
    if not isinstance(language, str):
        raise LocalizationError("language must be a string; null is not a plan language")
    if language.casefold() == "null":
        raise LocalizationError("language 'null' is not a plan language")
    return _canonicalize_bcp47(language)


def _skill_root(skill_dir: str | os.PathLike[str] | None = None) -> Path:
    if skill_dir is None:
        return Path(__file__).resolve().parent.parent
    try:
        return Path(skill_dir).resolve()
    except (OSError, RuntimeError, TypeError) as exc:
        raise LocalizationError(f"invalid skill directory: {exc}") from exc


def _source_paths(skill_dir: str | os.PathLike[str] | None = None) -> dict[str, Path]:
    root = _skill_root(skill_dir)
    return {
        "en": root / "scripts" / "locales" / "en.json",
        "zh-CN": root / "scripts" / "locales" / "zh-CN.json",
        "context": root / "references" / "localization.md",
    }


def _json_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LocalizationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise LocalizationError(f"non-standard JSON value is not allowed: {value}")


def _load_json(path: str | os.PathLike[str], *, label: str) -> Any:
    try:
        raw = Path(path).read_bytes()
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_json_pairs_no_duplicates,
            parse_constant=_reject_json_constant,
        )
    except LocalizationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LocalizationError(f"cannot read {label}: {exc}") from exc


def _load_json_argument(value: dict[str, Any] | str | os.PathLike[str], *, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    loaded = _load_json(value, label=label)
    if not isinstance(loaded, dict):
        raise LocalizationError(f"{label} must contain a JSON object")
    return loaded


def _validate_message_shape(messages: Any, *, label: str) -> dict[str, str]:
    if not isinstance(messages, dict):
        raise LocalizationError(f"{label} must be a JSON object")
    if any(not isinstance(key, str) for key in messages):
        raise LocalizationError(f"{label} keys must be strings")
    keys = set(messages)
    if keys != MESSAGE_KEYS:
        missing = sorted(MESSAGE_KEYS - keys)
        extra = sorted(keys - MESSAGE_KEYS)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise LocalizationError(f"{label} has an incomplete key set ({'; '.join(details)})")
    for key, value in messages.items():
        if not isinstance(value, str) or not value.strip():
            raise LocalizationError(f"{label}[{key!r}] must be a non-empty string")
    return messages


def _template_fields(value: str, *, label: str, key: str) -> Counter[tuple[str, str]]:
    fields: Counter[tuple[str, str]] = Counter()
    try:
        parts = list(Formatter().parse(value))
    except ValueError as exc:
        raise LocalizationError(f"{label}[{key!r}] has invalid format braces: {exc}") from exc

    for _, field_name, format_spec, conversion in parts:
        if field_name is None:
            continue
        if not _FIELD_NAME_RE.fullmatch(field_name):
            raise LocalizationError(
                f"{label}[{key!r}] uses unsupported placeholder access: {field_name!r}"
            )
        if conversion is not None:
            raise LocalizationError(
                f"{label}[{key!r}] must not convert placeholder {field_name!r}"
            )
        if "{" in format_spec or "}" in format_spec:
            raise LocalizationError(
                f"{label}[{key!r}] must not nest placeholders in a format specifier"
            )
        fields[(field_name, format_spec)] += 1
    return fields


def _validate_template_contract(messages: dict[str, str], *, label: str) -> None:
    """Validate frozen fields and exercise every format string without current sources."""
    for key in sorted(MESSAGE_KEYS):
        actual = _template_fields(messages[key], label=label, key=key)
        expected = Counter(TEMPLATE_PLACEHOLDERS.get(key, ()))
        if actual != expected:
            raise LocalizationError(
                f"{label}[{key!r}] violates the frozen placeholder contract"
            )
        if actual:
            values = {
                field: _REPRESENTATIVE_FORMAT_VALUES[field]
                for field, _ in actual
            }
            try:
                messages[key].format(**values)
            except (AttributeError, IndexError, KeyError, ValueError) as exc:
                raise LocalizationError(
                    f"{label}[{key!r}] cannot be formatted with its representative values: {exc}"
                ) from exc


def validate_messages(target: Any, english: Any) -> dict[str, str]:
    """Validate full locale coverage and exact named-placeholder formats."""
    target_messages = _validate_message_shape(target, label="target messages")
    english_messages = _validate_message_shape(english, label="English messages")
    _validate_template_contract(target_messages, label="target messages")
    _validate_template_contract(english_messages, label="English messages")
    for key in sorted(MESSAGE_KEYS):
        expected = _template_fields(english_messages[key], label="English messages", key=key)
        actual = _template_fields(target_messages[key], label="target messages", key=key)
        if actual != expected:
            raise LocalizationError(
                f"target messages[{key!r}] must preserve English placeholder names and formats"
            )
    return target_messages


def read_sources(skill_dir: str | os.PathLike[str] | None = None) -> dict[str, dict[str, str]]:
    """Read and validate the complete built-in English and Chinese catalogs."""
    paths = _source_paths(skill_dir)
    catalogs: dict[str, dict[str, str]] = {}
    for language in BUILTIN_LANGUAGES:
        raw = _load_json(paths[language], label=f"{language} source catalog")
        catalogs[language] = _validate_message_shape(raw, label=f"{language} source catalog")
    validate_messages(catalogs["zh-CN"], catalogs["en"])
    # Check the English templates themselves for malformed formatting or access.
    validate_messages(catalogs["en"], catalogs["en"])
    return catalogs


def current_source_hashes(skill_dir: str | os.PathLike[str] | None = None) -> dict[str, str]:
    """Hash the raw built-in catalogs and localization instructions."""
    hashes: dict[str, str] = {}
    for name, path in _source_paths(skill_dir).items():
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise LocalizationError(f"required localization source is missing or unreadable: {path}: {exc}") from exc
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return hashes


def _canonical_json(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LocalizationError(f"value cannot be encoded as canonical JSON: {exc}") from exc
    return encoded.encode("utf-8")


def messages_hash(messages: dict[str, Any]) -> str:
    """Return SHA-256 of canonical UTF-8 JSON for the message object."""
    if not isinstance(messages, dict):
        raise LocalizationError("messages must be an object before hashing")
    return hashlib.sha256(_canonical_json(messages)).hexdigest()


def _validate_hash(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise LocalizationError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def _validate_source_hashes(value: Any, *, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != SOURCE_HASH_KEYS:
        raise LocalizationError(f"{label} must contain exactly en, zh-CN, and context hashes")
    return {
        key: _validate_hash(value[key], label=f"{label}.{key}")
        for key in ("en", "zh-CN", "context")
    }


def _normalize_expected_messages_hashes(value: str | dict[str, str], *, label: str) -> str | dict[str, str]:
    if isinstance(value, str):
        return _validate_hash(value, label=label)
    if isinstance(value, dict) and set(value) == set(BUILTIN_LANGUAGES):
        return {
            language: _validate_hash(value[language], label=f"{label}.{language}")
            for language in BUILTIN_LANGUAGES
        }
    raise LocalizationError(f"{label} must be a SHA-256 digest or an en/zh-CN digest object")


def _validate_review(
    review: Any,
    *,
    expected_source_hashes: dict[str, str],
    expected_messages_sha256: str | dict[str, str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(review, dict):
        raise LocalizationError(f"{label} must be an object")
    status = review.get("status")
    if status != "PASS":
        raise LocalizationError(f"{label} status must be PASS; got {status!r}")

    per_key = review.get("per_key")
    if not isinstance(per_key, dict) or set(per_key) != MESSAGE_KEYS:
        raise LocalizationError(f"{label}.per_key must cover every message key exactly")
    for key in sorted(MESSAGE_KEYS):
        evidence = per_key[key]
        if not isinstance(evidence, dict) or evidence.get("status") != "PASS":
            raise LocalizationError(f"{label}.per_key[{key!r}] must have status PASS")
        if not isinstance(evidence.get("evidence"), str) or not evidence["evidence"].strip():
            raise LocalizationError(f"{label}.per_key[{key!r}] needs concrete non-empty evidence")

    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict):
        raise LocalizationError(f"{label}.reviewer must identify the independent reviewer")
    if not isinstance(reviewer.get("identity"), str) or not reviewer["identity"].strip():
        raise LocalizationError(f"{label}.reviewer.identity must be non-empty")
    if reviewer.get("fork_turns") != "none":
        raise LocalizationError(f"{label}.reviewer.fork_turns must be 'none'")

    phases = review.get("hashes")
    if not isinstance(phases, dict) or set(phases) != set(REVIEW_PHASES):
        raise LocalizationError(f"{label}.hashes must contain before, read, and after")
    expected_hashes = _normalize_expected_messages_hashes(
        expected_messages_sha256,
        label=f"{label}.expected_messages_sha256",
    )
    normalized_phases: dict[str, dict[str, Any]] = {}
    for phase in REVIEW_PHASES:
        snapshot = phases[phase]
        if not isinstance(snapshot, dict) or set(snapshot) != {"source_hashes", "messages_sha256"}:
            raise LocalizationError(f"{label}.hashes.{phase} has an invalid shape")
        source_hashes = _validate_source_hashes(
            snapshot["source_hashes"],
            label=f"{label}.hashes.{phase}.source_hashes",
        )
        actual_messages_hashes = _normalize_expected_messages_hashes(
            snapshot["messages_sha256"],
            label=f"{label}.hashes.{phase}.messages_sha256",
        )
        if source_hashes != expected_source_hashes:
            raise LocalizationError(f"{label}.hashes.{phase} does not bind the expected sources")
        if actual_messages_hashes != expected_hashes:
            raise LocalizationError(f"{label}.hashes.{phase} does not bind the expected messages")
        normalized_phases[phase] = {
            "source_hashes": source_hashes,
            "messages_sha256": actual_messages_hashes,
        }
    if not (
        normalized_phases["before"] == normalized_phases["read"]
        == normalized_phases["after"]
    ):
        raise LocalizationError(f"{label} before/read/after hashes do not match")
    return review


def _load_baseline_review(
    skill_dir: str | os.PathLike[str] | None,
    catalogs: dict[str, dict[str, str]],
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    root = _skill_root(skill_dir)
    path = root / "scripts" / "locales" / "baseline-review.json"
    baseline = _load_json(path, label="built-in baseline review")
    if not isinstance(baseline, dict):
        raise LocalizationError("built-in baseline review must be a JSON object")
    expected_fields = {
        "generator",
        "version",
        "source_hashes",
        "messages_sha256",
        "semantic_review",
    }
    if set(baseline) != expected_fields:
        raise LocalizationError("built-in baseline review has an invalid field set")
    if (baseline.get("generator") != GENERATOR
            or isinstance(baseline.get("version"), bool)
            or type(baseline.get("version")) is not int
            or baseline.get("version") != VERSION):
        raise LocalizationError("built-in baseline review has an unsupported generator or version")
    baseline_sources = _validate_source_hashes(
        baseline.get("source_hashes"),
        label="built-in baseline review.source_hashes",
    )
    if baseline_sources != source_hashes:
        raise LocalizationError("built-in baseline review is stale for the current source files")
    messages_sha = baseline.get("messages_sha256")
    if not isinstance(messages_sha, dict) or set(messages_sha) != set(BUILTIN_LANGUAGES):
        raise LocalizationError("built-in baseline review must hash both source catalogs")
    actual_hashes = {language: messages_hash(catalogs[language]) for language in BUILTIN_LANGUAGES}
    normalized_hashes = {
        language: _validate_hash(messages_sha[language], label=f"baseline messages_sha256.{language}")
        for language in BUILTIN_LANGUAGES
    }
    if normalized_hashes != actual_hashes:
        raise LocalizationError("built-in baseline review does not bind the current catalogs")
    _validate_review(
        baseline.get("semantic_review"),
        expected_source_hashes=source_hashes,
        expected_messages_sha256=normalized_hashes,
        label="built-in baseline semantic_review",
    )
    return baseline


def _bundle_shape(bundle: Any) -> tuple[str, dict[str, str], dict[str, str], str, dict[str, Any]]:
    if not isinstance(bundle, dict):
        raise LocalizationError("locale bundle must be an object")
    required = {
        "generator",
        "version",
        "language",
        "messages",
        "source_hashes",
        "messages_sha256",
        "semantic_review",
    }
    if set(bundle) != required:
        raise LocalizationError("locale bundle must contain exactly the documented fields")
    if (bundle["generator"] != GENERATOR
            or isinstance(bundle["version"], bool)
            or type(bundle["version"]) is not int
            or bundle["version"] != VERSION):
        raise LocalizationError("locale bundle has an unsupported generator or version")
    language = normalize_language(bundle["language"])
    messages = _validate_message_shape(bundle["messages"], label="locale bundle.messages")
    _validate_template_contract(messages, label="locale bundle.messages")
    source_hashes = _validate_source_hashes(
        bundle["source_hashes"],
        label="locale bundle.source_hashes",
    )
    claimed_messages_hash = _validate_hash(
        bundle["messages_sha256"],
        label="locale bundle.messages_sha256",
    )
    actual_messages_hash = messages_hash(messages)
    if claimed_messages_hash != actual_messages_hash:
        raise LocalizationError("locale bundle messages_sha256 does not match messages")
    review = bundle["semantic_review"]
    review_messages_hash: str | dict[str, str]
    if language in BUILTIN_LANGUAGES:
        if not isinstance(review, dict):
            raise LocalizationError("built-in locale bundle has no baseline semantic review")
        phases = review.get("hashes")
        first = phases.get("before") if isinstance(phases, dict) else None
        review_messages_hash = first.get("messages_sha256") if isinstance(first, dict) else ""
        if not isinstance(review_messages_hash, dict) or review_messages_hash.get(language) != actual_messages_hash:
            raise LocalizationError("built-in locale bundle is not bound to its baseline review")
    else:
        review_messages_hash = actual_messages_hash
    _validate_review(
        review,
        expected_source_hashes=source_hashes,
        expected_messages_sha256=review_messages_hash,
        label="locale bundle.semantic_review",
    )
    return language, messages, source_hashes, actual_messages_hash, review


def validate_bundle(
    bundle: Any,
    language: str | None = None,
    check_current_sources: bool = False,
    skill_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate a saved bundle; current-source checking is opt-in for snapshots."""
    resolved_language, messages, saved_hashes, message_sha, review = _bundle_shape(bundle)
    if language is not None and normalize_language(language) != resolved_language:
        raise LocalizationError("locale bundle language does not match the requested language")

    if check_current_sources:
        current_hashes = current_source_hashes(skill_dir)
        if saved_hashes != current_hashes:
            raise LocalizationError("locale bundle is stale for the current source files")
        catalogs = read_sources(skill_dir)
        if resolved_language in BUILTIN_LANGUAGES:
            if messages != catalogs[resolved_language]:
                raise LocalizationError("built-in locale bundle messages differ from their source catalog")
        else:
            validate_messages(messages, catalogs["en"])
        baseline = _load_baseline_review(skill_dir, catalogs, current_hashes)
        if resolved_language in BUILTIN_LANGUAGES:
            if review != baseline["semantic_review"]:
                raise LocalizationError("built-in locale bundle does not contain the current baseline review")

    return {
        "generator": GENERATOR,
        "version": VERSION,
        "language": resolved_language,
        "messages": messages,
        "source_hashes": saved_hashes,
        "messages_sha256": message_sha,
        "semantic_review": review,
    }


def get_bundle(
    language: str,
    skill_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Return a fully reviewed bundle for the current source versions."""
    code = normalize_language(language)
    root = _skill_root(skill_dir)
    source_hashes = current_source_hashes(root)
    catalogs = read_sources(root)
    baseline = _load_baseline_review(root, catalogs, source_hashes)

    if code in BUILTIN_LANGUAGES:
        messages = catalogs[code]
        semantic_review = baseline["semantic_review"]
        bundle = {
            "generator": GENERATOR,
            "version": VERSION,
            "language": code,
            "messages": messages,
            "source_hashes": source_hashes,
            "messages_sha256": messages_hash(messages),
            "semantic_review": semantic_review,
        }
    else:
        path = root / "user-locales" / f"{code}.json"
        bundle = _load_json(path, label=f"{code} locale bundle")
    return validate_bundle(bundle, language=code, check_current_sources=True, skill_dir=root)


def make_bundle(
    messages: dict[str, Any] | str | os.PathLike[str],
    review: dict[str, Any] | str | os.PathLike[str],
    language: str,
    skill_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Build and validate a candidate bundle against current sources and review evidence."""
    code = normalize_language(language)
    if code in BUILTIN_LANGUAGES:
        raise LocalizationError("built-in catalogs cannot be published as user locales")
    catalogs = read_sources(skill_dir)
    source_hashes = current_source_hashes(skill_dir)
    baseline = _load_baseline_review(skill_dir, catalogs, source_hashes)
    candidate_messages = _load_json_argument(messages, label="candidate messages")
    candidate_messages = validate_messages(candidate_messages, catalogs["en"])
    message_sha = messages_hash(candidate_messages)
    review_data = _load_json_argument(review, label="semantic review")
    _validate_review(
        review_data,
        expected_source_hashes=source_hashes,
        expected_messages_sha256=message_sha,
        label="semantic review",
    )
    bundle = {
        "generator": GENERATOR,
        "version": VERSION,
        "language": code,
        "messages": candidate_messages,
        "source_hashes": source_hashes,
        "messages_sha256": message_sha,
        "semantic_review": review_data,
    }
    # The bilingual baseline is required before any shared or one-off locale use.
    if baseline["source_hashes"] != source_hashes:
        raise LocalizationError("built-in baseline review is stale")
    return validate_bundle(bundle, language=code, check_current_sources=True, skill_dir=skill_dir)


def _ensure_safe_user_locale_dir(skill_dir: str | os.PathLike[str] | None) -> tuple[Path, Path]:
    root = _skill_root(skill_dir)
    locale_dir = root / "user-locales"
    if locale_dir.is_symlink():
        raise LocalizationError("user-locales must not be a symbolic link")
    try:
        resolved_root = root.resolve()
        resolved_dir = locale_dir.resolve()
        resolved_dir.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise LocalizationError("user-locales must stay within the skill directory") from exc
    return root, locale_dir


def _check_existing_owner(
    path: Path, language: str, *, allow_language_change: bool = False,
) -> None:
    """Allow a verified replacement to repair a damaged file owned by this module."""
    if path.is_symlink():
        raise LocalizationError(f"refusing to replace a symbolic link: {path}")
    if not path.exists():
        return
    if path.is_symlink() or not path.is_file():
        raise LocalizationError(f"refusing to replace a non-regular locale target: {path}")
    existing = _load_json(path, label=f"existing locale bundle {path}")
    if not isinstance(existing, dict) or existing.get("generator") != GENERATOR:
        raise LocalizationError(f"refusing to replace a file not owned by {GENERATOR}: {path}")
    version = existing.get("version")
    if isinstance(version, bool) or type(version) is not int or version != VERSION:
        raise LocalizationError(f"refusing to replace a locale target with an unknown version: {path}")
    try:
        existing_language = normalize_language(existing.get("language"))
    except LocalizationError as exc:
        raise LocalizationError(f"refusing to replace a locale target with unknown language ownership: {path}") from exc
    stored_language = existing["language"]
    legacy_alias = _GRANDFATHERED_TAGS.get(stored_language.lower()) == existing_language
    if stored_language != existing_language and not legacy_alias:
        raise LocalizationError(f"refusing to replace a locale target with noncanonical language ownership: {path}")
    if existing_language != language and not allow_language_change:
        raise LocalizationError(f"refusing to replace a locale target owned by another language: {path}")
    if existing_language != language:
        # A language switch is permitted only for an explicitly selected,
        # valid plan snapshot. Same-language damaged-file repair remains valid.
        validate_bundle(existing, check_current_sources=False)


def _atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
    except LocalizationError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise LocalizationError(f"cannot atomically write {path}: {exc}") from exc


def publish(
    candidate_messages: dict[str, Any] | str | os.PathLike[str],
    review: dict[str, Any] | str | os.PathLike[str],
    language: str,
    skill_dir: str | os.PathLike[str] | None = None,
) -> Path:
    """Validate a candidate fully, then atomically publish it under user-locales."""
    code = normalize_language(language)
    root, locale_dir = _ensure_safe_user_locale_dir(skill_dir)
    bundle = make_bundle(candidate_messages, review, code, skill_dir=root)
    target = locale_dir / f"{code}.json"
    _check_existing_owner(target, code)
    _atomic_json_write(target, bundle)
    return target


def _snapshot_target(path: str | os.PathLike[str]) -> Path:
    try:
        supplied_path = Path(path).expanduser()
        if supplied_path.is_symlink():
            raise LocalizationError(f"snapshot output must not be a symbolic link: {supplied_path}")
        target = supplied_path.resolve()
    except (OSError, RuntimeError, TypeError) as exc:
        raise LocalizationError(f"invalid snapshot output path: {exc}") from exc
    if target.exists() and (target.is_symlink() or not target.is_file()):
        raise LocalizationError(f"snapshot output must be a regular file: {target}")
    return target


def snapshot(
    language: str,
    output_path: str | os.PathLike[str],
    messages: dict[str, Any] | str | os.PathLike[str] | None = None,
    review: dict[str, Any] | str | os.PathLike[str] | None = None,
    skill_dir: str | os.PathLike[str] | None = None,
    *,
    replace_language: bool = False,
) -> Path:
    """Atomically save a reviewed bundle for this run, or a verified candidate."""
    if (messages is None) != (review is None):
        raise LocalizationError("snapshot candidate messages and review must be supplied together")
    code = normalize_language(language)
    if messages is None:
        bundle = get_bundle(code, skill_dir=skill_dir)
    else:
        bundle = make_bundle(messages, review, code, skill_dir=skill_dir)
    target = _snapshot_target(output_path)
    protected_sources = {
        os.path.normcase(str(path.resolve()))
        for path in (*_source_paths(skill_dir).values(),
                     _skill_root(skill_dir) / "scripts" / "locales" / "baseline-review.json")
    }
    if os.path.normcase(str(target)) in protected_sources:
        raise LocalizationError("snapshot output cannot replace a localization source or baseline review")
    locale_dir = _skill_root(skill_dir) / "user-locales"
    if target.is_relative_to(locale_dir.resolve()):
        raise LocalizationError("snapshot output cannot replace a persistent user locale; use publish")
    if target.exists():
        _check_existing_owner(target, code, allow_language_change=replace_language)
    _atomic_json_write(target, bundle)
    return target


def _write_json_stdout(value: Any) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    sys.stdout.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and manage project-planner locale bundles.")
    commands = parser.add_subparsers(dest="command", required=True)

    sources_parser = commands.add_parser("sources", help="print source catalogs and their fingerprints")
    sources_parser.add_argument("--skill-dir", type=Path)

    validate_parser = commands.add_parser("validate", help="validate a complete candidate message catalog")
    validate_parser.add_argument("--language", required=True)
    validate_parser.add_argument("--messages", required=True, type=Path)
    validate_parser.add_argument("--skill-dir", type=Path)

    publish_parser = commands.add_parser("publish", help="publish a fully reviewed user locale")
    publish_parser.add_argument("--language", required=True)
    publish_parser.add_argument("--messages", required=True, type=Path)
    publish_parser.add_argument("--review", required=True, type=Path)
    publish_parser.add_argument("--skill-dir", type=Path)

    snapshot_parser = commands.add_parser("snapshot", help="save a reviewed locale bundle for one plan")
    snapshot_parser.add_argument("--language", required=True)
    snapshot_parser.add_argument("--output", required=True, type=Path)
    snapshot_parser.add_argument("--messages", type=Path)
    snapshot_parser.add_argument("--review", type=Path)
    snapshot_parser.add_argument("--skill-dir", type=Path)
    snapshot_parser.add_argument(
        "--replace-language", action="store_true",
        help="allow an explicitly requested language switch of an existing valid plan snapshot",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "sources":
            catalogs = read_sources(args.skill_dir)
            source_hashes = current_source_hashes(args.skill_dir)
            _write_json_stdout(
                {
                    "messages": catalogs,
                    "messages_sha256": {
                        language: messages_hash(catalogs[language])
                        for language in BUILTIN_LANGUAGES
                    },
                    "source_hashes": source_hashes,
                }
            )
        elif args.command == "validate":
            language = normalize_language(args.language)
            catalogs = read_sources(args.skill_dir)
            candidate = _load_json_argument(args.messages, label="candidate messages")
            validate_messages(candidate, catalogs["en"])
            _write_json_stdout(
                {
                    "language": language,
                    "messages_sha256": messages_hash(candidate),
                    "valid": True,
                }
            )
        elif args.command == "publish":
            path = publish(args.messages, args.review, args.language, skill_dir=args.skill_dir)
            _write_json_stdout({"published": str(path)})
        elif args.command == "snapshot":
            if (args.messages is None) != (args.review is None):
                raise LocalizationError("--messages and --review must be supplied together")
            path = snapshot(
                args.language,
                args.output,
                messages=args.messages,
                review=args.review,
                skill_dir=args.skill_dir,
                replace_language=args.replace_language,
            )
            _write_json_stdout({"snapshot": str(path)})
        else:
            raise LocalizationError(f"unsupported command: {args.command}")
        return 0
    except LocalizationError as exc:
        sys.stderr.write(f"localization: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
