# Spimov MCP — Content / Listing Kit

Ready-to-use copy for the MCP marketplace, GitHub, PyPI, and launch posts.
Marketing sections sell outcomes; the **Tools** section is the developer-facing
reference. Everything below reflects the actual v0.6.0 capabilities.

---

## Taglines

> **Dub any video into 600+ languages — straight from your AI chat.**

- *AI video dubbing for Claude and any MCP client.*
- *Paste a YouTube, TikTok, Instagram, or Facebook link — get it dubbed. No dashboard, no downloads.*
- *Sign up, pay, and start dubbing without ever leaving the chat.*

---

## Short description (marketplace card / GitHub "About")

> Spimov MCP lets Claude (and any MCP client) dub videos into 600+ languages,
> edit translations line-by-line, generate speech and subtitles, and publish to
> YouTube — all from natural language. New users can even sign up and pay inline.
> Works locally (file upload) or over the hosted HTTP server.

One-line (PyPI / GitHub About):

> MCP server for Spimov — dub videos in 600+ languages, generate speech &
> subtitles, and publish to YouTube from Claude Desktop, Claude Code, or Claude web.

---

## Long description (listing body)

### Spimov MCP — AI video dubbing, inside your chat

Spimov MCP connects the [Spimov](https://spimov.com) dubbing engine to Claude and
any Model Context Protocol client. Ask in plain language — *"dub this TikTok into
German and upload it unlisted to my channel"* — and the whole pipeline runs
server-side: transcription, translation, voice cloning, lip-sync, and publishing.

**What you can do**

- 🎬 **Dub from any link or a local file** — YouTube (videos, Shorts, Music), **TikTok, Instagram, and Facebook**, or upload your own file.
- 🌍 **600+ target languages**, with automatic source-language detection.
- 🗣️ **Voice-preserving dubs** — the speaker's own voice is cloned into the new language automatically, emotion and all.
- ✍️ **Edit before you publish** — list transcript segments and fix any line's text, emotion, or speaker; only that segment is re-synthesized.
- 💬 **Subtitles your way** — fetch SRT/VTT, burn them in, embed soft tracks in extra languages, or **translate an existing SRT** on its own.
- 🔊 **Standalone Text-to-Speech** — turn any text into audio with **170+ ready voice presets** (no cloning setup needed).
- 🎚️ **Remix without re-dubbing** — adjust the audio mix, subtitle styling, or lip-sync on a finished job.
- 📺 **Publish to YouTube** automatically when the dub finishes.
- 🎨 **Jump into the studios** — get a link to AI video generation, the video cutter, UGC/ad maker, or the video editor when a task needs the browser.
- 🪄 **Onboard inline** — a brand-new user can sign up, get a checkout link, pay, and receive an API key **without leaving the chat** — no connector config.
- 🔗 **Get a shareable download link** for the finished MP4 — works in the browser, no API key needed.

**22 tools** across onboarding, dubbing, speech, editing, subtitles, publishing,
and studio hand-off (see below).

**Works everywhere MCP does**

- **Claude Desktop / Claude Code** (stdio) — supports local file upload.
- **Claude web & hosted clients** — connect to the hosted Streamable HTTP server, no install required.

**Setup in 2 minutes** — or skip it entirely: ask Claude to sign you up, pay via
the checkout link, and start dubbing right there.

---

## Tools (22)

> Developer-facing reference. MCP clients auto-discover these via `list_tools`;
> this table is here so human evaluators can see the full scope at a glance.

**Get started (no API key required)**
- `start_signup` — sign a new user up by email; returns a browser verify link
- `check_signup` — poll after verify to receive the new API key
- `create_checkout_link` — generate a DodoPayments checkout URL to upgrade a plan

**Create**
- `dub_from_url` — dub a YouTube / TikTok / Instagram / Facebook link
- `dub_youtube` — dub a YouTube link/Short; optional auto-upload to a channel
- `create_dub` — dub a local video file (stdio only)
- `text_to_speech` — synthesize speech from text using a voice preset
- `translate_srt` — translate an existing SRT subtitle file to another language

**Track**
- `get_job_status` · `list_jobs` · `get_quota` · `cancel_job`

**Edit & refine**
- `list_segments` — inspect transcript (text, speaker, emotion, timing)
- `update_segment` — edit one line's text/emotion/speaker; re-synths just that segment
- `remix_video` — re-render audio mix / subtitle styling / lip-sync, no re-dub

**Voices & languages**
- `list_voices` — 170+ voice presets (language, gender, style)
- `list_languages` — supported source/target languages

**Get results**
- `get_download_url` — shareable browser download link (use over HTTP/web)
- `download_video` — save the MP4 locally (stdio only)
- `get_subtitles` — fetch SRT/VTT in any embedded language
- `upload_to_youtube` — publish (or retry) a finished job to a connected channel

**Studio hand-off**
- `open_studio` — link to a browser studio: AI video generation, video cutter, UGC/ad, video edit, or YouTube automation

---

## Launch / announcement post (X / LinkedIn)

> We just shipped **Spimov MCP v0.6** 🎬
>
> Dub any video into **600+ languages** without leaving your AI chat. Paste a
> YouTube, TikTok, or Instagram link → Claude transcribes, translates, clones the
> voice, and can publish it straight to YouTube.
>
> • YouTube / TikTok / Instagram / Facebook, or a local file
> • Voice-preserving dubs — the original speaker's voice, new language
> • Edit any line, re-synth just that segment
> • Text-to-speech with 170+ voices + SRT translation
> • New? Sign up & pay right in the chat — no connector setup
> • Works in Claude Desktop, Claude Code & Claude web
>
> `pip install spimov-mcp` → spimov.com
> #MCP #Claude #AIdubbing

---

## Marketplace metadata (fields)

| Field | Value |
|---|---|
| **Name** | Spimov |
| **Category** | Media / Video |
| **Description** | Dub videos into 600+ languages, generate speech & subtitles, edit translations, and publish to YouTube — from any MCP client. Sign up and pay inline. |
| **Auth** | API key (`spk_live_…`) — or sign up inline with `start_signup` |
| **Homepage** | https://spimov.com |
| **Install (stdio)** | `pip install spimov-mcp` |
| **Connect (HTTP)** | `https://mcp.spimov.com/mcp` (Streamable HTTP; legacy SSE at `/sse`) |
