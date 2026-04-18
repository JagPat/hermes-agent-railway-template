import asyncio
import base64
import json
import os
import re
import secrets
import signal
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, StreamingResponse
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocket, WebSocketDisconnect

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_urlsafe(16)
    print(f"Generated admin password: {ADMIN_PASSWORD}")

HERMES_HOME = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
ENV_FILE_PATH = Path(HERMES_HOME) / ".env"
PAIRING_DIR = Path(HERMES_HOME) / "pairing"
SESSIONS_DIR = Path(HERMES_HOME) / "sessions"
SESSION_REGISTRY_PATH = SESSIONS_DIR / "_registry.json"
CODE_TTL_SECONDS = 3600

API_SERVER_HOST = os.environ.get("API_SERVER_HOST", "127.0.0.1")
API_SERVER_PORT = os.environ.get("API_SERVER_PORT", "8642")
API_SERVER_TARGET = f"http://{API_SERVER_HOST}:{API_SERVER_PORT}"

# Mission Control dashboard (hermes dashboard) — same container, different port.
DASHBOARD_HOST = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = os.environ.get("DASHBOARD_PORT", "9119")
DASHBOARD_TARGET = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}"
DASHBOARD_WS_TARGET = f"ws://{DASHBOARD_HOST}:{DASHBOARD_PORT}"

# Registry of known Hermes env vars exposed in the UI.
# Each entry: (key, label, category, is_password)
ENV_VAR_DEFS = [
    # Model
    ("LLM_MODEL", "Model", "model", False),
    # Providers
    ("OPENROUTER_API_KEY", "OpenRouter API Key", "provider", True),
    ("DEEPSEEK_API_KEY", "DeepSeek API Key", "provider", True),
    ("DASHSCOPE_API_KEY", "DashScope API Key", "provider", True),
    ("GLM_API_KEY", "GLM / Z.AI API Key", "provider", True),
    ("KIMI_API_KEY", "Kimi API Key", "provider", True),
    ("MINIMAX_API_KEY", "MiniMax API Key", "provider", True),
    ("HF_TOKEN", "Hugging Face Token", "provider", True),
    # Tools
    ("PARALLEL_API_KEY", "Parallel API Key", "tool", True),
    ("FIRECRAWL_API_KEY", "Firecrawl API Key", "tool", True),
    ("TAVILY_API_KEY", "Tavily API Key", "tool", True),
    ("FAL_KEY", "FAL API Key", "tool", True),
    ("BROWSERBASE_API_KEY", "Browserbase API Key", "tool", True),
    ("BROWSERBASE_PROJECT_ID", "Browserbase Project ID", "tool", False),
    ("GITHUB_TOKEN", "GitHub Token", "tool", True),
    ("VOICE_TOOLS_OPENAI_KEY", "OpenAI Voice Key", "tool", True),
    ("HONCHO_API_KEY", "Honcho API Key", "tool", True),
    # Messaging Ã¢ÂÂ Telegram
    ("TELEGRAM_BOT_TOKEN", "Telegram Bot Token", "messaging", True),
    ("TELEGRAM_ALLOWED_USERS", "Telegram Allowed Users", "messaging", False),
    # Messaging Ã¢ÂÂ Discord
    ("DISCORD_BOT_TOKEN", "Discord Bot Token", "messaging", True),
    ("DISCORD_ALLOWED_USERS", "Discord Allowed Users", "messaging", False),
    # Messaging Ã¢ÂÂ Slack
    ("SLACK_BOT_TOKEN", "Slack Bot Token", "messaging", True),
    ("SLACK_APP_TOKEN", "Slack App Token", "messaging", True),
    # Messaging Ã¢ÂÂ WhatsApp
    ("WHATSAPP_ENABLED", "WhatsApp Enabled", "messaging", False),
    # Messaging Ã¢ÂÂ Email
    ("EMAIL_ADDRESS", "Email Address", "messaging", False),
    ("EMAIL_PASSWORD", "Email Password", "messaging", True),
    ("EMAIL_IMAP_HOST", "Email IMAP Host", "messaging", False),
    ("EMAIL_SMTP_HOST", "Email SMTP Host", "messaging", False),
    # Messaging Ã¢ÂÂ Mattermost
    ("MATTERMOST_URL", "Mattermost URL", "messaging", False),
    ("MATTERMOST_TOKEN", "Mattermost Token", "messaging", True),
    # Messaging Ã¢ÂÂ Matrix
    ("MATRIX_HOMESERVER", "Matrix Homeserver", "messaging", False),
    ("MATRIX_ACCESS_TOKEN", "Matrix Access Token", "messaging", True),
    ("MATRIX_USER_ID", "Matrix User ID", "messaging", False),
    # Messaging Ã¢ÂÂ General
    ("GATEWAY_ALLOW_ALL_USERS", "Allow All Users", "messaging", False),
]

PASSWORD_KEYS = {key for key, _, _, is_pw in ENV_VAR_DEFS if is_pw}

