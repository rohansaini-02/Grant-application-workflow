# Deployment Guide

## Quick Deploy to Railway

1. **Push to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/grant-workflow.git
   git push -u origin main
   ```

2. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
   - Add PostgreSQL plugin
   - Set environment variables (copy from `.env.production`)
   - Deploy!

## Environment Variables Required

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | New secure key (use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | Your domain |
| `DATABASE_URL` | Auto-set by Railway |

## Post-Deployment Commands

Run these in Railway console:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python scripts/seed_demo.py  # Optional: seed demo data
```

## Other Platforms

### Heroku
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku run python manage.py migrate
```

### Render
- Use `render.yaml` or connect GitHub
- Add PostgreSQL database
- Set environment variables
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `gunicorn config.wsgi:application`
