FROM ghcr.io/astral-sh/uv:python3.12-alpine

RUN apk add --no-cache bash curl tmux ttyd

WORKDIR /workspace

COPY start.sh /start.sh
COPY tmux.conf /etc/tmux.conf
RUN chmod +x /start.sh

EXPOSE 7681 8000

CMD ["/start.sh"]
