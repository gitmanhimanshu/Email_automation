FROM python:3.12-slim

WORKDIR /app

COPY remote/requirements.txt ./remote/requirements.txt
RUN pip install --no-cache-dir -r remote/requirements.txt

COPY remote/ ./remote/

# SQLite lives here. On Railway/Render/Fly, mount a volume at /app/data or the
# database is wiped on every deploy, taking send history and resume links with it.
ENV DATABASE_PATH=/app/data/app.db
RUN mkdir -p /app/data

ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["python", "-m", "remote.server"]
