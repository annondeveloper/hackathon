# ClaimClear AI — Deployment Guide

## Streamlit Prototype Deployment

### Local Development

```bash
# 1. Clone and enter project
cd hackathon

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here

# 5. Run
streamlit run app.py
# Opens at http://localhost:8501
```

### Streamlit Community Cloud (Free)

1. Push code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `OPENAI_API_KEY` in Streamlit secrets
5. Deploy — live in ~2 minutes

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t claimclear-streamlit .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... claimclear-streamlit
```

---

## Rust + React Production Deployment

### Prerequisites

- Rust 1.75+ (`rustup install stable`)
- Node.js 20+ (`nvm install 20`)
- OpenAI API key

### Local Development

**Backend:**
```bash
cd claimclear-pro/backend
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-your-key-here

cargo run
# Server starts at http://localhost:3001
```

**Frontend:**
```bash
cd claimclear-pro/frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Production Build

**Backend:**
```bash
cd claimclear-pro/backend
cargo build --release
# Binary at ./target/release/claimclear-backend
```

**Frontend:**
```bash
cd claimclear-pro/frontend
npm run build
# Static files at ./dist/
```

### Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: ./claimclear-pro/backend
    ports:
      - "3001:3001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RUST_LOG=info

  frontend:
    build: ./claimclear-pro/frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

**Backend Dockerfile:**
```dockerfile
# claimclear-pro/backend/Dockerfile
FROM rust:1.75 AS builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/claimclear-backend /usr/local/bin/
EXPOSE 3001
CMD ["claimclear-backend"]
```

**Frontend Dockerfile:**
```dockerfile
# claimclear-pro/frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Cloud Deployment Options

| Platform | Best For | Estimated Cost |
|----------|----------|----------------|
| **Fly.io** | Quick deploy, free tier | Free (small) |
| **Railway** | Git-push deploys | ~$5/mo |
| **AWS ECS** | Enterprise scale | ~$20/mo+ |
| **Vercel** (frontend) + **Fly** (backend) | Hybrid | Free-$10/mo |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `RUST_LOG` | No | Log level (default: `info`) |
| `PORT` | No | Server port (default: `3001`) |

---

## Health Checks

- **Backend**: `GET /api/health` returns `{"status": "ok"}`
- **Frontend**: Static file serving (any 200 response from `/`)
- **Full test**: `POST /api/explain` with sample payload

### Sample Health Check Script

```bash
#!/bin/bash
curl -sf http://localhost:3001/api/health || echo "Backend DOWN"
curl -sf http://localhost:80/ || echo "Frontend DOWN"
```
