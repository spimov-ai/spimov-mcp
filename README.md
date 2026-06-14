# spimov-mcp

MCP server for Spimov — dub videos via Claude Desktop / Claude Code / any MCP client.

Two transports:
- **stdio** — runs locally, spawned by your MCP client, authenticated with `SPIMOV_API_KEY` env var.
- **HTTP/SSE** — long-lived server (we host at `mcp.spimov.com`), authenticated per-request with `Authorization: Bearer spk_live_...`.

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

## 2b. Use via HTTP/SSE (Claude Code / web clients)

Hosted endpoint: `https://mcp.spimov.com/sse`. Self-hosted: `MCP_PORT=8001 spimov-mcp-http`.

```json
{
  "mcpServers": {
    "spimov": {
      "url": "https://mcp.spimov.com/sse",
      "headers": {
        "Authorization": "Bearer spk_live_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

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
| `download_video` | Save the finished MP4 locally. |
| `get_subtitles` | Fetch SRT/VTT (any embedded language). |
| `upload_to_youtube` | Publish (or retry) a finished job to a connected channel. |
| `cancel_job` | Cancel/delete. |
| `list_languages` | Source + target language list (17 target languages). |
| `get_quota` | Current minute & request usage vs. plan limits. |

Dubbing tools (`create_dub`, `dub_youtube`) accept an optional `tts_provider`: `xtts` (quality voice, **default**), `chatterbox` (emotion voice), or `elevenlabs` (paid).

## 4. Override the API base (dev)

```bash
SPIMOV_API_BASE=http://localhost:8000/api/v1 spimov-mcp
```
