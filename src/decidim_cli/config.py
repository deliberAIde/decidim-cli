"""Profile-based configuration for decidim-cli.

Profiles live in ~/.decidim-cli/config.toml:

    [profiles.city]
    base_url = "https://participate.example.gov"
    auth = "api-credentials"       # none | api-credentials | bearer | oauth
    api_key = "..."

Bearer tokens are cached in ~/.decidim-cli/credentials.toml.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w


def config_dir() -> Path:
    return Path(os.environ.get("DECIDIM_CLI_HOME", Path.home() / ".decidim-cli"))


def config_file() -> Path:
    return config_dir() / "config.toml"


def credentials_file() -> Path:
    return config_dir() / "credentials.toml"


@dataclass
class Profile:
    name: str
    base_url: str
    auth: str = "none"  # none | api-credentials | bearer | oauth
    api_key: str | None = None
    api_path: str = "/api"
    jwt_aud: str | None = None
    open_data_url: str | None = None
    api_version_tag: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _write_toml(path: Path, data: dict[str, Any]) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        tomli_w.dump(data, f)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_profile(name: str) -> Profile:
    data = _load_toml(config_file())
    profiles = data.get("profiles", {})
    if name not in profiles:
        raise KeyError(
            f"Profile '{name}' not found in {config_file()}. "
            f"Known profiles: {', '.join(profiles) or '(none)'}"
        )
    raw = dict(profiles[name])
    fields = Profile.__dataclass_fields__
    known = {key: raw.pop(key) for key in list(raw) if key in fields}
    return Profile(name=name, **known, extra=raw)


def list_profiles() -> dict[str, dict[str, Any]]:
    return _load_toml(config_file()).get("profiles", {})


def save_profile(profile: Profile) -> None:
    data = _load_toml(config_file())
    profiles = data.setdefault("profiles", {})
    entry: dict[str, Any] = {
        "base_url": profile.base_url,
        "auth": profile.auth,
        "api_path": profile.api_path,
    }
    for key in ("api_key", "jwt_aud", "open_data_url", "api_version_tag"):
        value = getattr(profile, key)
        if value is not None:
            entry[key] = value
    entry.update(profile.extra)
    profiles[profile.name] = entry
    _write_toml(config_file(), data)


def load_cached_credential(profile_name: str) -> dict[str, Any]:
    return _load_toml(credentials_file()).get(profile_name, {})


def save_cached_credential(profile_name: str, credential: dict[str, Any]) -> None:
    data = _load_toml(credentials_file())
    data[profile_name] = credential
    _write_toml(credentials_file(), data)


def clear_cached_credential(profile_name: str) -> None:
    data = _load_toml(credentials_file())
    if profile_name in data:
        del data[profile_name]
        _write_toml(credentials_file(), data)
