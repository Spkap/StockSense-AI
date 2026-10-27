"""Read-only public readiness checks; optional fresh inference before presenting."""
import argparse
import json
import re
import ssl
import socket
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend", default="https://stocksense-agent.vercel.app")
    parser.add_argument("--api", default="https://stocksense.35-154-231-40.sslip.io")
    parser.add_argument("--live-ticker", help="Run a fresh paid-provider analysis, e.g. MSFT")
    args = parser.parse_args()
    api, frontend = args.api.rstrip("/"), args.frontend.rstrip("/")
    host = urlparse(api).hostname
    with socket.create_connection((host, 443), timeout=10) as raw:
        with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as tls:
            expiry = datetime.strptime(tls.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    assert expiry > datetime.now(timezone.utc) + timedelta(days=2), "TLS certificate expires soon"
    print("PASS HTTPS certificate:", expiry.isoformat(), flush=True)

    health = requests.get(api + "/health", timeout=15)
    health.raise_for_status()
    assert health.json()["status"] == "ok", "Backend dependency check is degraded"
    print("PASS API and Supabase health", flush=True)

    page = requests.get(frontend, timeout=15)
    page.raise_for_status()
    assert "id=\"root\"" in page.text, "Frontend did not return the app"
    asset = re.search(r'src="([^\"]+\.js)"', page.text)
    assert asset, "Frontend JavaScript bundle missing"
    bundle = requests.get(frontend + asset[1], timeout=20)
    bundle.raise_for_status()
    assert api in bundle.text, "Frontend build points to a different API"
    print("PASS public frontend and production API URL", flush=True)

    for origin, allowed in ((frontend, True), ("https://untrusted.example", False)):
        response = requests.options(api + "/api/theses", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        }, timeout=15)
        if allowed:
            assert response.status_code == 200 and response.headers.get("access-control-allow-origin") == origin
        else:
            assert response.status_code == 400 and "access-control-allow-origin" not in response.headers
    assert requests.get(api + "/api/theses", timeout=15).status_code == 401
    print("PASS CORS and unauthenticated user-data protection", flush=True)

    saved = requests.get(api + "/results/MSFT", timeout=15)
    saved.raise_for_status()
    assert saved.json()["data"].get("summary"), "Saved MSFT research unavailable"
    print("PASS saved MSFT research", flush=True)

    if args.live_ticker:
        started = time.monotonic()
        terminal = None
        with requests.get(api + "/analyze/" + requests.utils.quote(args.live_ticker.upper(), safe="") + "/stream",
                          headers={"Origin": frontend}, stream=True, timeout=(15, 200)) as stream:
            stream.raise_for_status()
            assert stream.headers.get("access-control-allow-origin") == frontend
            for line in stream.iter_lines():
                if line.startswith(b"data: "):
                    event = json.loads(line[6:])
                    print("STREAM", event.get("type"), event.get("message", ""), flush=True)
                    if event.get("type") in ("completed", "error"):
                        terminal = event
                        break
        assert terminal and terminal["type"] == "completed", "Live analysis did not complete"
        data = terminal["data"]
        assert data.get("cache_saved"), "Fresh analysis was not saved"
        assert data.get("critiques") and data.get("bear_cases"), "Independent review unavailable; retry or use saved research"
        print("PASS fresh analysis, independent review and persistence:", round(time.monotonic() - started, 1), "seconds", flush=True)
    print("READY: checked current live services; this is not a guarantee of future provider availability.")


if __name__ == "__main__":
    main()
