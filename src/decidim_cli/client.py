"""HTTP/GraphQL client for Decidim instances.

This module talks to unmodified Decidim instances over their official HTTP
surfaces. It contains no Decidim application code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .config import (
    Profile,
    clear_cached_credential,
    load_cached_credential,
    save_cached_credential,
)
from .mutations import INTROSPECTION_QUERY, SESSION_QUERY, VERSION_QUERY


class DecidimError(RuntimeError):
    def __init__(
        self,
        message: str,
        response: httpx.Response | None = None,
        graphql_errors: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.response = response
        self.graphql_errors = graphql_errors or []


class DecidimClient:
    def __init__(
        self,
        profile: Profile,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.profile = profile
        verify = profile.extra.get("verify", True)
        proxy = profile.extra.get("proxy") or None
        self._http = httpx.Client(
            base_url=profile.base_url.rstrip("/"),
            timeout=timeout,
            follow_redirects=True,
            verify=verify,
            proxy=proxy,
            transport=transport,
        )
        self._bearer: str | None = None
        self._restore_cached_auth()

    @property
    def api_path(self) -> str:
        return "/" + self.profile.api_path.strip("/")

    def _restore_cached_auth(self) -> None:
        cred = load_cached_credential(self.profile.name)
        if token := cred.get("bearer"):
            self._bearer = token

    def _persist_auth(self) -> None:
        save_cached_credential(self.profile.name, {"bearer": self._bearer or ""})

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._bearer:
            headers["Authorization"] = f"Bearer {self._bearer}"
        if self.profile.jwt_aud:
            headers["X-Jwt-Aud"] = self.profile.jwt_aud
        return headers

    @staticmethod
    def _raise_for_status(response: httpx.Response, context: str) -> None:
        if response.status_code >= 400:
            raise DecidimError(
                f"{context}: HTTP {response.status_code} - {response.text[:500]}",
                response=response,
            )

    def login_bearer(self, token: str) -> None:
        self._bearer = token.removeprefix("Bearer ").strip()
        self._persist_auth()

    def login_api_credentials(self, api_key: str, api_secret: str) -> str:
        response = self._http.post(
            f"{self.api_path}/sign_in",
            data={"api_user[key]": api_key, "api_user[secret]": api_secret},
            headers={"Accept": "application/json"},
        )
        self._raise_for_status(response, "api credentials sign-in failed")
        auth = response.headers.get("Authorization") or response.headers.get("authorization")
        if not auth:
            raise DecidimError("api credentials sign-in did not return an Authorization header")
        self.login_bearer(auth)
        return self._bearer or ""

    def logout(self) -> None:
        if self._bearer:
            response = self._http.delete(f"{self.api_path}/sign_out", headers=self._headers())
            self._raise_for_status(response, "api sign-out failed")
        clear_cached_credential(self.profile.name)
        self._bearer = None

    def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        operation_name: str | None = None,
        allow_errors: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name
        try:
            response = self._http.post(self.api_path, json=payload, headers=self._headers())
        except httpx.HTTPError as exc:
            raise DecidimError(f"GraphQL request failed: {exc}") from exc
        self._raise_for_status(response, "GraphQL request failed")
        try:
            data = response.json()
        except ValueError as exc:
            raise DecidimError(f"GraphQL response was not JSON: {response.text[:500]}") from exc
        errors = data.get("errors") or []
        if errors and not allow_errors:
            first = errors[0]
            raise DecidimError(
                f"GraphQL returned {len(errors)} error(s): {first.get('message', first)}",
                response=response,
                graphql_errors=errors,
            )
        return data

    def version(self) -> dict[str, Any]:
        return self.graphql(VERSION_QUERY)

    def session(self) -> dict[str, Any]:
        return self.graphql(SESSION_QUERY)

    def schema_summary(self) -> dict[str, Any]:
        return self.graphql(INTROSPECTION_QUERY)

    def download_open_data(self) -> tuple[bytes, str]:
        candidates: list[str] = []
        if self.profile.open_data_url:
            candidates.append(self.profile.open_data_url)
        candidates.extend(
            [
                "/open-data",
                "/open_data",
                "/open-data.zip",
                "/open_data.zip",
                "/open-data/download",
                "/open_data/download",
                "/open-data/download.zip",
                "/open_data/download.zip",
            ]
        )
        errors: list[str] = []
        for candidate in candidates:
            try:
                response = self._http.get(candidate)
                if response.status_code >= 400:
                    errors.append(f"{candidate}: HTTP {response.status_code}")
                    continue
                body = response.content
                ctype = response.headers.get("content-type", "")
                if body.startswith(b"PK") or "zip" in ctype:
                    return body, str(response.url)
                errors.append(f"{candidate}: not a zip/open-data response ({ctype or 'no type'})")
            except httpx.HTTPError as exc:
                errors.append(f"{candidate}: {exc}")
        raise DecidimError("Could not find a downloadable Open Data zip. Tried: " + "; ".join(errors))

    def save_open_data(self, path: Path) -> dict[str, Any]:
        body, url = self.download_open_data()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {"url": url, "path": str(path), "bytes": len(body)}