PROVIDER_KEYS = [key for key, _, cat, _ in ENV_VAR_DEFS if cat == "provider" and key != "LLM_MODEL"]
CHANNEL_KEYS = {
    "Telegram": "TELEGRAM_BOT_TOKEN",
    "Discord": "DISCORD_BOT_TOKEN",
    "Slack": "SLACK_BOT_TOKEN",
    "WhatsApp": "WHATSAPP_ENABLED",
    "Email": "EMAIL_ADDRESS",
    "Mattermost": "MATTERMOST_TOKEN",
    "Matrix": "MATRIX_ACCESS_TOKEN",
}


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def write_env_file(path: Path, env_vars: dict[str, str]):
    path.parent.mkdir(parents=True, exist_ok=True)

    categories = {"model": "Model", "provider": "Providers", "tool": "Tools", "messaging": "Messaging"}
    grouped: dict[str, list[str]] = {cat: [] for cat in categories}
    known_keys = {key for key, _, _, _ in ENV_VAR_DEFS}
    key_to_cat = {key: cat for key, _, cat, _ in ENV_VAR_DEFS}

    for key, value in env_vars.items():
        if not value:
            continue
        cat = key_to_cat.get(key, "other")
        line = f"{key}={value}"
        if cat in grouped:
            grouped[cat].append(line)
        else:
            grouped.setdefault("other", []).append(line)

    lines = []
    for cat, heading in categories.items():
        entries = grouped.get(cat, [])
        if entries:
            lines.append(f"# {heading}")
            lines.extend(sorted(entries))
            lines.append("")

    other = grouped.get("other", [])
    if other:
        lines.append("# Other")
        lines.extend(sorted(other))
        lines.append("")

    path.write_text("\n".join(lines) + "\n" if lines else "")


def mask_secrets(env_vars: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in env_vars.items():
        if key in PASSWORD_KEYS and value:
            result[key] = value[:8] + "***" if len(value) > 8 else "***"
        else:
            result[key] = value
    return result


def merge_secrets(new_vars: dict[str, str], existing_vars: dict[str, str]) -> dict[str, str]:
    result = {}
    for key, value in new_vars.items():
        if key in PASSWORD_KEYS and value.endswith("***"):
            result[key] = existing_vars.get(key, "")
        else:
            result[key] = value
    return result


# ─── Session Registry ──────────────────────────────────────────────────
# This Hermes instance is dedicated to Chanakya-Bot (AI trading platform).
# Each Chanakya service (web, worker, central, bot) gets its own session
# for persistent conversation context. Heavy features (strategy optimisation,
# deep analysis) route to dedicated sessions to avoid context pollution.
#
# Registry file: /data/.hermes/sessions/_registry.json
# Callers identify themselves with a friendly `x-caller-id` header (e.g.
# `chanakya-brain`) which is auto-mapped to a session_id (`chanakya:brain`).
# Callers may also send `x-hermes-session-id` directly.

# Default sessions created lazily on first boot. Callers that use these
# identifiers get consistent, persistent context across deploys.
DEFAULT_SESSIONS = {
    "chanakya:brain": {
        "label": "Chanakya Brain",
        "description": "Main AI orchestration — verdicts, recommendations",
    },
    "chanakya:worker": {
        "label": "Chanakya Worker",
        "description": "Background analysis loop, scheduling",
    },
    "chanakya:central": {
        "label": "Chanakya Central (OTS)",
        "description": "Operational truth service queries",
    },
    "chanakya:sage": {
        "label": "Chanakya Sage",
        "description": "User-facing conversational assistant",
    },
    "chanakya:optimizer": {
        "label": "Strategy Optimizer",
        "description": "Dedicated context for STRATEGY_OPTIMIZATION feature",
    },
    "chanakya:analyst": {
        "label": "Deep Analyst",
        "description": "Dedicated context for DEEP_ANALYSIS feature",
    },
}

# Friendly caller-id -> session_id mapping. Keys are case-insensitive
# and normalised to lowercase before lookup.
CALLER_ALIASES = {
    "chanakya-brain": "chanakya:brain",
    "chanakya-worker": "chanakya:worker",
    "chanakya-central": "chanakya:central",
    "chanakya-sage": "chanakya:sage",
    "chanakya-optimizer": "chanakya:optimizer",
    "chanakya-analyst": "chanakya:analyst",
}

_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*:[a-zA-Z0-9][a-zA-Z0-9_\-]*$")


def _load_session_registry() -> dict:
    if not SESSION_REGISTRY_PATH.exists():
        return {}
    try:
        data = json.loads(SESSION_REGISTRY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[sessions] Failed to load registry: {exc}")
        return {}


def _save_session_registry(registry: dict) -> None:
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_REGISTRY_PATH.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[sessions] Failed to save registry: {exc}")


def _ensure_default_sessions() -> dict:
    """Create default session entries if they don't yet exist. Idempotent."""
    registry = _load_session_registry()
    changed = False
    for sid, info in DEFAULT_SESSIONS.items():
        if sid not in registry:
            registry[sid] = {
                **info,
                "created_at": time.time(),
                "last_used": None,
                "request_count": 0,
            }
            changed = True
    if changed:
        _save_session_registry(registry)
        print(f"[sessions] Seeded {len(DEFAULT_SESSIONS)} default sessions")
    return registry


def _validate_session_id(session_id: str | None) -> str | None:
    """Return session_id if it matches the `prefix:name` format, else None."""
    if not session_id or not isinstance(session_id, str):
        return None
    if not _SESSION_ID_PATTERN.match(session_id):
        return None
    return session_id


def _resolve_caller_to_session(caller_id: str | None) -> str | None:
    """Map a friendly caller-id into a namespaced session_id."""
    if not caller_id:
        return None
    key = caller_id.strip().lower()
    if not key:
        return None
    if key in CALLER_ALIASES:
        return CALLER_ALIASES[key]
    # Accept already-namespaced ids as-is
    return _validate_session_id(caller_id)


_session_lock = asyncio.Lock()


async def _touch_session(session_id: str) -> None:
    """Update last_used + request_count for a session. Creates entry if missing."""
    async with _session_lock:
        registry = _load_session_registry()
        entry = registry.get(session_id)
        if not entry:
            entry = {
                "label": session_id,
                "description": "Auto-created on first use",
                "created_at": time.time(),
                "last_used": None,
                "request_count": 0,
            }
        entry["last_used"] = time.time()
        entry["request_count"] = int(entry.get("request_count", 0)) + 1
        registry[session_id] = entry
        _save_session_registry(registry)


def _resolve_session_from_request(request: Request) -> str | None:
    """Resolve a valid namespaced session_id from request headers.

    Priority: explicit x-hermes-session-id > friendly x-caller-id alias.
    Returns None if neither header yields a valid namespaced id.
    """
    explicit = request.headers.get("x-hermes-session-id")
    resolved = _validate_session_id(explicit)
    if resolved:
        return resolved
    caller_id = request.headers.get("x-caller-id")
    return _resolve_caller_to_session(caller_id)


# ─── End Session Registry ──────────────────────────────────────────────


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        # Skip basic auth for /v1/* routes Ã¢ÂÂ they use Bearer token auth via Hermes API server
        path = conn.url.path
        if (
            path.startswith("/v1/")
            or path.startswith("/paperclip/")
            or path == "/health"
        ):
            return AuthCredentials(["authenticated"]), SimpleUser("api_client")

        if "Authorization" not in conn.headers:
            return None

        auth = conn.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != "basic":
                return None
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError):
            raise AuthenticationError("Invalid credentials")

        username, _, password = decoded.partition(":")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return AuthCredentials(["authenticated"]), SimpleUser(username)

        raise AuthenticationError("Invalid credentials")


def require_auth(request: Request):
    if not request.user.is_authenticated:
        return PlainTextResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="hermes"'},
        )
    return None


