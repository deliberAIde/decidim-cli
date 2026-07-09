"""decidim-cli - drive Decidim instances from the command line or an agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from .client import DecidimClient, DecidimError
from .config import Profile, list_profiles, load_profile, save_profile
from . import mutations
from .normalize import normalize_open_data_zip

app = typer.Typer(help=__doc__, no_args_is_help=True)
profile_app = typer.Typer(help="Manage instance profiles.", no_args_is_help=True)
open_data_app = typer.Typer(help="Download and normalize Decidim Open Data.", no_args_is_help=True)
proposal_app = typer.Typer(help="Proposal component mutations.", no_args_is_help=True)
meeting_app = typer.Typer(help="Meeting component mutations.", no_args_is_help=True)
debate_app = typer.Typer(help="Debate component mutations.", no_args_is_help=True)
process_app = typer.Typer(help="Future/admin participatory process provisioning mutations.", no_args_is_help=True)

app.add_typer(profile_app, name="profile")
app.add_typer(open_data_app, name="open-data")
app.add_typer(proposal_app, name="proposal")
app.add_typer(meeting_app, name="meeting")
app.add_typer(debate_app, name="debate")
app.add_typer(process_app, name="process")

console = Console()
err_console = Console(stderr=True)
_JSON = False


def _client(profile_name: str) -> DecidimClient:
    try:
        return DecidimClient(load_profile(profile_name))
    except KeyError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc


def _emit(data: Any, human_render=None) -> None:
    if _JSON:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    elif human_render:
        human_render(data)
    else:
        console.print(data)


def _read_json_arg(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    path = Path(value)
    text = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise typer.BadParameter("JSON value must be an object")
    return parsed


def _load_query(query_or_file: str | None, query_file: Path | None) -> str:
    if query_file:
        return query_file.read_text(encoding="utf-8")
    if not query_or_file:
        raise typer.BadParameter("provide a query string or --file")
    if query_or_file.startswith("@"):
        return Path(query_or_file[1:]).read_text(encoding="utf-8")
    path = Path(query_or_file)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return query_or_file


def _ids(values: Optional[list[str]]) -> list[int] | None:
    if not values:
        return None
    return [int(value) for value in values]


def _attributes(base: dict[str, Any], extra_json: str | None = None) -> dict[str, Any]:
    attrs = {key: value for key, value in base.items() if value is not None}
    attrs.update(_read_json_arg(extra_json))
    return attrs


def _input(locale: str | None, attributes: dict[str, Any], input_json: str | None = None) -> dict[str, Any]:
    if input_json:
        return _read_json_arg(input_json)
    payload: dict[str, Any] = {"attributes": attributes}
    if locale:
        payload["locale"] = locale
    return payload


def _run_mutation(profile: str, query: str, variables: dict[str, Any]) -> None:
    try:
        _emit(_client(profile).graphql(query, variables))
    except DecidimError as exc:
        err_console.print(f"[red]{exc}[/red]")
        if exc.graphql_errors and not _JSON:
            err_console.print_json(json.dumps(exc.graphql_errors, ensure_ascii=False))
        raise typer.Exit(1) from exc


@app.callback()
def _global(json_output: bool = typer.Option(False, "--json", help="Machine-readable output.")):
    global _JSON
    _JSON = json_output


@profile_app.command("add")
def profile_add(
    name: str,
    base_url: str,
    auth: str = typer.Option("none", help="none | api-credentials | bearer | oauth"),
    api_key: Optional[str] = typer.Option(None, envvar="DECIDIM_API_KEY"),
    api_path: str = typer.Option("/api", help="GraphQL/API path."),
    jwt_aud: Optional[str] = typer.Option(None, help="OAuth client id for X-Jwt-Aud."),
    open_data_url: Optional[str] = typer.Option(None, help="Known Open Data zip URL/path."),
    no_verify_tls: bool = typer.Option(False, help="Disable TLS verification."),
    proxy: Optional[str] = typer.Option(None, help="HTTP/SOCKS proxy URL."),
):
    """Register a Decidim instance profile."""
    extra: dict[str, Any] = {}
    if no_verify_tls:
        extra["verify"] = False
    if proxy:
        extra["proxy"] = proxy
    save_profile(
        Profile(
            name=name,
            base_url=base_url,
            auth=auth,
            api_key=api_key,
            api_path=api_path,
            jwt_aud=jwt_aud,
            open_data_url=open_data_url,
            extra=extra,
        )
    )
    _emit({"profile": name, "base_url": base_url, "auth": auth, "status": "saved"})


@profile_app.command("list")
def profile_list():
    """List configured profiles."""
    profiles = list_profiles()

    def render(data):
        table = Table("profile", "base_url", "auth", "api_path")
        for name, entry in data.items():
            table.add_row(name, entry.get("base_url", ""), entry.get("auth", ""), entry.get("api_path", "/api"))
        console.print(table)

    _emit(profiles, render)


@profile_app.command("show")
def profile_show(name: str):
    """Show one profile with sensitive fields redacted."""
    profile = load_profile(name)
    data = {
        "name": profile.name,
        "base_url": profile.base_url,
        "auth": profile.auth,
        "api_path": profile.api_path,
        "api_key": (profile.api_key[:6] + "..." if profile.api_key else None),
        "jwt_aud": profile.jwt_aud,
        "open_data_url": profile.open_data_url,
        "extra": profile.extra,
    }
    _emit(data)


@app.command()
def login(
    profile: str = typer.Option("default", "--profile", "-p"),
    api_key: Optional[str] = typer.Option(None, envvar="DECIDIM_API_KEY"),
    api_secret: Optional[str] = typer.Option(None, envvar="DECIDIM_API_SECRET"),
    bearer: Optional[str] = typer.Option(None, envvar="DECIDIM_BEARER"),
):
    """Authenticate and cache a bearer token."""
    client = _client(profile)
    if bearer:
        client.login_bearer(bearer)
        _emit({"profile": profile, "auth": "bearer", "status": "token cached"})
        return
    key = api_key or client.profile.api_key or typer.prompt("api key")
    secret = api_secret or typer.prompt("api secret", hide_input=True)
    try:
        token = client.login_api_credentials(key, secret)
        _emit({"profile": profile, "auth": "api-credentials", "status": "token cached", "token_prefix": token[:12]})
    except DecidimError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def logout(profile: str = typer.Option("default", "--profile", "-p")):
    """Revoke cached API token."""
    try:
        _client(profile).logout()
        _emit({"profile": profile, "status": "signed out"})
    except DecidimError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def version(profile: str = typer.Option("default", "--profile", "-p")):
    """Fetch Decidim version."""
    _emit(_client(profile).version())


@app.command()
def session(profile: str = typer.Option("default", "--profile", "-p")):
    """Show current API session/user if authenticated."""
    _emit(_client(profile).session())


@app.command()
def gql(
    query: Optional[str] = typer.Argument(None, help="GraphQL query string, @file, or file path."),
    query_file: Optional[Path] = typer.Option(None, "--file", "-f"),
    variables: Optional[str] = typer.Option(None, "--vars", help="JSON object or path."),
    variables_file: Optional[Path] = typer.Option(None, "--vars-file"),
    operation: Optional[str] = typer.Option(None, "--operation"),
    allow_errors: bool = typer.Option(False, help="Return GraphQL errors instead of exiting."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Run an arbitrary GraphQL query or mutation."""
    vars_obj = _read_json_arg(variables)
    if variables_file:
        vars_obj.update(json.loads(variables_file.read_text(encoding="utf-8")))
    try:
        _emit(
            _client(profile).graphql(
                _load_query(query, query_file),
                vars_obj or None,
                operation_name=operation,
                allow_errors=allow_errors,
            )
        )
    except DecidimError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@app.command()
