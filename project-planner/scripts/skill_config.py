#!/usr/bin/env python3
"""Read and update the project-planner skill's shared configuration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from localization import LocalizationError, normalize_language


DEFAULTS: dict[str, Any] = {
    "language": None,
    "max_parallel": None,
    "max_review_revisions": 2,
}


class ConfigError(ValueError):
    """An invalid or unavailable skill configuration."""


class ConfigSaveError(ConfigError):
    """A configuration could not be saved atomically."""


def default_config_path() -> Path:
    """Return config.json beside the skill's entrypoint, independent of cwd."""
    return Path(__file__).resolve().parents[1] / "config.json"


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(config)
    language = config.get("language")
    if language is not None:
        try:
            normalized["language"] = normalize_language(language)
        except LocalizationError as exc:
            raise ConfigError(f"language 必须是有效的 BCP 47 语言标签或 null: {exc}") from exc

    max_parallel = normalized.get("max_parallel")
    if max_parallel is not None and (
        not isinstance(max_parallel, int) or isinstance(max_parallel, bool) or max_parallel <= 0
    ):
        raise ConfigError("max_parallel 必须为严格正整数或 null")

    max_review_revisions = normalized.get("max_review_revisions")
    if (
        not isinstance(max_review_revisions, int)
        or isinstance(max_review_revisions, bool)
        or max_review_revisions < 0
    ):
        raise ConfigError("max_review_revisions 必须为非负整数")
    return normalized


def read_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Load the configuration, returning defaults without creating a missing file."""
    config_path = Path(path) if path is not None else default_config_path()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raw = {}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"无法读取配置文件 {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"配置文件 {config_path} 顶层必须是 JSON 对象")

    config = {**DEFAULTS, **raw}
    try:
        config = _normalize_config(config)
    except ConfigError as exc:
        raise ConfigError(f"配置文件 {config_path} 字段无效: {exc}") from exc
    return config


def save_config(config: dict[str, Any], path: str | os.PathLike[str]) -> None:
    """Atomically replace a configuration file after validating its values."""
    config = _normalize_config(config)
    config_path = Path(path)
    temp_path: str | None = None
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            json.dump(config, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, config_path)
        temp_path = None
    except OSError as exc:
        raise ConfigSaveError(f"无法原子保存配置文件 {config_path}: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def update_config(
    updates: dict[str, Any],
    *,
    path: str | os.PathLike[str] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Merge explicitly supplied settings and save only after confirmation."""
    if not confirmed:
        raise ConfigError("保存配置需要明确确认（CLI 使用 --confirmed）")
    unknown = set(updates) - set(DEFAULTS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ConfigError(f"不支持的配置字段: {names}")

    config_path = Path(path) if path is not None else default_config_path()
    config = read_config(config_path)
    if not updates:
        return config

    config.update(updates)
    config = _normalize_config(config)
    save_config(config, config_path)
    return config


def _language_arg(value: str) -> str | None:
    if value == "null":
        return None
    try:
        return normalize_language(value)
    except LocalizationError as exc:
        raise argparse.ArgumentTypeError(f"必须是有效的 BCP 47 语言标签或 null: {exc}") from exc


def _positive_int_or_null(value: str) -> int | None:
    if value == "null":
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是正整数或 null") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须是正整数或 null")
    return parsed


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是非负整数") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("必须是非负整数")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="读取或更新 project-planner 技能配置")
    parser.add_argument(
        "--config",
        type=Path,
        help="配置文件路径（默认使用本技能目录下的 config.json）",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("read", help="读取并输出有效配置")

    set_parser = commands.add_parser("set", help="更新指定配置项")
    set_parser.add_argument("--language", type=_language_arg, default=argparse.SUPPRESS)
    set_parser.add_argument("--max-parallel", type=_positive_int_or_null, default=argparse.SUPPRESS)
    set_parser.add_argument("--max-review-revisions", type=_nonnegative_int, default=argparse.SUPPRESS)
    set_parser.add_argument(
        "--confirmed",
        action="store_true",
        help="确认将指定设置保存为本技能的跨项目默认值",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = args.config if args.config is not None else default_config_path()

    try:
        if args.command == "read":
            result = read_config(config_path)
        else:
            argument_names = {
                "language": "language",
                "max_parallel": "max_parallel",
                "max_review_revisions": "max_review_revisions",
            }
            updates = {
                config_key: getattr(args, argument_name)
                for argument_name, config_key in argument_names.items()
                if hasattr(args, argument_name)
            }
            result = update_config(updates, path=config_path, confirmed=args.confirmed)
    except ConfigError as exc:
        parser.exit(2, f"错误: {exc}\n")

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
