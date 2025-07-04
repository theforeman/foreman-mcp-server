FROM quay.io/centos/centos:stream10

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

RUN mkdir app
WORKDIR /app

COPY ./ ./

RUN uv sync

ENTRYPOINT ["uv", "run", "foreman-mcp-server"]

