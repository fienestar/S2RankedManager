"""GitHub release utilities for latest asset lookup and download."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from config import LATEST_RELEASE_API


@dataclass
class ReleaseAsset:
    name: str
    download_url: str


@dataclass
class ReleaseInfo:
    tag_name: str
    html_url: str
    assets: list[ReleaseAsset]

    def asset_by_name(self, name: str) -> ReleaseAsset | None:
        for asset in self.assets:
            if asset.name == name:
                return asset
        return None


def fetch_latest_release_from_api(api_url: str, timeout: int = 20) -> ReleaseInfo:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SpelunkyRankedManager",
    }
    response = requests.get(api_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    assets_raw = payload.get("assets", [])
    assets: list[ReleaseAsset] = []
    for item in assets_raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        url = str(item.get("browser_download_url", ""))
        if name and url:
            assets.append(ReleaseAsset(name=name, download_url=url))
    return ReleaseInfo(
        tag_name=str(payload.get("tag_name", "")),
        html_url=str(payload.get("html_url", "")),
        assets=assets,
    )


def fetch_latest_release(timeout: int = 20) -> ReleaseInfo:
    return fetch_latest_release_from_api(LATEST_RELEASE_API, timeout=timeout)


def download_file(url: str, destination: Path, timeout: int = 60) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with destination.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
