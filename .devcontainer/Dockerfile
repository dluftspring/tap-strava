ARG PYTHON_VERSION=3

FROM mcr.microsoft.com/devcontainers/python:${PYTHON_VERSION}-bullseye

RUN pipx install --system-site-packages \
    --pip-args '--no-cache-dir --force-reinstall' \
    ruff;

RUN pipx install --system-site-packages \
    --pip-args '--no-cache-dir --force-reinstall' \
    poetry;