from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import httpx

from decidim_cli.client import DecidimClient
from decidim_cli.config import Profile
from decidim_cli.normalize import normalize_open_data_zip


def test_api_credentials_login_and_graphql(tmp_path, monkeypatch):
    monkeypatch.setenv("DECIDIM_CLI_HOME", str(tmp_path))
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/sign_in":
            assert request.method == "POST"
            assert b"api_user%5Bkey%5D=key" in request.content
            return httpx.Response(200, headers={"Authorization": "Bearer abc123"})
        if request.url.path == "/api":
            seen["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"data": {"decidim": {"version": "0.31.0"}}})
        raise AssertionError(request.url)

    client = DecidimClient(
        Profile(name="t", base_url="https://example.org", auth="api-credentials"),
        transport=httpx.MockTransport(handler),
    )
    assert client.login_api_credentials("key", "secret") == "abc123"
    assert client.version()["data"]["decidim"]["version"] == "0.31.0"
    assert seen["auth"] == "Bearer abc123"


def test_open_data_normalizer(tmp_path: Path):
    zip_path = tmp_path / "open-data.zip"
    out_path = tmp_path / "contributions.jsonl"
    with ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "proposals.csv",
            "id,title,body,author_name,created_at\n"
            '1,"More trees","<p>Plant trees downtown.</p>",Ada,2026-01-01\n',
        )
    result = normalize_open_data_zip(zip_path, out_path)
    assert result["count"] == 1
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["contribution_type"] == "proposal"
    assert rows[0]["body"] == "Plant trees downtown."



def test_admin_mutation_inputs_are_relay_shaped():
    from decidim_cli import mutations
    from decidim_cli.main import _with_input_fields

    assert "createParticipatoryProcess(input: $input)" in mutations.CREATE_PARTICIPATORY_PROCESS
    assert "component(id:" not in mutations.CREATE_COMPONENT
    assert _with_input_fields({"attributes": {"title": "X"}}, processId="7") == {
        "input": {"attributes": {"title": "X"}, "processId": "7"}
    }
