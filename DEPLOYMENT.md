# Deployment Guide

## Your Setup: Railway PostgreSQL + Render Web Service

### Step 1: Get Railway PostgreSQL Connection URL

1. Go to your Railway project
2. Click on your PostgreSQL service
3. Go to **"Variables"** tab
4. Copy the **`DATABASE_URL`** value (starts with `postgresql://...`)

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com) → **Dashboard**
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `grant-workflow` |
| **Runtime** | `Docker` |
| **Dockerfile Path** | `./Dockerfile` |
| **Instance Type** | Free (or paid for better performance) |

5. Add **Environment Variables**:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DATABASE_URL` | **Paste from Railway** (postgresql://...) |

6. Click **"Create Web Service"**

### Step 3: Run Migrations

After deployment completes:
1. Go to your Render service → **"Shell"** tab
2. Run:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Step 4: Access Your App

Your app will be available at: `https://grant-workflow.onrender.com`

---

## Troubleshooting

### Database Connection Error
- Ensure Railway PostgreSQL is running
- Verify `DATABASE_URL` is correctly copied (no extra spaces)
- Check Railway allows external connections

### Static Files Not Loading
- WhiteNoise is enabled in settings
- `collectstatic` runs automatically in Dockerfile

### Build Fails
- Check Render logs for errors
- Ensure all dependencies in `requirements.txt`

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `False` for production |
| `ALLOWED_HOSTS` | Yes | `.onrender.com` |
| `DATABASE_URL` | Yes | Railway PostgreSQL URL |

