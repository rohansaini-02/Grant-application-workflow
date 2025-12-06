# Railway Quick Start Guide

## 🚀 Quick Deployment Steps

### 1. Create Railway Project
- Go to [railway.app](https://railway.app)
- Click **"New Project"** → **"Deploy from GitHub repo"**
- Select your repository

### 2. Add PostgreSQL
- Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
- `DATABASE_URL` is automatically set ✅

### 3. Set Environment Variables
In your service → **"Variables"** tab, add:

```env
SECRET_KEY=<generate-using-command-below>
DEBUG=False
ALLOWED_HOSTS=*.railway.app
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

**Generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Deploy
- Railway auto-deploys on push to GitHub
- Or click **"Deploy"** manually

### 5. Run Migrations
In Railway Shell or Deploy Command:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 6. Create Admin User
```bash
python manage.py createsuperuser
```

### 7. Access Your App
- Railway provides URL: `https://your-app.up.railway.app`
- Admin: `https://your-app.up.railway.app/admin`

## ✅ What's Already Configured

- ✅ `Procfile` - Gunicorn server configuration
- ✅ `requirements.txt` - All dependencies including gunicorn, whitenoise
- ✅ `runtime.txt` - Python 3.11.0
- ✅ WhiteNoise - Enabled for static file serving
- ✅ Database - Uses `dj-database-url` (auto-detects Railway's DATABASE_URL)

## 📝 Important Notes

1. **Media Files**: Currently stored locally (ephemeral on Railway). Consider S3 for production.
2. **Cron Jobs**: Railway doesn't support cron. Use Railway scheduled tasks or external services.
3. **Updates**: Push to GitHub → Railway auto-deploys

## 🔗 Full Guide

See `RAILWAY_DEPLOYMENT.md` for detailed instructions and troubleshooting.