# âââ Paperclip â Hermes Translation Layer âââââââââââââââââââââââââ
# Accepts Paperclip HTTP adapter format, translates to OpenAI chat
# completions, calls internal Hermes API server, returns result.

API_SERVER_KEY = os.environ.get("API_SERVER_KEY", "")


def _extract_messages_from_paperclip(body: dict) -> list[dict]:
    """Extract or construct OpenAI messages array from Paperclip payload."""
    # If Paperclip sends messages directly (future-proof)
    if "messages" in body and isinstance(body["messages"], list):
        return body["messages"]

    # Extract from context object
    ctx = body.get("context", {})
    if isinstance(ctx, dict):
        if "messages" in ctx and isinstance(ctx["messages"], list):
            return ctx["messages"]

        # Build from task fields
        parts = []
        task_title = ctx.get("taskTitle") or ctx.get("task_title") or ""
        task_body = ctx.get("taskBody") or ctx.get("task_body") or ctx.get("description") or ""
        instructions = ctx.get("instructions") or ctx.get("systemPrompt") or ""

        if task_title or task_body:
            content = ""
            if task_title:
                content += f"Task: {task_title}\n\n"
            if task_body:
                content += task_body
            parts.append({"role": "user", "content": content.strip()})
        elif ctx.get("prompt"):
            parts.append({"role": "user", "content": ctx["prompt"]})

        if instructions and parts:
            parts.insert(0, {"role": "system", "content": instructions})

        if parts:
            return parts

    # Last resort: dump the whole body as user message
    fallback_content = json.dumps(body, indent=2, default=str)[:4000]
    return [{"role": "user", "content": f"Process this request:\n{fallback_content}"}]


