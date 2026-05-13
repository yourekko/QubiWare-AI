# Deploy QubiWare AI (Streamlit Community Cloud)

## What you need

1. **GitHub account** (free).
2. **This repo pushed to GitHub** as a **public** repository (Community Cloud free tier).
3. **Optional:** `GEMINI_API_KEY` and/or `OPENAI_API_KEY` for live CoPilot (otherwise the rule-based engine runs).

## One-time: push code to GitHub

From the project folder (replace `YOUR_USER` / `YOUR_REPO`):

```bash
cd /path/to/QubiWare-AI
git init
git add app.py requirements.txt runtime.txt utils/ data/ .gitignore .env.example DEPLOY.md
git commit -m "Initial commit: QubiWare AI Streamlit app"
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

Do **not** commit `venv/`, `.env`, or `.streamlit/secrets.toml` (they are in `.gitignore`).

## Deploy on Streamlit Community Cloud

1. Open **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
2. **New app** → pick your GitHub repo, branch `main`, main file **`app.py`**.
3. **Advanced settings** → Python version should match **`runtime.txt`** (`python-3.11.8`).
4. Click **Deploy**.

## API keys (Secrets)

In the Cloud app: **Settings (gear) → Secrets**, paste:

```toml
GEMINI_API_KEY = "your-key-here"
# optional:
# OPENAI_API_KEY = "your-key-here"
```

Save and **Reboot** the app. The app reads secrets into `os.environ` after `st.set_page_config` (see `app.py`).

## Checklist before demo

- [ ] `data/*.csv` files are **committed** (the app loads from `data/`).
- [ ] Open the live URL after cold start (~30–60s first load).
- [ ] Test **AI CoPilot** after adding secrets (or accept rule-based fallback).

## Troubleshooting

| Issue | Fix |
|--------|-----|
| `ModuleNotFoundError` | Add missing package to `requirements.txt` and push. |
| Build fails on Python version | Change `runtime.txt` to another supported 3.11.x line from Streamlit docs. |
| Blank / file not found for CSV | Ensure `data/` is in the repo and paths are correct. |

## Private repo or SLA

Streamlit Community Cloud **public** repos are free; **private** repos need a paid plan. For production SLAs, consider Streamlit in Snowflake, paid Streamlit Cloud, Render, or a small VPS.
