# StockSense AWS deployment

The frontend stays in the existing Vercel project. The backend runs unchanged on
one Ubuntu EC2 `t3.small` (2 vCPU, 2 GiB RAM), with a 20 GiB encrypted gp3 volume
and 2 GiB swap. Caddy provides HTTPS and streams SSE without buffering. There is
one Uvicorn worker because the app starts its scheduler in its lifespan.

## Infrastructure and release

Use the authenticated AWS CLI in `ap-south-1`. Select a public subnet in your VPC:

```sh
aws cloudformation deploy --region ap-south-1 \
  --template-file deploy/aws/cloudformation.yaml \
  --stack-name stocksense-backend --capabilities CAPABILITY_IAM \
  --parameter-overrides VpcId=YOUR_VPC SubnetId=YOUR_PUBLIC_SUBNET \
  --tags Project=StockSense ManagedBy=CloudFormation

.venv/bin/python deploy/aws/release.py
```

`release.py` publishes an explicit allowlist of backend source files from the
current working copy, including uncommitted changes. It records their SHA256
hashes and release metadata in ignored `deploy/aws/.state/release.json`.
It never uploads `.env`, Git history, frontend sources, test data, or local tools.
It copies only required backend settings from the existing ignored `.env` into
AWS Secrets Manager. The container retrieves them in memory using its instance
role; no backend credentials are embedded in the image or stored on the server.
The AWS SDK has its own Python environment so it cannot change the app's locked
dependencies. After loading configuration, it executes the app's Python process.

The role can read only this stack's secret and release bucket. Administration uses
SSM; only ports 80 and 443 are public. A static Elastic IP makes the API address
stable. The initial HTTPS hostname uses sslip.io DNS and Caddy's automatic public
certificate issuance; a custom domain can replace it later.

Before cutover, the release runs a candidate container and requires a healthy
`/health` response. Compose then starts the release with automatic restart and
bounded memory/log files. Inspect the SSM command ID recorded in `release.json`:

```sh
aws ssm get-command-invocation --region ap-south-1 \
  --command-id COMMAND_ID --instance-id INSTANCE_ID
```

## Frontend

Project: `stock-sense-ai`, team: `spkaps-projects`.
Supabase project: `Stock-sense` (`mznluitmsoziwdskxzjv`), in `Sourabh's Org`.
The minimal Auth config in `deploy/aws/supabase/config.toml` sets the hosted site
and exact redirect allowlist while retaining local development. Inspect and apply
only these declared settings with the authenticated Supabase CLI:

```sh
supabase config diff --workdir deploy/aws --project-ref mznluitmsoziwdskxzjv
supabase config push --workdir deploy/aws --project-ref mznluitmsoziwdskxzjv --yes
```

Set production `VITE_API_URL` to the recorded HTTPS `api_url`; use the existing
Supabase URL and anon key, never the backend service key. Deploy the frontend
working copy from this branch and verify analysis streaming from its public URL.
Use the authenticated Vercel CLI to stage and then release the frontend:

```sh
vercel link --yes --project stock-sense-ai --scope spkaps-projects
vercel deploy --prod --skip-domain --yes --scope spkaps-projects
# Verify the returned deployment URL, then assign the production domains:
vercel promote DEPLOYMENT_URL --yes --scope spkaps-projects
```

The default backend CORS origins are `https://stocksense-agent.vercel.app` and
`https://stock-sense-ai-spkaps-projects.vercel.app`. Supply repeatable `--origin`
arguments to `release.py` when adding another frontend origin.

## Rollback and operations

The previous successful release path is saved in `/opt/stocksense/previous`.
Use an SSM Run Shell Script command to restore its image and configuration:

```sh
cd "$(cat /opt/stocksense/previous)"
docker compose -p stocksense --env-file runtime.env -f deploy/aws/compose.yaml up -d --wait
ln -sfn "$PWD" /opt/stocksense/current
```

Then verify the public `/health` endpoint and a streamed analysis. Vercel can
independently roll back to the prior production deployment. The first deployment
has no previous backend release. Runtime credentials always use the secret's
current version; code rollback does not restore credentials or database changes.

Use SSM to inspect `docker stats --no-stream`, `free -m`, and container logs.
`/health` checks configuration and Supabase connectivity; a full fresh analysis
is required to check provider calls and end-to-end streaming.

This instance runs continuously. AWS charges apply to compute, EBS, the public
IPv4 address, secret storage, and traffic; credit coverage depends on the account.
Stopping EC2 pauses the backend and its scheduler but keeps EBS and the Elastic IP.
To remove the deployment, first empty the private artifact bucket, then delete
the `stocksense-backend` CloudFormation stack. Secrets Manager uses its normal
recovery period. No other instances or resources are part of this stack.

## Supabase security

The deployment uses the existing database and schema. The accompanying
`20261026193223_harden_trigger_function_access.sql` migration fixes the inspected
trigger search paths, revokes unnecessary direct API execution of the signup
trigger, and removes a permissive anonymous alert INSERT policy. Normal users
retain their ownership policy; the scheduler uses the backend-only service role.

The post-change Supabase security advisor has no ERROR findings. Two existing
WARN findings remain: the vector extension is in the public schema, and Auth
leaked-password protection is disabled. Neither was changed as part of hosting.

The existing app explicitly flags an unavailable skeptic review when its model
response fails validation. Hosting checks cannot guarantee every provider response;
use saved research or retry when that warning appears.
