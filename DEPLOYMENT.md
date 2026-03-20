# ClaimClear AI — Deployment Guide

## Prerequisites

| Requirement | Version | Check Command |
|------------|---------|---------------|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| OpenAI API key | — | Optional for demo mode |

---

## 1. Local Development

### Step-by-Step Setup

```bash
# 1. Clone the repository and switch to the correct branch
git clone https://github.com/annondeveloper/hackathon.git
cd hackathon
git checkout claude/python-version-oTxa2

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows (Command Prompt)
# venv\Scripts\Activate.ps1     # Windows (PowerShell)

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure API key via environment
cp .env.example .env
# Edit .env and set: OPENAI_API_KEY=sk-your-key-here

# 5. Run the application
streamlit run app.py
```

The app opens at **http://localhost:8501**.

### Quick Verification

1. The app loads with the ClaimClear AI header
2. Select a sample claim from the dropdown (e.g., "Denied Health — Out-of-Network")
3. Click "Generate Explanation"
4. In demo mode (no API key): a pre-built explanation appears instantly
5. With an API key: the 4-stage pipeline runs and shows real-time progress

### Configuration Options

| Setting | Where | Description |
|---------|-------|-------------|
| API Key | Sidebar password field | Entered at runtime, stays in memory only |
| API Key | `.env` file | Loaded on startup via `python-dotenv` |
| Model | Sidebar dropdown | `gpt-4o-mini` (default) or `gpt-4o` |
| Tone | Sidebar dropdown | Simple & Friendly, Professional, Technical |
| Reading Level | Sidebar dropdown | Basic, Intermediate, Advanced |
| Pipeline Details | Sidebar checkbox | Show/hide per-stage output |

---

## 2. Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py pipeline.py policy_store.py sample_data.py ./
COPY .env.example .env.example

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

### Build & Run

```bash
# Build the image
docker build -t claimclear-ai .

# Run with API key
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-your-key claimclear-ai

# Run in demo mode (no key)
docker run -p 8501:8501 claimclear-ai
```

Access at **http://localhost:8501**.

---

## 3. Streamlit Community Cloud (Free)

The fastest way to deploy publicly:

1. Push code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and select your repository
4. Set the main file to `app.py`
5. In **Advanced settings > Secrets**, add:
   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   ```
6. Click "Deploy" — live in ~2 minutes

### Streamlit Secrets Access

The app reads the API key from the sidebar input first, then falls back to
the environment variable. On Streamlit Cloud, secrets are injected as
environment variables automatically.

---

## 4. Cloud Platform Deployment

### Option A: Railway (Git-push deploy)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway add --plugin python
railway variables set OPENAI_API_KEY=sk-your-key
railway up
```

### Option B: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Initialize and deploy
fly launch --name claimclear-ai
fly secrets set OPENAI_API_KEY=sk-your-key
fly deploy
```

### Option C: AWS (ECS / Fargate)

```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker build -t claimclear-ai .
docker tag claimclear-ai:latest $ECR_URI/claimclear-ai:latest
docker push $ECR_URI/claimclear-ai:latest

# Deploy via ECS task definition (see AWS docs for full setup)
```

### Cost Comparison

| Platform | Free Tier | Paid Estimate |
|----------|-----------|---------------|
| Streamlit Cloud | Yes (public apps) | — |
| Railway | $5 free credit/month | ~$5/month |
| Fly.io | 3 shared VMs free | ~$3/month |
| AWS ECS/Fargate | 12-month free tier | ~$15/month |

---

## 5. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | — | OpenAI API key. Can also be entered in the UI sidebar. |

No other environment variables are needed. All configuration is done through
the Streamlit sidebar at runtime.

---

## 6. Health Checks

### Local

```bash
# Check if Streamlit is running
curl -sf http://localhost:8501/_stcore/health && echo "OK" || echo "DOWN"
```

### Docker

The Dockerfile includes a built-in health check that runs every 30 seconds.

### Full Pipeline Test

1. Open the app in a browser
2. Select any sample claim
3. Enter your API key in the sidebar
4. Click "Generate Explanation"
5. Verify all 4 quality scores appear
6. Check "Show pipeline details" to confirm all stages completed

---

## 7. Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` in your venv |
| `openai.AuthenticationError` | Check your API key is valid and has credits |
| `openai.RateLimitError` | Wait 60 seconds or upgrade your OpenAI plan |
| Port 8501 in use | Run `streamlit run app.py --server.port=8502` |
| Blank page in browser | Clear browser cache or try incognito mode |
| Docker build fails | Ensure Docker is running and you have internet access |
| Demo mode shows instead of live | Check API key is entered (not just the env var) |

---

## 8. Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | 1.41.0 | Web UI framework |
| `openai` | ≥1.50.0 | OpenAI API client (chat completions, JSON mode) |
| `python-dotenv` | ≥1.0.0 | Load `.env` file for API key |

All dependencies are pure Python — no system-level packages or compilers
needed.
