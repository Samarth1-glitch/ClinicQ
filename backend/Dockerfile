FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m pip install --upgrade \
        "setuptools>=78.1.1" \
        "wheel>=0.46.2" \
        "urllib3>=2.8.0" \
        "msgpack>=1.2.1" \
    && python -m pip check

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
