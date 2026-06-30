# Deployment Guide

This project should be deployed as two parts:

- Frontend on GitHub Pages
- Backend API on Render

## Backend: Render

This repository includes [render.yaml](../render.yaml), so Render can create the service from the repo directly.

Recommended settings:

- Service type: `Web Service`
- Runtime: `Python`
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Environment variables:

- `CORS_ORIGINS=https://liuweihua123.github.io`
- `ADMIN_TOKEN=<optional>`

After deploy, verify:

```text
https://<your-render-domain>/api/health
```

Expected response:

```json
{"status":"ok","service":"ASPathLens"}
```

## Frontend: GitHub Pages

The workflow file [.github/workflows/deploy-frontend.yml](../.github/workflows/deploy-frontend.yml) publishes the Vite app to GitHub Pages.

In your GitHub repository, set:

- `Settings`
- `Secrets and variables`
- `Actions`
- `Variables`

Create this repository variable:

```text
VITE_API_BASE_URL=https://<your-render-domain>
```

Then enable Pages:

- `Settings`
- `Pages`
- `Source: GitHub Actions`

Push to `master`, or manually run the `Deploy Frontend to GitHub Pages` workflow.

The frontend URL will be:

```text
https://liuweihua123.github.io/ASPathLens/
```

## Notes

- GitHub Pages cannot run the FastAPI backend.
- On Render free tier, the first request after idle may be slow.
- The backend loads data from `backend/data/raw`, so keep those files available in the deployed repo.
