FROM python:3.12-slim
# stdlib only — no pip layer (ADR-0002)
RUN useradd -r -u 10001 holocortex && mkdir -m 755 /app
COPY --chmod=644 holocortex_router.py /app/holocortex_router.py
USER holocortex
ENV HCR_LOG_FILE=/data/routing.jsonl
EXPOSE 8377
HEALTHCHECK --interval=60s --timeout=5s \
  CMD ["python3", "-c", "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8377/stats', timeout=4)"]
CMD ["python3", "-u", "/app/holocortex_router.py"]
