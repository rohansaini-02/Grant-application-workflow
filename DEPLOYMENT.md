# Railway Deployment Guide (Docker)

## Prerequisites
- GitHub account with your code pushed
- Railway account (free tier available)

## 1. Quick Deploy to Railway

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Add Docker deployment configuration"
git push origin main
```

### Step 2: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway and select your repository
5. Railway will **auto-detect** your `Dockerfile` and use it for deployment

### Step 3: Add PostgreSQL Database
1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will create a PostgreSQL instance and provide `DATABASE_URL`

### Step 4: Set Environment Variables
Click on your service, go to **"Variables"** tab, and add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.railway.app,your-custom-domain.com` |
| `DATABASE_URL` | Auto-set from PostgreSQL service |
| `PORT` | `8000` (Railway sets this automatically) |

### Step 5: Deploy
Railway will auto-deploy when you push to GitHub. First deploy may take 5-10 minutes.

## 2. Run Migrations & Create Superuser

After deployment, open **Railway Console** (click on your service → "Shell"):

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Seed demo data
python scripts/seed_demo.py
```

## 3. Access Your App
Your app will be available at: `https://your-project-name.up.railway.app`

## Troubleshooting

### Build Fails
- Check Railway logs for specific errors
- Ensure all dependencies are in `requirements.txt`

### Static Files Not Loading
- Ensure WhiteNoise is in MIDDLEWARE
- Run `python manage.py collectstatic --noinput` (already in Dockerfile)

### Database Connection Error
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Django secret key |
| `DEBUG` | Yes | `False` | Debug mode |
| `ALLOWED_HOSTS` | Yes | - | Comma-separated hosts |
| `DATABASE_URL` | Yes | - | PostgreSQL URL |
| `EMAIL_HOST_USER` | No | - | SMTP email |
| `EMAIL_HOST_PASSWORD` | No | - | SMTP password |