async def paperclip_invoke(request: Request):
    """Translation endpoint: Paperclip HTTP adapter -> Hermes chat completions."""
    if not AIOHTTP_AVAILABLE:
        return JSONResponse({"error": "aiohttp not installed"}, status_code=503)

    try:
        body = await request.json()
    except Exception:
        # Log raw body for debugging
        raw = await request.body()
        print(f"[paperclip-invoke] Bad JSON. Raw body: {raw[:500]}")
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    agent_id = body.get("agentId", "unknown")
    run_id = body.get("runId", "unknown")
    print(f"[paperclip-invoke] Received: agent={agent_id} run={run_id} keys={list(body.keys())}")
    # Log full body for first-time debugging (remove later)
    print(f"[paperclip-invoke] Full body: {json.dumps(body, default=str)[:2000]}")

    messages = _extract_messages_from_paperclip(body)

    # Read model from Hermes config
    env_vars = read_env_file(ENV_FILE_PATH)
    model = env_vars.get("LLM_MODEL") or os.environ.get("LLM_MODEL", "auto")

    chat_request = {
        "model": model,
        "messages": messages,
        "max_tokens": 16384,
    }

    # Session resolution (Phase 3):
    #   1) Explicit sessionParams.sessionId from the Paperclip payload.
    #   2) x-hermes-session-id header (already validated against namespaces).
    #   3) x-caller-id header mapped via CALLER_ALIASES.
    #   4) agentId from the Paperclip body mapped via CALLER_ALIASES.
    session_id = None
    ctx = body.get("context", {})
    if isinstance(ctx, dict):
        sp = ctx.get("sessionParams") or {}
        raw_id = sp.get("sessionId") if isinstance(sp, dict) else None
        session_id = _validate_session_id(raw_id)

    if not session_id:
        session_id = _resolve_session_from_request(request)

    if not session_id and agent_id and agent_id != "unknown":
        session_id = _resolve_caller_to_session(agent_id)

    if session_id:
        try:
            await _touch_session(session_id)
        except Exception as exc:
            print(f"[paperclip-invoke] Session touch failed: {exc}")

    target_url = f"{API_SERVER_TARGET}/v1/chat/completions"
    forward_headers = {"content-type": "application/json"}
    if API_SERVER_KEY:
        forward_headers["authorization"] = f"Bearer {API_SERVER_KEY}"
    if session_id:
        forward_headers["x-hermes-session-id"] = session_id

    try:
        session = await _get_proxy_session()
        resp = await session.request(
            method="POST", url=target_url,
            headers=forward_headers, json=chat_request,
        )
        resp_body = await resp.read()
        resp_data = json.loads(resp_body.decode("utf-8", errors="replace"))
        resp.release()

        if resp.status != 200:
            err_msg = resp_data.get("error", {}).get("message", "Unknown") if isinstance(resp_data, dict) else str(resp_data)[:500]
            print(f"[paperclip-invoke] Hermes error: {resp.status} {err_msg}")
            return JSONResponse({
                "exitCode": 1, "timedOut": False, "errorMessage": f"Hermes: {err_msg}",
                "summary": err_msg, "resultJson": {"result": "", "session_id": ""},
            })

        choices = resp_data.get("choices", [])
        assistant_msg = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = resp_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        resp_session_id = session_id or f"hermes_{run_id}_{int(time.time())}"

        result = {
            "exitCode": 0, "signal": None, "timedOut": False,
            "provider": "openrouter", "model": resp_data.get("model", model),
            "summary": assistant_msg[:2000],
            "resultJson": {
                "result": assistant_msg,
                "session_id": resp_session_id,
                "usage": {"inputTokens": input_tokens, "outputTokens": output_tokens},
                "cost_usd": 0,
            },
            "sessionParams": {"sessionId": resp_session_id},
            "sessionDisplayId": resp_session_id[:16],
            "usage": {"inputTokens": input_tokens, "outputTokens": output_tokens},
        }

        print(f"[paperclip-invoke] OK: model={resp_data.get('model')} tokens={input_tokens}+{output_tokens}")
        return JSONResponse(result)

    except aiohttp.ClientConnectorError:
        return JSONResponse({"exitCode": 1, "timedOut": False, "errorMessage": "Hermes not reachable",
                             "summary": "Gateway starting", "resultJson": {"result": "", "session_id": ""}})
    except asyncio.TimeoutError:
        return JSONResponse({"exitCode": 1, "timedOut": True, "errorMessage": "Timed out",
                             "summary": "Timed out", "resultJson": {"result": "", "session_id": ""}})
    except Exception as e:
        print(f"[paperclip-invoke] Error: {type(e).__name__}: {e}")
        return JSONResponse({"exitCode": 1, "timedOut": False, "errorMessage": str(e),
                             "summary": f"Error: {e}", "resultJson": {"result": "", "session_id": ""}})


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ /v1/* Reverse Proxy to Hermes API Server Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

_proxy_session: aiohttp.ClientSession | None = None if AIOHTTP_AVAILABLE else None


async def _get_proxy_session() -> "aiohttp.ClientSession":
    global _proxy_session
    if _proxy_session is None or _proxy_session.closed:
        timeout = aiohttp.ClientTimeout(total=300)  # 5 min for long agent responses
        _proxy_session = aiohttp.ClientSession(timeout=timeout)
    return _proxy_session


async def _close_proxy_session():
    global _proxy_session
    if _proxy_session and not _proxy_session.closed:
        await _proxy_session.close()
        _proxy_session = None


async def v1_proxy(request: Request):
    """Reverse-proxy /v1/* requests to the internal Hermes API server.
    No basic auth required Ã¢ÂÂ Hermes uses its own API_SERVER_KEY Bearer auth."""
    if not AIOHTTP_AVAILABLE:
        return JSONResponse(
            {"error": "aiohttp not installed Ã¢ÂÂ proxy unavailable"},
            status_code=503,
        )

    path = request.url.path
    target_url = f"{API_SERVER_TARGET}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward relevant headers (Authorization, Content-Type, etc.)
    forward_headers = {}
    for key in ("authorization", "content-type", "accept", "x-hermes-session-id"):
        val = request.headers.get(key)
        if val:
            forward_headers[key] = val

    # Phase 3: resolve friendly x-caller-id into a namespaced session_id
    # and track usage on the registry. Explicit x-hermes-session-id (if
    # valid) always wins; otherwise we map the caller alias.
    resolved_session = _resolve_session_from_request(request)
    if resolved_session:
        forward_headers["x-hermes-session-id"] = resolved_session
        try:
            await _touch_session(resolved_session)
        except Exception as exc:
            print(f"[v1-proxy] Session touch failed: {exc}")

    body = await request.body()

    try:
        session = await _get_proxy_session()
        resp = await session.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            data=body if body else None,
        )

        # Check if this is a streaming response (SSE)
        content_type = resp.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Stream the response back
            async def stream_generator():
                try:
                    async for chunk in resp.content.iter_any():
                        yield chunk
                finally:
                    resp.release()

            return StreamingResponse(
                stream_generator(),
                status_code=resp.status,
                headers={
                    "content-type": content_type,
                    "cache-control": "no-cache",
                },
            )
        else:
            # Non-streaming: read full response and return
            resp_body = await resp.read()
            resp_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")
            }
            resp.release()
            return PlainTextResponse(
                content=resp_body.decode("utf-8", errors="replace"),
                status_code=resp.status,
                headers=resp_headers,
                media_type=content_type or "application/json",
            )
    except aiohttp.ClientConnectorError:
        return JSONResponse(
            {"error": "Hermes API server not reachable Ã¢ÂÂ gateway may still be starting"},
            status_code=503,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            {"error": "Request to Hermes API server timed out"},
            status_code=504,
        )
    except Exception as e:
        return JSONResponse(
            {"error": f"Proxy error: {type(e).__name__}: {e}"},
            status_code=502,
        )


# --- Mission Control dashboard reverse proxy (HTTP + WebSocket) ---
# The `hermes dashboard` process runs in the same container on DASHBOARD_PORT
# (default 9119). We proxy everything through the wrapper so the dashboard is
# reachable at the public URL (behind Basic auth) without exposing a second
# port. Binary-safe: response bodies are streamed as raw bytes.

# Hop-by-hop headers that must NOT be forwarded between client and upstream
# (RFC 7230 sec 6.1). Case-insensitive.
_HOP_BY_HOP = frozenset({
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
    # These are managed by aiohttp / Starlette; forwarding them corrupts the body.
    "content-encoding", "content-length",
    # Host must be set by the HTTP client for the upstream connection.
    "host",
})


def _filter_headers(headers) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP}


async def dashboard_http_proxy(request: Request):
    """Reverse-proxy HTTP requests to the Mission Control dashboard.

    Streams raw bytes to preserve binary assets (JS bundles, images, fonts).
    Requires Basic auth — Mission Control ships with no auth of its own.
    """
    auth_err = require_auth(request)
    if auth_err:
        return auth_err

    if not AIOHTTP_AVAILABLE:
        return JSONResponse(
            {"error": "aiohttp not installed - proxy unavailable"},
            status_code=503,
        )

    path = request.url.path
    target_url = f"{DASHBOARD_TARGET}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    forward_headers = _filter_headers(request.headers)
    body = await request.body()

    try:
        session = await _get_proxy_session()
        resp = await session.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            data=body if body else None,
            allow_redirects=False,
        )

        resp_headers = _filter_headers(resp.headers)
        content_type = resp.headers.get("content-type", "application/octet-stream")

        async def stream_generator():
            try:
                async for chunk in resp.content.iter_any():
                    yield chunk
            finally:
                resp.release()

        return StreamingResponse(
            stream_generator(),
            status_code=resp.status,
            headers=resp_headers,
            media_type=content_type,
        )
    except aiohttp.ClientConnectorError:
        return JSONResponse(
            {"error": "Dashboard not reachable - it may still be starting"},
            status_code=503,
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            {"error": "Dashboard request timed out"},
            status_code=504,
        )
    except Exception as e:
        return JSONResponse(
            {"error": f"Dashboard proxy error: {type(e).__name__}: {e}"},
            status_code=502,
        )


async def dashboard_ws_proxy(websocket: WebSocket):
    """Bidirectional WebSocket relay for the dashboard.

    Requires Basic auth — unauthenticated connections are closed before accept.
    """
    # Close unauthenticated WS before the handshake completes. Browsers that
    # supply credentials on the parent HTTP page will carry them into the WS
    # handshake via the Cookie / Authorization headers picked up by
    # AuthenticationMiddleware.
    if not getattr(websocket, "user", None) or not websocket.user.is_authenticated:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    if not AIOHTTP_AVAILABLE:
        await websocket.close(code=1011, reason="aiohttp unavailable")
        return

    await websocket.accept()

    path = websocket.url.path
    target_url = f"{DASHBOARD_WS_TARGET}{path}"
    if websocket.url.query:
        target_url += f"?{websocket.url.query}"

    # Forward only safe headers to the upstream WS handshake.
    forward_headers = {}
    for key in ("cookie", "authorization", "x-forwarded-for", "x-forwarded-proto"):
        val = websocket.headers.get(key)
        if val:
            forward_headers[key] = val

    try:
        session = await _get_proxy_session()
        async with session.ws_connect(target_url, headers=forward_headers) as upstream:

            async def forward_client_to_server():
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            await upstream.close()
                            break
                        if msg.get("text") is not None:
                            await upstream.send_str(msg["text"])
                        elif msg.get("bytes") is not None:
                            await upstream.send_bytes(msg["bytes"])
                except WebSocketDisconnect:
                    await upstream.close()
                except Exception as e:
                    print(f"[dashboard-ws] client->server: {type(e).__name__}: {e}")
                    await upstream.close()

            async def forward_server_to_client():
                try:
                    async for msg in upstream:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await websocket.send_text(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await websocket.send_bytes(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSE,
                                           aiohttp.WSMsgType.CLOSED,
                                           aiohttp.WSMsgType.ERROR):
                            break
                except Exception as e:
                    print(f"[dashboard-ws] server->client: {type(e).__name__}: {e}")
                finally:
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(
                forward_client_to_server(),
                forward_server_to_client(),
                return_exceptions=True,
            )
    except aiohttp.ClientConnectorError:
        try:
            await websocket.close(code=1011, reason="Dashboard not reachable")
        except Exception:
            pass
    except Exception as e:
        print(f"[dashboard-ws] setup error: {type(e).__name__}: {e}")
        try:
            await websocket.close(code=1011, reason="Upstream error")
        except Exception:
            pass


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ End Proxy Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ


class GatewayManager:
    def __init__(self):
        self.process: asyncio.subprocess.Process | None = None
        self.state = "stopped"
        self.logs: deque[str] = deque(maxlen=500)
        self.start_time: float | None = None
        self.restart_count = 0
        self._read_tasks: list[asyncio.Task] = []

    async def start(self):
        if self.process and self.process.returncode is None:
            return
        self.state = "starting"
        try:
            env = os.environ.copy()
            env["HERMES_HOME"] = HERMES_HOME
            env_vars = read_env_file(ENV_FILE_PATH)
            env.update(env_vars)

            self.process = await asyncio.create_subprocess_exec(
                "hermes", "gateway",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )
            self.state = "running"
            self.start_time = time.time()
            task = asyncio.create_task(self._read_output())
            self._read_tasks.append(task)
        except Exception as e:
            self.state = "error"
            self.logs.append(f"Failed to start gateway: {e}")

    async def stop(self):
        if not self.process or self.process.returncode is not None:
            self.state = "stopped"
            return
        self.state = "stopping"
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=10)
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
        self.state = "stopped"
        self.start_time = None

    async def restart(self):
        await self.stop()
        self.restart_count += 1
        await self.start()

    async def _read_output(self):
        try:
            while self.process and self.process.stdout:
                line = await self.process.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                cleaned = ANSI_ESCAPE.sub("", decoded)
                self.logs.append(cleaned)
        except asyncio.CancelledError:
            return
        if self.process and self.process.returncode is not None and self.state == "running":
            self.state = "error"
            self.logs.append(f"Gateway exited with code {self.process.returncode}")

    def get_status(self) -> dict:
        pid = None
        if self.process and self.process.returncode is None:
            pid = self.process.pid
        uptime = None
        if self.start_time and self.state == "running":
            uptime = int(time.time() - self.start_time)
        return {
            "state": self.state,
            "pid": pid,
            "uptime": uptime,
            "restart_count": self.restart_count,
        }


gateway = GatewayManager()
config_lock = asyncio.Lock()


async def homepage(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    return templates.TemplateResponse(request, "index.html")


async def health(request: Request):
    return JSONResponse({"status": "ok", "gateway": gateway.state})


async def api_config_get(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    async with config_lock:
        env_vars = read_env_file(ENV_FILE_PATH)
    defs = [
        {"key": key, "label": label, "category": cat, "password": is_pw}
        for key, label, cat, is_pw in ENV_VAR_DEFS
    ]
    return JSONResponse({"vars": mask_secrets(env_vars), "defs": defs})


async def api_config_put(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    try:
        restart = body.pop("_restartGateway", False)
        new_vars = body.get("vars", {})

        async with config_lock:
            existing = read_env_file(ENV_FILE_PATH)
            merged = merge_secrets(new_vars, existing)
            # Preserve any existing vars not in the UI
            for key, value in existing.items():
                if key not in merged:
                    merged[key] = value
            write_env_file(ENV_FILE_PATH, merged)

        if restart:
            asyncio.create_task(gateway.restart())

        return JSONResponse({"ok": True, "restarting": restart})
    except Exception as e:
        print(f"Config save error: {type(e).__name__}: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def api_status(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err

    env_vars = read_env_file(ENV_FILE_PATH)

    providers = {}
    for key in PROVIDER_KEYS:
        label = key.replace("_API_KEY", "").replace("_TOKEN", "").replace("HF_", "HuggingFace ").replace("_", " ").title()
        providers[label] = {"configured": bool(env_vars.get(key))}

    channels = {}
    for name, key in CHANNEL_KEYS.items():
        val = env_vars.get(key, "")
        channels[name] = {"configured": bool(val) and val.lower() not in ("false", "0", "no")}

    return JSONResponse({
        "gateway": gateway.get_status(),
        "providers": providers,
        "channels": channels,
    })


async def api_logs(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    return JSONResponse({"lines": list(gateway.logs)})


async def api_gateway_start(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    asyncio.create_task(gateway.start())
    return JSONResponse({"ok": True})


async def api_gateway_stop(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    asyncio.create_task(gateway.stop())
    return JSONResponse({"ok": True})


async def api_gateway_restart(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    asyncio.create_task(gateway.restart())
    return JSONResponse({"ok": True})


def _load_pairing_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_pairing_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _pairing_platforms(suffix: str) -> list[str]:
    if not PAIRING_DIR.exists():
        return []
    return [
        f.stem.rsplit(f"-{suffix}", 1)[0]
        for f in PAIRING_DIR.glob(f"*-{suffix}.json")
    ]


async def api_pairing_pending(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    now = time.time()
    results = []
    for platform in _pairing_platforms("pending"):
        pending = _load_pairing_json(PAIRING_DIR / f"{platform}-pending.json")
        for code, info in pending.items():
            age = now - info.get("created_at", now)
            if age > CODE_TTL_SECONDS:
                continue
            results.append({
                "platform": platform,
                "code": code,
                "user_id": info.get("user_id", ""),
                "user_name": info.get("user_name", ""),
                "age_minutes": int(age / 60),
            })
    return JSONResponse({"pending": results})


async def api_pairing_approve(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    platform = body.get("platform", "")
    code = body.get("code", "").upper().strip()
    if not platform or not code:
        return JSONResponse({"error": "platform and code required"}, status_code=400)

    pending_path = PAIRING_DIR / f"{platform}-pending.json"
    pending = _load_pairing_json(pending_path)
    if code not in pending:
        return JSONResponse({"error": "Code not found or expired"}, status_code=404)

    entry = pending.pop(code)
    _save_pairing_json(pending_path, pending)

    approved_path = PAIRING_DIR / f"{platform}-approved.json"
    approved = _load_pairing_json(approved_path)
    approved[entry["user_id"]] = {
        "user_name": entry.get("user_name", ""),
        "approved_at": time.time(),
    }
    _save_pairing_json(approved_path, approved)

    return JSONResponse({"ok": True, "user_id": entry["user_id"], "user_name": entry.get("user_name", "")})


async def api_pairing_deny(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    platform = body.get("platform", "")
    code = body.get("code", "").upper().strip()
    if not platform or not code:
        return JSONResponse({"error": "platform and code required"}, status_code=400)

    pending_path = PAIRING_DIR / f"{platform}-pending.json"
    pending = _load_pairing_json(pending_path)
    if code in pending:
        del pending[code]
        _save_pairing_json(pending_path, pending)

    return JSONResponse({"ok": True})


async def api_pairing_approved(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    results = []
    for platform in _pairing_platforms("approved"):
        approved = _load_pairing_json(PAIRING_DIR / f"{platform}-approved.json")
        for user_id, info in approved.items():
            results.append({
                "platform": platform,
                "user_id": user_id,
                "user_name": info.get("user_name", ""),
                "approved_at": info.get("approved_at", 0),
            })
    return JSONResponse({"approved": results})


async def api_pairing_revoke(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    platform = body.get("platform", "")
    user_id = body.get("user_id", "")
    if not platform or not user_id:
        return JSONResponse({"error": "platform and user_id required"}, status_code=400)

    approved_path = PAIRING_DIR / f"{platform}-approved.json"
    approved = _load_pairing_json(approved_path)
    if user_id in approved:
        del approved[user_id]
        _save_pairing_json(approved_path, approved)

    return JSONResponse({"ok": True})


# ─── Session registry API ─────────────────────────────────────────────


async def api_sessions_list(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    registry = _load_session_registry()
    # Return a stable, sorted list grouped by namespace
    sessions = []
    for sid, info in sorted(registry.items()):
        if not isinstance(info, dict):
            continue
        sessions.append({
            "session_id": sid,
            "label": info.get("label", sid),
            "description": info.get("description", ""),
            "created_at": info.get("created_at"),
            "last_used": info.get("last_used"),
            "request_count": info.get("request_count", 0),
        })
    return JSONResponse({
        "sessions": sessions,
        "aliases": CALLER_ALIASES,
    })


async def api_sessions_create(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    session_id = body.get("session_id", "").strip()
    valid = _validate_session_id(session_id)
    if not valid:
        return JSONResponse({
            "error": "session_id must be in 'prefix:name' format (e.g. 'chanakya:my-session')",
        }, status_code=400)

    label = body.get("label") or valid
    description = body.get("description") or ""

    async with _session_lock:
        registry = _load_session_registry()
        if valid in registry:
            return JSONResponse({"error": "Session already exists", "session_id": valid}, status_code=409)
        registry[valid] = {
            "label": label,
            "description": description,
            "created_at": time.time(),
            "last_used": None,
            "request_count": 0,
        }
        _save_session_registry(registry)

    return JSONResponse({"ok": True, "session_id": valid})


async def api_sessions_delete(request: Request):
    auth_err = require_auth(request)
    if auth_err:
        return auth_err
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    session_id = body.get("session_id", "").strip()
    if not session_id:
        return JSONResponse({"error": "session_id required"}, status_code=400)

    async with _session_lock:
        registry = _load_session_registry()
        if session_id not in registry:
            return JSONResponse({"error": "Session not found"}, status_code=404)
        del registry[session_id]
        _save_session_registry(registry)

    # Best-effort cleanup of any per-session JSON files Hermes itself wrote.
    # The Hermes API server owns those — we only prune the registry entry.
    return JSONResponse({"ok": True, "session_id": session_id})


# ─── End session registry API ─────────────────────────────────────────


async def auto_start_gateway():
    env_vars = read_env_file(ENV_FILE_PATH)
    has_provider = any(env_vars.get(key) for key in PROVIDER_KEYS)
    if has_provider:
        asyncio.create_task(gateway.start())


routes = [
    # --- Public / Bearer-auth endpoints (must come before the catch-all) ---
    Route("/health", health),
    # Paperclip translation endpoint (no basic auth)
    Route("/paperclip/invoke", paperclip_invoke, methods=["POST"]),
    # Reverse proxy: /v1/* -> Hermes API server (no basic auth - uses Bearer token)
    Route("/v1/{path:path}", v1_proxy, methods=["GET", "POST", "PUT", "DELETE", "PATCH"]),

    # --- Wrapper UI + its API, namespaced under /gateway/* to avoid
    #     colliding with Mission Control's own /api/* endpoints. ---
    Route("/gateway", homepage),
    Route("/gateway/", homepage),
    Route("/gateway/api/config", api_config_get, methods=["GET"]),
    Route("/gateway/api/config", api_config_put, methods=["PUT"]),
    Route("/gateway/api/status", api_status),
    Route("/gateway/api/logs", api_logs),
    Route("/gateway/api/gateway/start", api_gateway_start, methods=["POST"]),
    Route("/gateway/api/gateway/stop", api_gateway_stop, methods=["POST"]),
    Route("/gateway/api/gateway/restart", api_gateway_restart, methods=["POST"]),
    Route("/gateway/api/pairing/pending", api_pairing_pending),
    Route("/gateway/api/pairing/approve", api_pairing_approve, methods=["POST"]),
    Route("/gateway/api/pairing/deny", api_pairing_deny, methods=["POST"]),
    Route("/gateway/api/pairing/approved", api_pairing_approved),
    Route("/gateway/api/pairing/revoke", api_pairing_revoke, methods=["POST"]),
    Route("/gateway/api/sessions", api_sessions_list, methods=["GET"]),
    Route("/gateway/api/sessions", api_sessions_create, methods=["POST"]),
    Route("/gateway/api/sessions/delete", api_sessions_delete, methods=["POST"]),

    # --- Catch-all: everything else reverse-proxies to the Mission Control
    #     dashboard running on DASHBOARD_PORT inside the same container.
    #     WebSocket upgrades are routed here first (scope type=websocket),
    #     every other method falls through to the HTTP proxy below. ---
    WebSocketRoute("/{path:path}", dashboard_ws_proxy),
    Route(
        "/{path:path}",
        dashboard_http_proxy,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    ),
]

@asynccontextmanager
async def lifespan(app):
    # Seed the session registry with the default Vitan + Chanakya entries
    # on first boot. Idempotent — existing entries are preserved.
    try:
        _ensure_default_sessions()
    except Exception as exc:
        print(f"[lifespan] Session seeding failed: {exc}")
    await auto_start_gateway()
    yield
    await _close_proxy_session()
    await gateway.stop()


app = Starlette(
    routes=routes,
    middleware=[Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())],
    lifespan=lifespan,
)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info", loop="asyncio")
    server = uvicorn.Server(config)

    def handle_signal():
        loop.create_task(gateway.stop())
        server.should_exit = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    loop.run_until_complete(server.serve())
