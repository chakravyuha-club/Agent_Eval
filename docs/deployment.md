# AgentScore Deployment Guide

This guide covers deploying AgentScore into production environments using modern cloud platforms or container infrastructure.

---

## 1. Production Architecture Topology

- **Frontend:** Vercel / Cloudflare Pages / AWS Amplify
- **Backend API:** AWS ECS / GCP Cloud Run / Render / Railway / DigitalOcean
- **Background Worker:** Standalone worker service (e.g. Celery / Celery Beat or background runner)
- **Database:** Managed PostgreSQL 15+ (e.g., Supabase / AWS RDS / Neon / NeonDB)
- **Cache & Queue:** Managed Redis 7+ (e.g., Upstash / AWS ElastiCache / Redis Cloud)
- **Object Storage:** AWS S3 / Supabase Storage / Cloudflare R2

---

## 2. Environment Variables Checklist

Ensure the following environment variables are securely provisioned:

| Variable | Description | Example / Recommended |
|---|---|---|
| `ENVIRONMENT` | Environment type | `production` |
| `SECRET_KEY` | 64+ char cryptographic key | `openssl rand -hex 32` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis connection string | `rediss://default:token@host:6379/0` |
| `CORS_ORIGINS` | Permitted frontend origins | `https://agentscore.org,https://www.agentscore.org` |
| `STORAGE_PROVIDER` | Object storage provider | `s3` or `local` |
| `ENABLE_SSRF_PROTECTION` | Strict IP verification | `True` |

---

## 3. Deployment Steps

### Step 1: Database Migration & Seeding
```bash
cd backend
alembic upgrade head
python -m app.services.seed_data
```

### Step 2: Backend API Service
Launch FastAPI with Gunicorn + Uvicorn workers:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 3: Background Worker Service
```bash
python -m app.workers.evaluation_worker
```

### Step 4: Frontend Deployment
```bash
cd frontend
npm run build
npm run start
```
