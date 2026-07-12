"""Spimov MCP server core — shared between stdio and HTTP transports.

The server is a thin wrapper over the public REST API: the user supplies an
API key (env SPIMOV_API_KEY for stdio, Authorization header for HTTP) and we
forward calls to https://spimov.com/api/v1/*.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

DEFAULT_API_BASE = os.environ.get("SPIMOV_API_BASE", "https://spimov.com/api/v1")


def _client(api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=DEFAULT_API_BASE,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=10.0),
    )


# Tools that only make sense over stdio: they read/write the client's local
# filesystem, so their path arguments are meaningless on a hosted transport.
# (Over HTTP, use get_download_url instead of download_video.)
LOCAL_ONLY_TOOLS = frozenset({"create_dub", "download_video"})


def mcp_tools_definitions(include_local: bool = True) -> list[Tool]:
    """The full list of MCP tools the Spimov server exposes.

    Module-level so the REST docs endpoint (/api/mcp/manifest.json) can dump
    the same definitions without spinning up an MCP server instance.

    `include_local=False` drops filesystem-bound tools (create_dub) — used by
    the hosted HTTP transport, where a local file_path can't be honored.
    """
    tools = [
            Tool(
                name="create_dub",
                description=(
                    "Upload a local video file and start a dubbing job. Returns the job_id "
                    "you can poll with get_job_status."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["file_path", "target_lang"],
                    "properties": {
                        "file_path": {"type": "string", "description": "Absolute path to a local video file (mp4/mov/mkv)."},
                        "source_lang": {"type": "string", "default": "auto"},
                        "target_lang": {"type": "string", "description": "ISO-639-1 code, e.g. 'tr', 'en', 'de'."},
                        "burn_subtitles": {"type": "boolean", "default": False},
                        "extra_subtitle_langs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Creator+ only. Extra languages to embed as soft subtitle tracks.",
                        },
                        "num_speakers": {"type": "integer", "minimum": 0, "default": 0},
                        "tts_provider": {
                            "type": "string",
                            "enum": ["xtts", "chatterbox", "elevenlabs"],
                            "default": "xtts",
                            "description": "TTS engine. xtts = quality voice (self-hosted, default, no per-character cost). chatterbox = emotion voice (self-hosted). elevenlabs = paid API.",
                        },
                    },
                },
            ),
            Tool(
                name="get_job_status",
                description="Check the status of a dubbing job (queued / processing / review / completed / failed).",
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {"job_id": {"type": "string"}},
                },
            ),
            Tool(
                name="list_jobs",
                description="List the most recent dubbing jobs for the current account.",
                inputSchema={
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 200}},
                },
            ),
            Tool(
                name="download_video",
                description=(
                    "Download the finished dubbed video and save it to disk. Returns the local path."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id", "save_to"],
                    "properties": {
                        "job_id": {"type": "string"},
                        "save_to": {"type": "string", "description": "Local file path to write the MP4 to."},
                    },
                },
            ),
            Tool(
                name="get_download_url",
                description=(
                    "Get a shareable, time-limited URL to download the finished dubbed MP4 "
                    "in a browser. Use this over HTTP/web (where download_video can't save to "
                    "your machine). The link works without an API key and expires."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {"job_id": {"type": "string"}},
                },
            ),
            Tool(
                name="get_subtitles",
                description="Fetch SRT or VTT subtitle text for a finished job.",
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {
                        "job_id": {"type": "string"},
                        "lang": {"type": "string", "default": "target", "description": "'original', 'target', or any embedded language code."},
                        "fmt": {"type": "string", "enum": ["srt", "vtt"], "default": "srt"},
                    },
                },
            ),
            Tool(
                name="cancel_job",
                description="Cancel a queued/processing job, or delete a finished one.",
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {"job_id": {"type": "string"}},
                },
            ),
            Tool(
                name="list_languages",
                description="List supported source and target languages.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_quota",
                description="Report current minutes/requests usage and plan limits.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="dub_youtube",
                description=(
                    "Start a dubbing job from a YouTube link (regular videos, Shorts, "
                    "and YouTube Music are all supported). Returns job_id immediately; "
                    "the download + pipeline run in the background, so poll with get_job_status. "
                    "Set `upload_to_channel_id` to auto-publish the dubbed result to a connected "
                    "YouTube channel as soon as the pipeline finishes."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["url", "target_lang"],
                    "properties": {
                        "url": {"type": "string", "description": "Full YouTube URL (watch / youtu.be / shorts)."},
                        "source_lang": {"type": "string", "default": "auto"},
                        "target_lang": {"type": "string", "description": "ISO-639-1 code."},
                        "burn_subtitles": {"type": "boolean", "default": False},
                        "lipsync": {"type": "boolean", "default": False, "description": "Pro+ only — re-syncs lips to the dub track."},
                        "num_speakers": {"type": "integer", "minimum": 0, "default": 0},
                        "extra_subtitle_langs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Creator+ only. Extra languages embedded as soft subtitle tracks.",
                        },
                        "upload_to_channel_id": {
                            "type": "string",
                            "description": "If set, auto-publish the dubbed video to this YouTube channel id (UCxxx...) after the pipeline completes. Must be a channel the user has connected via the Spimov web UI.",
                        },
                        "upload_visibility": {
                            "type": "string",
                            "enum": ["private", "unlisted", "public"],
                            "default": "private",
                            "description": "Upload visibility when upload_to_channel_id is set.",
                        },
                        "upload_title": {"type": "string", "description": "Override the YouTube video title (default: dubbed source title)."},
                        "upload_description": {"type": "string", "description": "Override the YouTube video description."},
                        "tts_provider": {
                            "type": "string",
                            "enum": ["xtts", "chatterbox", "elevenlabs"],
                            "default": "xtts",
                            "description": "TTS engine. xtts = quality voice (self-hosted, default, no per-character cost). chatterbox = emotion voice (self-hosted). elevenlabs = paid API.",
                        },
                    },
                },
            ),
            Tool(
                name="upload_to_youtube",
                description=(
                    "Manually trigger (or retry) the YouTube upload for an existing job. "
                    "The job must already have auto_upload_target_channel_id set — i.e. you "
                    "started it with upload_to_channel_id in dub_youtube or via the web UI."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {"job_id": {"type": "string"}},
                },
            ),
            Tool(
                name="list_segments",
                description=(
                    "List the transcript segments of a job (speaker, timing, text, emotion). "
                    "Use this to inspect a dub before editing with update_segment."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {"job_id": {"type": "string"}},
                },
            ),
            Tool(
                name="update_segment",
                description=(
                    "Edit a single transcript segment and queue resynthesis. "
                    "Apply any combination of text / emotion / speaker / skip in one call. "
                    "Resynth fires once; the dubbed audio is regenerated for that segment only."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id", "idx"],
                    "properties": {
                        "job_id": {"type": "string"},
                        "idx": {"type": "integer", "minimum": 0, "description": "Zero-based segment index."},
                        "text": {"type": "string", "description": "New translated text. Pass empty string to leave unchanged."},
                        "emotion": {"type": "string", "description": "neutral|happy|excited|angry|sad|scared|surprised|sarcastic|flirty|disgusted|calm|tense"},
                        "speaker": {"type": "string", "description": "Speaker id (e.g. SPEAKER_00). Existing wav is invalidated."},
                        "skip": {"type": "boolean", "description": "True = mute this segment in the mix; False = restore from original text."},
                    },
                },
            ),
            Tool(
                name="remix_video",
                description=(
                    "Re-render a finished/review-status job with new audio mix, subtitle styling, "
                    "or lipsync setting — without re-uploading the source. Returns the updated job."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {
                        "job_id": {"type": "string"},
                        "tts_gain_db": {"type": "number", "minimum": -24, "maximum": 12},
                        "bg_gain_db": {"type": "number", "minimum": -24, "maximum": 12},
                        "burn_subtitles": {"type": "boolean"},
                        "subtitle_font_size": {"type": "integer", "minimum": 10, "maximum": 48},
                        "subtitle_color": {"type": "string", "enum": ["white", "yellow", "cyan", "green", "pink"]},
                        "subtitle_bg": {"type": "string", "enum": ["box", "shadow", "none"]},
                        "subtitle_position": {"type": "string", "enum": ["bottom", "top"]},
                        "extra_subtitle_langs": {"type": "array", "items": {"type": "string"}},
                        "lipsync": {"type": "boolean"},
                    },
                },
            ),
            Tool(
                name="create_checkout_link",
                description=(
                    "Get a DodoPayments hosted-checkout URL so the user can upgrade their plan "
                    "(pro/max/max_plus). Returns a URL the user opens in a browser to pay — nothing is "
                    "charged here. Confirm the plan and price with the user before calling."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["plan"],
                    "properties": {
                        "plan": {"type": "string", "enum": ["pro", "max", "max_plus"]},
                        "billing": {"type": "string", "enum": ["monthly", "yearly"], "default": "monthly"},
                    },
                },
            ),
            Tool(
                name="translate_srt",
                description=(
                    "Translate SRT subtitle text into another language and return the translated SRT. "
                    "Pass the full .srt content as text. mode=basic (fast, line-by-line) or smart "
                    "(Gemini, whole-file context so terms stay consistent). Consumes credits."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["srt_content", "target_lang"],
                    "properties": {
                        "srt_content": {"type": "string", "description": "Full .srt file content"},
                        "target_lang": {"type": "string", "description": "Target language code, e.g. tr, es, ar"},
                        "source_lang": {"type": "string", "default": "auto"},
                        "mode": {"type": "string", "enum": ["basic", "smart"], "default": "basic"},
                    },
                },
            ),
            Tool(
                name="start_signup",
                description=(
                    "Sign a NEW user up to Spimov from here — no browser config or connector setup. "
                    "Give the user's email; returns a verify_url they open in a browser to create their "
                    "account (and optionally pay for a plan). No API key required. After they open it, "
                    "call check_signup with the returned device_code to receive an API key."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["email"],
                    "properties": {"email": {"type": "string", "description": "The user's email address"}},
                },
            ),
            Tool(
                name="check_signup",
                description=(
                    "Poll after start_signup. Given the device_code, returns {status}. When the user has "
                    "opened the verify_url, status becomes 'ready' and includes an api_key — store it and "
                    "use it for every other tool. 'pending' means keep waiting; 'expired' means restart."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["device_code"],
                    "properties": {"device_code": {"type": "string"}},
                },
            ),
        ]
    if not include_local:
        tools = [t for t in tools if t.name not in LOCAL_ONLY_TOOLS]
    return tools


def build_server(get_api_key, include_local: bool = True) -> Server:
    """Build the Server. `get_api_key()` returns the active key (env or header).

    `include_local=False` hides (and refuses) filesystem-bound tools — set this
    on the hosted HTTP transport.
    """
    server = Server("spimov-mcp")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return mcp_tools_definitions(include_local=include_local)

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if not include_local and name in LOCAL_ONLY_TOOLS:
            return [TextContent(type="text", text=json.dumps(
                {"error": "local_only_tool", "tool": name,
                 "hint": "This tool needs local filesystem access; use the stdio transport (pip install spimov-mcp)."}
            ))]
        # ── Public onboarding tools (no API key required) ──────────────
        if name in ("start_signup", "check_signup"):
            onb_base = DEFAULT_API_BASE.rsplit("/api/", 1)[0] + "/api/mcp-onboard"
            async with httpx.AsyncClient(base_url=onb_base, timeout=30.0) as oc:
                try:
                    if name == "start_signup":
                        r = await oc.post("/start", json={"email": arguments["email"]})
                    else:
                        r = await oc.post("/check", json={"device_code": arguments["device_code"]})
                    return _wrap(r)
                except httpx.HTTPError as exc:
                    return [TextContent(type="text", text=json.dumps({"error": "transport_error", "detail": str(exc)}))]

        api_key = get_api_key()
        if not api_key and name != "list_languages":
            return [TextContent(type="text", text=json.dumps(
                {"error": "missing_api_key", "hint": "Set SPIMOV_API_KEY env var (stdio) or send Authorization header (HTTP)."}
            ))]
        async with _client(api_key or "anonymous") as http:
            try:
                if name == "create_dub":
                    return await _create_dub(http, arguments)
                if name == "get_job_status":
                    r = await http.get(f"/videos/{arguments['job_id']}")
                    return _wrap(r)
                if name == "list_jobs":
                    r = await http.get("/videos", params={"limit": arguments.get("limit", 20)})
                    return _wrap(r)
                if name == "download_video":
                    return await _download_video(http, arguments)
                if name == "get_download_url":
                    r = await http.get(f"/videos/{arguments['job_id']}/download-url")
                    return _wrap(r)
                if name == "get_subtitles":
                    r = await http.get(
                        f"/videos/{arguments['job_id']}/subtitles",
                        params={"lang": arguments.get("lang", "target"), "fmt": arguments.get("fmt", "srt")},
                    )
                    if r.status_code == 200:
                        return [TextContent(type="text", text=r.text)]
                    return _wrap(r)
                if name == "cancel_job":
                    r = await http.delete(f"/videos/{arguments['job_id']}")
                    if r.status_code == 204:
                        return [TextContent(type="text", text=json.dumps({"ok": True}))]
                    return _wrap(r)
                if name == "list_languages":
                    r = await http.get("/languages")
                    return _wrap(r)
                if name == "get_quota":
                    r = await http.get("/quota")
                    return _wrap(r)
                if name == "dub_youtube":
                    payload = {k: v for k, v in {
                        "url": arguments["url"],
                        "source_lang": arguments.get("source_lang", "auto"),
                        "target_lang": arguments["target_lang"],
                        "burn_subtitles": bool(arguments.get("burn_subtitles", False)),
                        "lipsync": bool(arguments.get("lipsync", False)),
                        "num_speakers": arguments.get("num_speakers") or None,
                        "extra_subtitle_langs": arguments.get("extra_subtitle_langs") or None,
                        "tts_provider": arguments.get("tts_provider") or "xtts",
                        "auto_upload_target_channel_id": arguments.get("upload_to_channel_id") or None,
                        "auto_upload_visibility": arguments.get("upload_visibility") or None,
                        "auto_upload_title": arguments.get("upload_title") or None,
                        "auto_upload_description": arguments.get("upload_description") or None,
                    }.items() if v not in (None, [], "")}
                    r = await http.post("/videos/youtube", json=payload)
                    return _wrap(r)
                if name == "upload_to_youtube":
                    r = await http.post(f"/videos/{arguments['job_id']}/upload-to-youtube")
                    return _wrap(r)
                if name == "list_segments":
                    r = await http.get(f"/videos/{arguments['job_id']}/segments")
                    return _wrap(r)
                if name == "update_segment":
                    patch = {k: v for k, v in {
                        "text": arguments.get("text") or None,
                        "emotion": arguments.get("emotion") or None,
                        "speaker": arguments.get("speaker") or None,
                        "skip": arguments.get("skip"),
                    }.items() if v is not None}
                    r = await http.patch(
                        f"/videos/{arguments['job_id']}/segments/{int(arguments['idx'])}",
                        json=patch,
                    )
                    return _wrap(r)
                if name == "remix_video":
                    payload = {k: v for k, v in arguments.items() if k != "job_id" and v is not None}
                    r = await http.post(f"/videos/{arguments['job_id']}/remix", json=payload)
                    return _wrap(r)
                if name == "create_checkout_link":
                    r = await http.post("/checkout", json={
                        "plan": arguments["plan"],
                        "billing": arguments.get("billing", "monthly"),
                    })
                    return _wrap(r)
                if name == "translate_srt":
                    r = await http.post("/translate-srt", json={
                        "srt_content": arguments["srt_content"],
                        "target_lang": arguments["target_lang"],
                        "source_lang": arguments.get("source_lang", "auto"),
                        "mode": arguments.get("mode", "basic"),
                    })
                    return _wrap(r)
                return [TextContent(type="text", text=json.dumps({"error": f"unknown tool: {name}"}))]
            except httpx.HTTPError as exc:
                return [TextContent(type="text", text=json.dumps({"error": "transport_error", "detail": str(exc)}))]

    return server


def _wrap(r: httpx.Response) -> list[TextContent]:
    try:
        body = r.json()
    except ValueError:
        body = {"status_code": r.status_code, "text": r.text[:1000]}
    if r.status_code >= 400:
        return [TextContent(type="text", text=json.dumps({"error": True, "status": r.status_code, "body": body}))]
    return [TextContent(type="text", text=json.dumps(body, default=str))]


async def _create_dub(http: httpx.AsyncClient, args: dict) -> list[TextContent]:
    file_path = Path(args["file_path"]).expanduser()
    if not file_path.exists() or not file_path.is_file():
        return [TextContent(type="text", text=json.dumps({"error": "file_not_found", "path": str(file_path)}))]
    meta = {k: v for k, v in {
        "source_lang": args.get("source_lang", "auto"),
        "target_lang": args["target_lang"],
        "burn_subtitles": bool(args.get("burn_subtitles", False)),
        "num_speakers": args.get("num_speakers") or None,
        "extra_subtitle_langs": args.get("extra_subtitle_langs") or None,
        "tts_provider": args.get("tts_provider") or "xtts",
    }.items() if v not in (None, [], "")}
    with file_path.open("rb") as fh:
        r = await http.post(
            "/videos",
            files={"file": (file_path.name, fh, "video/mp4")},
            data={"meta": json.dumps(meta)},
        )
    return _wrap(r)


async def _download_video(http: httpx.AsyncClient, args: dict) -> list[TextContent]:
    job_id = args["job_id"]
    save_to = Path(args["save_to"]).expanduser()
    save_to.parent.mkdir(parents=True, exist_ok=True)
    async with http.stream("GET", f"/videos/{job_id}/download") as r:
        if r.status_code != 200:
            text = await r.aread()
            return _wrap(httpx.Response(r.status_code, content=text, request=r.request))
        with save_to.open("wb") as fh:
            async for chunk in r.aiter_bytes():
                fh.write(chunk)
    size = save_to.stat().st_size
    return [TextContent(type="text", text=json.dumps({"ok": True, "path": str(save_to), "bytes": size}))]
