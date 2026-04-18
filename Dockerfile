FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# Node.js 20.x required for Vite + Tailwind CSS v4 (Debian default is v18, too old)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Clone hermes-agent, install Python deps, and pre-build the React frontend.
# `hermes dashboard` falls back to an at-startup `npm install + npm run build`
# if web_dist/ is missing — that runtime build is unreliable (network flakes,
# ephemeral /tmp, disk pressure) and has already broken the dashboard on
# redeploy. Baking the build into the image makes container start deterministic.
RUN git clone --depth 1 --branch v2026.4.16 https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent && \
    cd /tmp/hermes-agent && \
    uv pip install --system --no-cache -e ".[all,web]" && \
    cd web && npm ci && npm run build && \
    rm -rf /tmp/hermes-agent/.git /tmp/hermes-agent/web/node_modules

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
