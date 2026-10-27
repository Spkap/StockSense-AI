"""Load backend credentials from the instance's scoped AWS secret, then start FastAPI."""
import json
import os

import boto3


def main():
    client = boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
    response = client.get_secret_value(SecretId=os.environ["STOCKSENSE_SECRET_ID"])
    settings = json.loads(response["SecretString"])
    required = ("FIREWORKS_API_KEY", "NEWSAPI_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY")
    if any(not settings.get(key) for key in required):
        raise RuntimeError("AWS backend secret is missing required configuration")
    os.environ.update({key: str(value) for key, value in settings.items()})
    # The scheduler starts in the app lifespan: one worker prevents duplicate jobs.
    # Replace the SDK environment with the app's Python and original locked packages.
    os.execv("/usr/local/bin/python", ["python", "-m", "uvicorn", "stocksense.main:app",
             "--host", "0.0.0.0", "--port", "8000", "--workers", "1",
             "--proxy-headers", "--forwarded-allow-ips", "172.16.0.0/12,127.0.0.1"])


if __name__ == "__main__":
    main()
