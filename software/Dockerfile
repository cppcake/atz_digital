FROM debian:bookworm

RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-fastapi \
    python3-uvicorn \
    python3-jinja2 \
    python3-pytest \
    python3-serial \
    python3-requests \
    python3-pil \
    && apt-get clean

WORKDIR /repo
COPY . /repo

# This line has been generated using GitHub CoPilot with GPT-4.1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /repo/app/web/imgs /repo/app/sessions || true

RUN chmod +x ./init_container.sh
ENTRYPOINT ["sh", "./init_container.sh"]

