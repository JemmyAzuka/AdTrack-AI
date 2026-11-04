# AdTrack AI

A conversion event ledger and tracking-health dashboard for performance marketers.

AdTrack AI is designed to collect conversion events from first-party website/backend systems, CRM exports, CSV files and (in later connector stages) ad platforms such as Meta and TikTok. It helps answer:

- How many conversion events did our own systems record?
- Which source sent each event?
- Are event IDs missing or duplicated?
- Are campaign tags present?
- Do ad-platform totals differ from the first-party conversion ledger?

## What this MVP does

- Streamlit dashboard with conversion totals, value, source breakdown and daily trend.
- FastAPI endpoint for real-time first-party conversion ingestion.
- SQLite event ledger.
- Idempotency using `event_id` to prevent the same event being inserted twice.
- CSV import for website, CRM, backend and ad-platform exports.
- Basic data-quality warnings for missing event IDs and campaign tags.
- Sample data and a small automated test.

## What it does not do yet

- It does not automatically connect to Meta or TikTok accounts. Their APIs require app setup, access tokens, account permissions and provider-specific connector code.
- It cannot discover conversions that are never sent to AdTrack AI or included in an import.
- It does not claim that an event received from Meta/TikTok was caused by that platform. Event collection and ad attribution are different.
- AI-generated diagnosis and automated campaign changes are not enabled in this MVP.

## Architecture

```text
Website / checkout / app ──┐
CRM / sales system ────────┤
Meta + TikTok exports ─────┼──> FastAPI / CSV imports ──> SQLite event ledger
Backend / payment system ──┘                                  │
                                                              └──> Streamlit dashboard
```

For production, use your backend or CRM as the first-party conversion source of truth. Send the same stable `event_id` to browser and server tracking where the ad platform supports deduplication. Never send raw personal data unless you have a lawful basis and the required consent; use provider-approved hashing and consent controls.

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env             # optional for local testing
```

Start the event API:

```bash
uvicorn api:app --reload --port 8000
```

Start the dashboard in another terminal:

```bash
streamlit run app.py
```

Open the dashboard at `http://localhost:8501` and API docs at `http://localhost:8000/docs`.

## Send a test conversion

```bash
curl -X POST http://localhost:8000/v1/events \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: replace-with-a-long-random-secret" \\
  -d '{
    "event_id": "order-123-purchase",
    "source": "website",
    "event_name": "Purchase",
    "occurred_at": "2026-11-04T12:00:00Z",
    "value": 49.99,
    "currency": "USD",
    "order_id": "order-123",
    "utm_source": "meta",
    "utm_medium": "paid_social",
    "utm_campaign": "november_launch"
  }'
```

If `ADTRACK_API_KEY` is not set, the API accepts requests without a key for local development. Set it before deploying.

## CSV format

Required: `source`, `event_name`. Recommended: `event_id`, `occurred_at`, `value`, `currency`, `order_id`, `utm_source`, `utm_medium`, `utm_campaign`, `fbc`, `fbp`, `ttclid`, `gclid`.

Import a CSV from the dashboard sidebar. Events with an existing `event_id` are skipped.

## Run tests

```bash
pytest -q
```

## Roadmap

1. **MVP:** first-party event API, CSV ingestion, deduplication, dashboard and quality checks.
2. **Platform connectors:** Meta Conversions API / Insights, TikTok Events API / reporting APIs, OAuth token handling and scheduled sync.
3. **Reconciliation:** compare first-party event counts against platform event receipt and attributed conversions, with attribution windows labelled clearly.
4. **AI analyst:** explain anomalies and produce troubleshooting steps from event diagnostics.
5. **Production:** PostgreSQL, authentication, tenant isolation, encrypted secrets, retention controls, monitoring and deployment.

## Security notes

This is a learning MVP, not yet ready for production use with customer personal data. Add authentication, tenant isolation, HTTPS, rate limiting, secret management, retention/deletion workflows, audit logs and consent enforcement before using it with real customer data.
