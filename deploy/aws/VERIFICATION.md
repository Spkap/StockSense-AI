# Deployment verification

Verified on 27 October 2026 IST, using branch `deploy` and the existing local
working copy. Deployment infrastructure and a focused database security migration
were added; application source files were preserved.

| Component | Target |
| --- | --- |
| Frontend | https://stocksense-agent.vercel.app |
| API | https://stocksense.35-154-231-40.sslip.io |
| AWS | `061525532820`, `ap-south-1`, stack `stocksense-backend` |
| Instance | `i-0f776f16837d1c37f`, `t3.small`, `35.154.231.40` |
| Vercel | `spkaps-projects/stock-sense-ai` |
| Vercel deployment | `dpl_CPMvrbNTHHzjtmQbV2nQY6wkYoVz` |
| Supabase | `Stock-sense`, `mznluitmsoziwdskxzjv`, `Sourabh's Org` |

## Passed checks

- CloudFormation creation completed. The instance is running; the only public
  inbound ports are 80 and 443, and instance metadata requires IMDSv2.
- HTTPS validates normally; `/health` returns `ok`, including database access.
- Thirty backend/release source files match the local SHA256 manifest. Thirty-five
  deployed frontend application modules match the local source via the build map.
- The local frontend production build and Vercel build passed. The production
  bundle uses the AWS API and contains none of the local backend service/API keys.
- Vercel production Supabase settings match the local folder. Backend credentials
  are loaded from AWS Secrets Manager through the scoped instance role.
- Allowed frontend CORS preflight passes; a different origin gets no allow header.
  The user-data endpoint `/api/theses` returns 401 without authorization.
- RLS is enabled on the analysis cache, theses, positions, alerts, and thesis history.
  The permissive alerts policy was removed and signup-trigger API execution revoked.
  The focused migration is recorded as applied in Supabase migration history.
- A fresh AAPL stream completed in 41.7 seconds with 20 headlines, 21 price points,
  sentiment, independent critique, and a confirmed Supabase save/read-back.
- The public browser UI connected to EC2, completed research, rendered saved MSFT
  independent review (six critiques and seven downside scenarios), and had no
  captured browser console errors at the final check.
- After analysis, the API container used about 169 MiB, the proxy about 13 MiB;
  the host had about 1.2 GiB available and no swap usage. Container `pip check` passed.

## Limits and existing findings

One subsequent AAPL response had an unavailable skeptic review, which the existing
app clearly flagged while retaining its primary analysis. A later MSFT response
included the complete review. Model outputs can require retry; deployment does
not change that behavior.

Two existing Supabase WARN findings remain: the vector extension is in `public`,
and leaked-password protection is disabled. There are no security ERROR findings
from the post-change advisor. A complete interactive Google/email sign-in was not
performed; provider availability, hosted Auth configuration, and the initial OAuth
redirect were checked separately.

The API's initial hostname depends on sslip.io public DNS. AWS resources run
continuously and consume credits. Live resource readings and upstream services
can change. Operational commands and rollback steps are in [README.md](README.md).

## Provider resilience release

The release from commit `6617bd0` was deployed to EC2 and Vercel. Fifty targeted
provider, agent, streaming, cache, authentication, scheduler, and configuration
tests passed; the production frontend build succeeded. A live MSFT analysis
completed with 16 news headlines, 21 daily price points, an independent review,
and persistence in 36 seconds. The public browser read the saved analysis and
showed a headline's publisher, date, and source link with no captured console errors.
After an EC2 reboot, HTTPS, API and Supabase health, CORS, access protection, and
saved research checks passed. Startup briefly returned 502 while the API started.

NewsAPI subscription limits and licensing depend on the actual plan. Yahoo data
uses the unofficial yfinance library, so upstream availability can change. The
full interactive authentication flow was not retested in this verification.

## Sentiment and skeptic flow trace

After backing up and clearing the six existing cache rows, a fresh deployed MSFT
stream collected 16 headlines and 21 price points, ran sentiment and skeptic
model calls, and completed in about 35 seconds. Its headline assessments,
prices, critiques and bear cases matched the saved Supabase snapshot. A separate
fresh AAPL LangGraph request used all five research tools in five iterations;
20 headline assessments, 65 price points, six critiques and four bear cases
matched the saved snapshot. Both checks used real upstream services.

The dashboard uses a fixed staged stream; the ReAct route is a separate LangGraph
workflow. Both model passes use headlines rather than full articles. The skeptic
is a separate call using the same model and evidence, not independent sourcing.
Even with stricter prompts, the observed critic included interpretations not
established by the headlines. Users should verify model-generated claims at their
sources. Old cache rows are in the ignored local `data/verification/` backup;
that folder also holds the captured API traces for these checks.
