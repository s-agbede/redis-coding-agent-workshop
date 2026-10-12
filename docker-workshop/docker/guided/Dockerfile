FROM ghcr.io/astral-sh/uv:latest AS uv
FROM codercom/code-server@sha256:4193b3a0c2661bce87b3cafede59e7d50e1e99e35f7c10bece7c2a7e0660c0a8

USER root
COPY --from=uv /uv /uvx /usr/local/bin/
RUN apt-get update && apt-get install -y --no-install-recommends curl tmux \
    && rm -rf /var/lib/apt/lists/*
ARG TARGETARCH
RUN case "$TARGETARCH" in arm64) tty_arch=aarch64 ;; amd64) tty_arch=x86_64 ;; *) exit 1 ;; esac \
    && curl -fsSL "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.$tty_arch" -o "/tmp/ttyd.$tty_arch" \
    && curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.7/SHA256SUMS -o /tmp/ttyd-checksums \
    && cd /tmp && grep " ttyd.$tty_arch\$" ttyd-checksums | sha256sum -c - \
    && install -m 755 "ttyd.$tty_arch" /usr/local/bin/ttyd \
    && rm ttyd.* ttyd-checksums
ENV UV_PYTHON_INSTALL_DIR=/opt/python
ENV UV_PYTHON_BIN_DIR=/usr/local/bin
ENV UV_PYTHON=3.12
RUN uv python install 3.12 --default

WORKDIR /opt/editor
COPY docker-workshop/backend/pyproject.toml docker-workshop/backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY docker-workshop/backend/app.py docker-workshop/backend/terminal.py ./
COPY docker-workshop/docker/guided/terminal.bash ./

# Preinstall learner dependencies outside the host's macOS virtual environment.
WORKDIR /opt/student
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY agent.py main.py tools.py ui.py demo.py preview.py check_setup.py verify_capstone.py pyproject.toml uv.lock README.md WORKSHOP.md FACILITATOR.md /opt/workshop/
COPY capstone /opt/workshop/capstone
COPY checkpoints /opt/workshop/checkpoints
COPY solutions /opt/workshop/solutions
COPY tests /opt/workshop/tests
COPY scripts/prepare_workspace.py /opt/workshop/prepare_workspace.py
COPY docker-workshop/docker/guided/start.sh /start.sh
COPY docker-workshop/docker/guided/tmux.conf /etc/tmux.conf
RUN chmod +x /start.sh

WORKDIR /workspace
ENV WORKSPACE_ROOT=/workspace
ENV UV_PROJECT_ENVIRONMENT=/opt/student/.venv
ENV PATH=/opt/student/.venv/bin:$PATH
EXPOSE 7681 8080 8081 8000
ENTRYPOINT []
CMD ["/start.sh"]