def schema(
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Fetch a compact GraphQL schema summary via introspection."""
    result = _client(profile).schema_summary()
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _emit({"path": str(out), "status": "written"})
    else:
        _emit(result)


@open_data_app.command("download")
def open_data_download(
    out: Path = typer.Option(Path("open-data.zip"), "--out", "-o"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Download a generated Open Data zip from an instance."""
    try:
        _emit(_client(profile).save_open_data(out))
    except DecidimError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


@open_data_app.command("normalize")
def open_data_normalize(
    zip_path: Path,
    out: Path = typer.Option(Path("contributions.jsonl"), "--out", "-o"),
):
    """Normalize Open Data CSV/JSON files to contribution JSONL."""
    _emit(normalize_open_data_zip(zip_path, out))


@app.command("export")
def export_alias(
    out: Path = typer.Option(Path("open-data.zip"), "--out", "-o"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Alias for open-data download."""
    open_data_download(out=out, profile=profile)


@proposal_app.command("create")
def proposal_create(
    component_id: str,
    title: str,
    body: str,
    locale: str = typer.Option("en", "--locale"),
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    taxonomy: Optional[list[str]] = typer.Option(None, "--taxonomy"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json", help="JSON object merged into attributes."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    attrs = _attributes(
        {
            "title": title,
            "body": body,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "taxonomies": _ids(taxonomy),
        },
        extra_json,
    )
    _run_mutation(
        profile,
        mutations.CREATE_PROPOSAL,
        {"componentId": component_id, "input": _input(locale, attrs)},
    )


@proposal_app.command("update")
def proposal_update(
    component_id: str,
    proposal_id: str,
    title: str,
    body: str,
    locale: str = typer.Option("en", "--locale"),
    address: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    taxonomy: Optional[list[str]] = typer.Option(None, "--taxonomy"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    input_json: Optional[str] = typer.Option(None, "--input-json"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    attrs = _attributes(
        {
            "title": title,
            "body": body,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "taxonomies": _ids(taxonomy),
        },
        extra_json,
    )
    _run_mutation(
        profile,
        mutations.UPDATE_PROPOSAL,
        {"componentId": component_id, "proposalId": proposal_id, "input": _input(locale, attrs, input_json)},
    )


@proposal_app.command("withdraw")
def proposal_withdraw(
    component_id: str,
    proposal_id: str,
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(profile, mutations.WITHDRAW_PROPOSAL, {"componentId": component_id, "proposalId": proposal_id})


@proposal_app.command("vote")
def proposal_vote(
    component_id: str,
    proposal_id: str,
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(profile, mutations.VOTE_PROPOSAL, {"componentId": component_id, "proposalId": proposal_id})


@proposal_app.command("unvote")
def proposal_unvote(
    component_id: str,
    proposal_id: str,
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(profile, mutations.UNVOTE_PROPOSAL, {"componentId": component_id, "proposalId": proposal_id})


@proposal_app.command("answer")
def proposal_answer(
    component_id: str,
    proposal_id: str,
    state: str = typer.Option(..., help="accepted | rejected | evaluating"),
    answer: str = typer.Option(..., help="Answer text in the selected locale."),
    locale: str = typer.Option("en", "--locale"),
    cost: Optional[float] = None,
    input_json: Optional[str] = typer.Option(None, "--input-json", help="Raw AnswerInput JSON."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    raw = _read_json_arg(input_json) if input_json else None
    payload = raw or {"attributes": {"state": state, "answerContent": {locale: answer}}}
    if cost is not None and raw is None:
        payload["attributes"]["cost"] = cost
    _run_mutation(
        profile,
        mutations.ANSWER_PROPOSAL,
        {"componentId": component_id, "proposalId": proposal_id, "input": payload},
    )


@meeting_app.command("create")
def meeting_create(
    component_id: str,
    title: str,
    description: str,
    start_time: str,
    end_time: str,
    locale: str = typer.Option("en", "--locale"),
    type_of_meeting: str = typer.Option("ONLINE", "--type-of-meeting"),
    registration_type: str = typer.Option("ON_THIS_PLATFORM", "--registration-type"),
    address: Optional[str] = None,
    location: Optional[str] = None,
    location_hints: Optional[str] = typer.Option(None, "--location-hints"),
    online_meeting_url: Optional[str] = typer.Option(None, "--online-meeting-url"),
    registration_url: Optional[str] = typer.Option(None, "--registration-url"),
    registration_terms: Optional[str] = typer.Option(None, "--registration-terms"),
    registrations_enabled: Optional[bool] = typer.Option(None, "--registrations-enabled/--registrations-disabled"),
    available_slots: Optional[int] = typer.Option(None, "--available-slots"),
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    taxonomy: Optional[list[str]] = typer.Option(None, "--taxonomy"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    attrs = _attributes(
        {
            "title": title,
            "description": description,
            "startTime": start_time,
            "endTime": end_time,
            "typeOfMeeting": type_of_meeting,
            "registrationType": registration_type,
            "address": address,
            "location": location,
            "locationHints": location_hints,
            "onlineMeetingUrl": online_meeting_url,
            "registrationUrl": registration_url,
            "registrationTerms": registration_terms,
            "registrationsEnabled": registrations_enabled,
            "availableSlots": available_slots,
            "latitude": latitude,
            "longitude": longitude,
            "taxonomies": _ids(taxonomy),
        },
        extra_json,
    )
    _run_mutation(profile, mutations.CREATE_MEETING, {"componentId": component_id, "input": _input(locale, attrs)})


@meeting_app.command("update")
def meeting_update(
    component_id: str,
    meeting_id: str,
    input_json: str = typer.Option(..., "--input-json", help="Raw UpdateMeetingInput JSON object."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(
        profile,
        mutations.UPDATE_MEETING,
        {"componentId": component_id, "meetingId": meeting_id, "input": _read_json_arg(input_json)},
    )


@meeting_app.command("withdraw")
def meeting_withdraw(
    component_id: str,
    meeting_id: str,
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(profile, mutations.WITHDRAW_MEETING, {"componentId": component_id, "meetingId": meeting_id})


@meeting_app.command("close")
def meeting_close(
    component_id: str,
    meeting_id: str,
    input_json: str = typer.Option(..., "--input-json", help="Raw CloseMeetingInput JSON object."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(
        profile,
        mutations.CLOSE_MEETING,
        {"componentId": component_id, "meetingId": meeting_id, "input": _read_json_arg(input_json)},
    )


@debate_app.command("create")
def debate_create(
    component_id: str,
    title: str,
    description: str,
    locale: str = typer.Option("en", "--locale"),
    taxonomy: Optional[list[str]] = typer.Option(None, "--taxonomy"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    attrs = _attributes(
        {"title": title, "description": description, "taxonomies": _ids(taxonomy)},
        extra_json,
    )
    _run_mutation(profile, mutations.CREATE_DEBATE, {"componentId": component_id, "input": _input(locale, attrs)})


@debate_app.command("update")
def debate_update(
    component_id: str,
    debate_id: str,
    title: str,
    description: str,
    locale: str = typer.Option("en", "--locale"),
    taxonomy: Optional[list[str]] = typer.Option(None, "--taxonomy"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    input_json: Optional[str] = typer.Option(None, "--input-json"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    attrs = _attributes(
        {"title": title, "description": description, "taxonomies": _ids(taxonomy)},
        extra_json,
    )
    _run_mutation(
        profile,
        mutations.UPDATE_DEBATE,
        {"componentId": component_id, "debateId": debate_id, "input": _input(locale, attrs, input_json)},
    )


@debate_app.command("close")
def debate_close(
    component_id: str,
    debate_id: str,
    input_json: str = typer.Option(..., "--input-json", help="Raw CloseDebateInput JSON object."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    _run_mutation(
        profile,
        mutations.CLOSE_DEBATE,
        {"componentId": component_id, "debateId": debate_id, "input": _read_json_arg(input_json)},
    )

@process_app.command("create")
def process_create(
    slug: str,
    title: str,
    locale: str = typer.Option("en", "--locale"),
    subtitle: Optional[str] = None,
    short_description: Optional[str] = typer.Option(None, "--short-description"),
    description: Optional[str] = None,
    start_date: Optional[str] = typer.Option(None, "--start-date"),
    end_date: Optional[str] = typer.Option(None, "--end-date"),
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    input_json: Optional[str] = typer.Option(
        None,
        "--input-json",
        help="Raw CreateParticipatoryProcessInput JSON for a module/upstream implementation.",
    ),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Create a participatory process when the instance exposes admin API mutations."""
    attrs = _attributes(
        {
            "slug": slug,
            "title": title,
            "subtitle": subtitle,
            "shortDescription": short_description,
            "description": description,
            "startDate": start_date,
            "endDate": end_date,
        },
        extra_json,
    )
    _run_mutation(
        profile,
        mutations.CREATE_PARTICIPATORY_PROCESS,
        {"input": _input(locale, attrs, input_json)},
    )


@process_app.command("update")
def process_update(
    process_id: str,
    input_json: str = typer.Option(..., "--input-json", help="Raw UpdateParticipatoryProcessInput JSON."),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Update a participatory process when admin API mutations are installed."""
    _run_mutation(
        profile,
        mutations.UPDATE_PARTICIPATORY_PROCESS,
        {"processId": process_id, "input": _read_json_arg(input_json)},
    )


@process_app.command("publish")
def process_publish(
    process_id: str,
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Publish a participatory process when admin API mutations are installed."""
    _run_mutation(profile, mutations.PUBLISH_PARTICIPATORY_PROCESS, {"processId": process_id})


@process_app.command("phase-create")
def process_phase_create(
    process_id: str,
    title: str,
    start_date: str,
    end_date: str,
    locale: str = typer.Option("en", "--locale"),
    description: Optional[str] = None,
    extra_json: Optional[str] = typer.Option(None, "--extra-json"),
    input_json: Optional[str] = typer.Option(None, "--input-json"),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Create a phase/step when admin API mutations are installed."""
    attrs = _attributes(
        {
            "title": title,
            "description": description,
            "startDate": start_date,
            "endDate": end_date,
        },
        extra_json,
    )
    _run_mutation(
        profile,
        mutations.CREATE_PROCESS_PHASE,
        {"processId": process_id, "input": _input(locale, attrs, input_json)},
    )


@process_app.command("component-create")
def process_component_create(
    space_id: str,
    manifest_name: str,
    name: str,
    locale: str = typer.Option("en", "--locale"),
    settings_json: Optional[str] = typer.Option(None, "--settings-json"),
    step_settings_json: Optional[str] = typer.Option(None, "--step-settings-json"),
    input_json: Optional[str] = typer.Option(
        None,
        "--input-json",
        help="Raw CreateComponentInput JSON for a module/upstream implementation.",
    ),
    profile: str = typer.Option("default", "--profile", "-p"),
):
    """Create a component under a participatory space when admin API mutations are installed."""
    attrs = {
        "manifestName": manifest_name,
        "name": {locale: name},
        "settings": _read_json_arg(settings_json) if settings_json else None,
        "stepSettings": _read_json_arg(step_settings_json) if step_settings_json else None,
    }
    attrs = {key: value for key, value in attrs.items() if value is not None}
    payload = _read_json_arg(input_json) if input_json else {"attributes": attrs}
    _run_mutation(
        profile,
        mutations.CREATE_COMPONENT,
        {"spaceId": space_id, "input": payload},
    )

if __name__ == "__main__":
    app()



