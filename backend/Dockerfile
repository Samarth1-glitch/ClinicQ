FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
    # Remove the packaging tools from the runtime image: the app does not need them, and
    # pip's vendored libraries (msgpack, urllib3, pkg_resources) are what Trivy flags.
    && pip uninstall -y pip setuptools wheel

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Run as a non-root user (numeric UID so Kubernetes runAsNonRoot can verify it)
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

EXPOSE 8000

# Apply migrations, then start the API
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]