FROM python:3.12.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock \
    && python -m venv /opt/aws-runtime \
    && /opt/aws-runtime/bin/pip install --no-cache-dir boto3==1.40.59 \
    && useradd --uid 10001 --create-home stocksense
COPY stocksense ./stocksense
COPY deploy/aws/start.py ./start.py
USER stocksense
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=8)); assert r['status']=='ok'"
CMD ["/opt/aws-runtime/bin/python", "start.py"]
