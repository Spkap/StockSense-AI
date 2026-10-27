"""Publish the current working copy through AWS CLI, without uploading local env files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(__file__).parent / ".state"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--stack", default="stocksense-backend")
    parser.add_argument("--origin", action="append", default=[])
    args = parser.parse_args()
    STATE.mkdir(mode=0o700, exist_ok=True)
    STATE.chmod(0o700)

    def aws(*command):
        result = subprocess.run(["aws", "--region", args.region, *command,
                                 "--output", "json", "--no-cli-pager"],
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else None

    stack = aws("cloudformation", "describe-stacks", "--stack-name", args.stack)["Stacks"][0]
    if stack["StackStatus"] not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
        raise RuntimeError("Infrastructure is not ready: " + stack["StackStatus"])
    outputs = {entry["OutputKey"]: entry["OutputValue"] for entry in stack["Outputs"]}
    api_host = "stocksense." + outputs["PublicIp"].replace(".", "-") + ".sslip.io"
    origins = args.origin or ["https://stocksense-agent.vercel.app",
                              "https://stock-sense-ai-spkaps-projects.vercel.app"]
    local = dotenv_values(ROOT / ".env")
    keys = ("FIREWORKS_API_KEY", "FIREWORKS_MODEL", "NEWSAPI_KEY", "SUPABASE_URL",
            "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY")
    settings = {key: local[key] for key in keys if local.get(key)}
    if any(not settings.get(key) for key in keys if key != "FIREWORKS_MODEL"):
        raise RuntimeError("Configure the existing backend .env before deployment")
    settings.update(CORS_ORIGINS=",".join(origins), LOG_LEVEL="info")
    # AWS reads the private temporary file; credentials never become CLI arguments or logs.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as handle:
        os.chmod(handle.name, 0o600)
        json.dump(settings, handle)
        handle.flush()
        aws("secretsmanager", "put-secret-value", "--secret-id", outputs["SecretArn"],
            "--secret-string", "file://" + handle.name)

    files = [ROOT / "requirements.lock", ROOT / "requirements.txt"]
    files += sorted(path for path in (ROOT / "stocksense").rglob("*.py")
                    if "__pycache__" not in path.parts)
    files += [Path(__file__).parent / name for name in
              ("Dockerfile", "start.py", "compose.yaml", "Caddyfile")]
    manifest = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    release_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + digest[:12]
    archive = STATE / (release_id + ".tar.gz")
    with tarfile.open(archive, "w:gz") as package:
        for path in files:
            package.add(path, arcname=str(path.relative_to(ROOT)))
    object_key = "releases/" + archive.name
    subprocess.run(["aws", "--region", args.region, "s3", "cp", str(archive),
                    "s3://" + outputs["ArtifactBucket"] + "/" + object_key,
                    "--only-show-errors"], check=True)

    runtime = "\n".join(("RELEASE_ID=" + release_id, "AWS_REGION=" + args.region,
                           "API_HOST=" + api_host, "STOCKSENSE_SECRET_ID=" + outputs["SecretArn"])) + "\n"
    import base64
    runtime_b64 = base64.b64encode(runtime.encode()).decode()
    # All substituted values are locally generated infrastructure identifiers, never secrets.
    release_path = "/opt/stocksense/releases/" + release_id
    command = f"""set -eu
cloud-init status --wait
mkdir -p {shlex.quote(release_path)}
aws s3 cp {shlex.quote('s3://' + outputs['ArtifactBucket'] + '/' + object_key)} /tmp/stocksense-release.tar.gz --region {shlex.quote(args.region)} --only-show-errors
tar -xzf /tmp/stocksense-release.tar.gz -C {shlex.quote(release_path)}
cd {shlex.quote(release_path)}
echo {shlex.quote(runtime_b64)} | base64 --decode > runtime.env
docker compose -p stocksense --env-file runtime.env -f deploy/aws/compose.yaml build --pull api
docker rm -f stocksense-candidate 2>/dev/null || true
docker run -d --name stocksense-candidate --read-only --tmpfs /tmp:size=134217728,mode=1777 --memory 1400m --cpus 1.75 --cap-drop ALL --security-opt no-new-privileges --env AWS_REGION={shlex.quote(args.region)} --env STOCKSENSE_SECRET_ID={shlex.quote(outputs['SecretArn'])} -p 127.0.0.1:8001:8000 stocksense-backend:{release_id}
ready=0
for i in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8001/health -o /tmp/stocksense-health.json && python3 -c 'import json; assert json.load(open("/tmp/stocksense-health.json"))["status"]=="ok"'; then ready=1; break; fi
  sleep 3
done
if [ "$ready" != 1 ]; then docker logs --tail 60 stocksense-candidate; exit 1; fi
docker rm -f stocksense-candidate
docker compose -p stocksense --env-file runtime.env -f deploy/aws/compose.yaml up -d --wait --wait-timeout 120
if [ -L /opt/stocksense/current ]; then readlink /opt/stocksense/current > /opt/stocksense/previous; fi
ln -sfn {shlex.quote(release_path)} /opt/stocksense/current
docker compose -p stocksense --env-file runtime.env -f deploy/aws/compose.yaml ps
free -m
"""
    sent = aws("ssm", "send-command", "--instance-ids", outputs["InstanceId"],
               "--document-name", "AWS-RunShellScript", "--comment", "Deploy StockSense " + release_id,
               "--parameters", json.dumps({"commands": [command], "executionTimeout": ["1800"]}))
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    release = dict(outputs, region=args.region, stack=args.stack, release=release_id,
                   api_url="https://" + api_host, command_id=sent["Command"]["CommandId"],
                   branch=branch, source_sha256=digest, source_files=manifest)
    (STATE / "release.json").write_text(json.dumps(release, indent=2) + "\n")
    print(json.dumps({key: value for key, value in release.items() if key != "source_files"}, indent=2))


if __name__ == "__main__":
    main()
