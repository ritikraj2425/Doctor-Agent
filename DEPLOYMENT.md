# Run and deploy Clarity

## Run locally

The app can use the local MongoDB configured in `.env`, or SQLite if you remove/unset `MONGODB_URI`.

```bash
source venv/bin/activate
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. The app creates `data/clarity.sqlite3` automatically when using SQLite. Local MongoDB stores the same account and chat data in the `clarity` database.

## Deploy to Vercel

This repository already has a FastAPI entry point in `main.py`, a `requirements.txt`, a `vercel.json` with a 300-second function duration, and the frontend under `static/`. Vercel's Python runtime supports FastAPI and streaming responses; no separate frontend build command is needed. [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi) · [Python runtime](https://vercel.com/docs/functions/runtimes/python)

### 1. Create a persistent MongoDB database

Create/use a MongoDB Atlas cluster and database user. Copy its `mongodb+srv://...` connection URI. The local URI `mongodb://127.0.0.1:27017` in your `.env` will not work from Vercel. SQLite on Vercel's `/tmp` is temporary and is not appropriate for persistent chat history.

Configure Atlas network access for Vercel's function egress. If your Vercel plan supports Static IPs, allowlist those addresses in Atlas. Atlas warns that `0.0.0.0/0` permits connections from anywhere; use it only if needed, with a strong database password and least-privilege database user. [Atlas IP access lists](https://www.mongodb.com/docs/atlas/security/ip-access-list/) · [Vercel Static IPs](https://vercel.com/changelog/static-ips-are-now-available-for-more-secure-connectivity)

### 2. Import the repository

Push this project to GitHub, then in Vercel choose **Add New → Project** and import the repository. Keep the Root Directory at the repository root. Vercel detects the FastAPI `app` in `main.py` and installs Python dependencies from `requirements.txt`. Leave the Build Command empty unless you add a build step later.

### 3. Add environment variables

In **Project → Settings → Environment Variables**, add the following for Production and Preview as needed:

| Name | Value |
| --- | --- |
| `MONGODB_URI` | Your Atlas `mongodb+srv://...` URI |
| `MONGODB_DATABASE` | `clarity` |
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | Optional; defaults to `qwen/qwen3.8-27b` |
| `GEMINI_API_KEY` | Gemini API key for fallback when Groq is rate-limited |
| `GEMINI_MODEL` | Optional; defaults to `gemini-3.8-flash` |
| `TAVILY_API_KEY` | Tavily search API key |
| `COHERE_API_KEY` | Cohere embeddings API key |
| `QDRANT_URL` | Qdrant cluster URL |
| `QDRANT_API_KEY` | Qdrant API key |

Gemini fallback requires a Google project that can call the Gemini API. The current local key returned HTTP 403 because its project does not have Gemini free-tier access; enable billing for that project or use a key from an eligible, enabled project. [Gemini project access troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting#project-unavailable)

Do not commit `.env` or put provider keys in frontend JavaScript. Vercel applies environment-variable changes only to new deployments, so redeploy after saving them. [Vercel environment variables](https://vercel.com/docs/environment-variables)

### 4. Deploy and verify

Click **Deploy** in Vercel, or install the CLI and run these commands from the repository root:

```bash
npm install --global vercel
vercel login
vercel
```

The first CLI deployment creates a Preview deployment. After adding the Production environment variables, deploy to production with:

```bash
vercel --prod
```

Check `https://<your-project>.vercel.app/health`, then create an account and chat. Refresh the chat and sign in again to confirm messages persist in Atlas. If the function times out, review the Vercel function logs and the 300-second `maxDuration` setting in `vercel.json`; Vercel may enforce a lower limit depending on plan/configuration. [Function duration limits](https://vercel.com/docs/functions/configuring-functions/duration)

## Deployment notes

- The `/api/stream` endpoint uses FastAPI `StreamingResponse` to send completed phase updates.
- The upload UI caps files at 4 MB to stay under Vercel's request-body limits.
- Keep the Vercel function region close to your Atlas cluster when possible; a new Vercel project defaults to `iad1` (Washington, D.C.).
- MongoDB collections and indexes are initialized automatically. The database connection string is read only by the backend.
