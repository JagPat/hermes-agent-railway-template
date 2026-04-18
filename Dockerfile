FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# Node.js 20.x required for Vite + Tailwind CSS v4 (Debian default is v18, too old)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Clone hermes-agent, install Python deps, and pre-build the React frontend.
#
# Bake the frontend build into the image so container start is deterministic.
# Two things must be true at runtime for `hermes dashboard` to serve the UI:
#
#   1. /tmp/hermes-agent/hermes_cli/web_dist/ must exist (where start_server
#      reads from — Path(__file__).parent / "web_dist").
#   2. /tmp/hermes-agent/web/package.json must NOT exist. Reason: cmd_dashboard
#      unconditionally calls _build_web_ui(PROJECT_ROOT / "web", fatal=True),
#      which early-returns only when web/package.json is absent (main.py:3239).
#      When it runs, Vite's emptyOutDir=true wipes the baked web_dist first,
#      then npm install fails in the slim runtime (no build toolchain), so
#      the dashboard never comes up on 9119.
#
# Therefore: after building, we drop the whole web/ source tree. The compiled
# output under hermes_cli/web_dist/ is what the server serves.
RUN git clone --depth 1 --branch v2026.4.16 https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent && \
    cd /tmp/hermes-agent && \
    uv pip install --system --no-cache -e ".[all,web]" && \
    cd web && npm ci && npm run build && \
    rm -rf /tmp/hermes-agent/.git /tmp/hermes-agent/web

COPY requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r /app/requirements.txt

RUN mkdir -p /data/.hermes

COPY server.py /app/server.py
COPY templates/ /app/templates/
COPY start.sh /app/start.sh
# Chanakya trading intelligence: memory seeds + skills.
# start.sh copies them to /data/.hermes on first boot without
# overwriting learned content that Hermes has accumulated.
COPY memory/ /app/memory/
COPY skills/ /app/skills/
RUN chmod +x /app/start.sh

ENV HOME=/data
ENV HERMES_HOME=/data/.hermes

CMD ["/app/start.sh"]
