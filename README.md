# spimov-mcp

MCP server for Spimov — dub videos via Claude Desktop / Claude Code / any MCP client.

Two transports:
- **stdio** — runs locally, spawned by your MCP client, authenticated with `SPIMOV_API_KEY` env var. Supports local file upload (`create_dub`).
- **HTTP** — long-lived server (we host at `mcp.spimov.com`), authenticated per-request with `Authorization: Bearer spk_live_...` (or `?api_key=`). Exposes both Streamable HTTP (`/mcp`, current spec) and legacy SSE (`/sse`). URL-only — no local file upload.

Both transports are thin wrappers over the public REST API at `https://spimov.com/api/v1`. The same API key, the same daily request quota.

---

## 1. Get an API key

Sign in at https://spimov.com → **Settings → API keys → Create new key**. Copy the `spk_live_...` token shown once.

## 2a. Use via stdio (Claude Desktop)

Install:

```bash
pip install spimov-mcp
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "spimov": {
      "command": "spimov-mcp",
      "env": {
        "SPIMOV_API_KEY": "spk_live_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Restart Claude Desktop. The "spimov" MCP server should appear; ask Claude to "dub /Users/me/Movies/clip.mp4 into Turkish using Spimov".

## 2b. Use via HTTP (Claude Code / Claude web / other clients)

Self-hosted: `MCP_PORT=8001 spimov-mcp-http`. Hosted endpoints:
- Streamable HTTP (recommended): `https://mcp.spimov.com/mcp`
- Legacy SSE: `https://mcp.spimov.com/sse`

**Claude Code / config-file clients** (header auth):

```json
{
  "mcpServers": {
    "spimov": {
      "url": "https://mcp.spimov.com/mcp",
      "headers": {
        "Authorization": "Bearer spk_live_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

**Claude web** (claude.ai → Settings → Connectors → *Add custom connector*): the
UI only takes a URL, so put the key in the query string:

```
https://mcp.spimov.com/mcp?api_key=spk_live_xxxxxxxxxxxxxxxxxxxxxxxx
```

> The key travels in the URL (stored in your connector config). Treat it like a
> password and rotate it from **Settings → API keys** if it leaks. Local file
> tools (`create_dub`, `download_video`) are unavailable here — use `dub_youtube`
> to dub, and `get_download_url` to get a clickable browser download link for the
> finished MP4.

## 3. Tools

| Tool | Purpose |
|---|---|
| `create_dub` | Upload a local file and queue a dubbing job (stdio only). |
| `dub_youtube` | Dub a YouTube URL server-side; optional auto-upload to a channel. |
| `get_job_status` | Poll a job (queued / processing / review / completed / failed). |
| `list_jobs` | Recent jobs for the account. |
| `list_segments` | Transcript segments (text, speaker, emotion, timing) of a job. |
| `update_segment` | Edit one segment's text/emotion/speaker/skip and resynth. |
| `remix_video` | Re-render audio mix / subtitles / lipsync without re-dubbing. |
| `download_video` | Save the finished MP4 locally (**stdio only**). |
| `get_download_url` | Get a shareable, time-limited browser download link for the MP4 (use this over HTTP/web). |
| `get_subtitles` | Fetch SRT/VTT (any embedded language). |
| `upload_to_youtube` | Publish (or retry) a finished job to a connected channel. |
| `cancel_job` | Cancel/delete. |
| `list_languages` | Source + target language list (17 target languages). |
| `get_quota` | Current minute & request usage vs. plan limits. |

Dubbing tools (`create_dub`, `dub_youtube`) accept an optional(quality voice, **default**), `chatterbox` (emotion voice), or `elevenlabs` (paid).

## 4. Override the API base (dev)

```bash
SPIMOV_API_BASE=http://localhost:8000/api/v1 spimov-mcp
```
