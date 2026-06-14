# spimov-mcp – AI Kılavuzu

Bu repo, eski `spimov` monorepo'sundan ayrılan **MCP server** parçasıdır (2026-06 split). PyPI paketi: `spimov-mcp`.

## Amaç
Spimov'u MCP üzerinden kullandıran sunucu. Backend'in **public v1 API**'sini API key ile tüketir; kendi başına iş mantığı barındırmaz.

## Yapı
- `src/spimov_mcp/server.py` — 13 araç tanımı
- `src/spimov_mcp/stdio_main.py` — stdio transport (yerel dosya upload destekler)
- `src/spimov_mcp/http_main.py` — HTTP/SSE transport (`mcp.spimov.com/sse`, URL-only)
- `pyproject.toml`, `build_and_publish.py`

## Transport kararı
- **stdio:** local dosya upload var → `create_dub` stdio-only. `SPIMOV_API_KEY` env var.
- **HTTP/SSE:** hosted, sadece URL tabanlı işler (dosya upload yok).

## Kardeş repolar
- `spimov-backend-dubbing` — public v1 API'yi sağlar (mcp onu tüketir)
- `spimov-frontend`, `spimov-lipsync`

## Sürüm & yayın
Sürüm artırırken: `pyproject.toml` bump → build → `twine upload`. **PyPI publish dışa dönük + geri alınamaz → önce insana sor.**

## Repo-arası seam (KIRMA)
- Backend public v1 API kontratı (`spk_live_*` Bearer)
- Araç imzaları = istemci kontratı; geriye dönük uyumu koru

## Rol
`.claude/agents/mcp.md` — **mcpçi**. PyPI publish öncesi insana sorar.
