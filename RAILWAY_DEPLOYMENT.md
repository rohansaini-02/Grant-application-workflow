# Railway Deployment Guide

This guide will walk you through deploying your Django Grant Application Workflow project on Railway.

## Prerequisites

- ✅ Code pushed to GitHub
- ✅ Railway account (sign up at [railway.app](https://railway.app))
- ✅ GitHub account connected to Railway

## Step-by-Step Deployment

### Step 1: Create a New Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"** button
3. Select **"Deploy from GitHub repo"**
4. Choose your repository from the list
5. Railway will automatically detect it's a Python/Django project

### Step 2: Add PostgreSQL Database

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway will automatically create a PostgreSQL database
4. The `DATABASE_URL` environment variable will be automatically set

### Step 3: Configure Environment Variables

Click on your service (the web service, not the database), then go to the **"Variables"** tab and add the following environment variables:

#### Required Variables

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `SECRET_KEY` | `[Generate a new secret key]` | Django secret key (see below) |
| `DEBUG` | `False` | Set to False for production |
| `ALLOWED_HOSTS` | `*.railway.app,your-custom-domain.com` | Your Railway domain (Railway will provide this) |
| `CSRF_COOKIE_SECURE` | `True` | Enable secure cookies for HTTPS |
| `SESSION_COOKIE_SECURE` | `True` | Enable secure session cookies |

#### Optional Variables (Recommended)

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Use SMTP for emails |
| `EMAIL_HOST` | `smtp.gmail.com` | Your email SMTP host |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_USE_TLS` | `True` | Enable TLS |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | Your email address |
| `EMAIL_HOST_PASSWORD` | `your-app-password` | Your email app password |
| `ADMIN_EMAIL` | `admin@yourdomain.com` | Admin contact email |
| `SITE_NAME` | `Grant Application Workflow` | Site name |

#### Generate SECRET_KEY

To generate a secure SECRET_KEY, run this command locally:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as the value for `SECRET_KEY` in Railway.

**Note:** The `DATABASE_URL` is automatically set by Railway when you add the PostgreSQL database. You don't need to set it manually.

### Step 4: Configure Build Settings

Railway should automatically detect your project, but verify these settings:

1. Go to your service → **"Settings"** tab
2. **Root Directory:** Leave empty (or set if your Django app is in a subdirectory)
3. **Build Command:** Railway will auto-detect, but you can set:
   ```
   pip install -r requirements.txt
   ```
4. **Start Command:** Railway will use your `Procfile`, which contains:
   ```
   web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

### Step 5: Deploy

1. Railway will automatically deploy when you push to your GitHub repository
2. You can also manually trigger a deployment by clicking **"Deploy"** in the Railway dashboard
3. Watch the build logs to ensure everything builds correctly

### Step 6: Run Database Migrations

After the first deployment, you need to run migrations:

1. In Railway dashboard, go to your service
2. Click on **"Deployments"** tab
3. Click on the latest deployment
4. Click **"View Logs"** or use the **"Shell"** button
5. Run these commands:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Alternatively, you can add these as a one-time command in Railway:

1. Go to your service → **"Settings"**
2. Add a **"Deploy Command"**:
   ```
   python manage.py migrate && python manage.py collectstatic --noinput
   ```

### Step 7: Create Superuser (Optional)

To create an admin user, use Railway's shell:

1. In Railway dashboard, click on your service
2. Click **"Shell"** or use the terminal
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow the prompts to create your admin account

Or use the provided script:
```bash
python scripts/create_admin.py
```

### Step 8: Access Your Application

1. Railway will provide you with a URL like: `https://your-app-name.up.railway.app`
2. Visit the URL to access your application
3. Access admin panel at: `https://your-app-name.up.railway.app/admin`

### Step 9: Set Up Custom Domain (Optional)

1. In Railway dashboard, go to your service → **"Settings"**
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"** or **"Custom Domain"**
4. Add your custom domain
5. Update `ALLOWED_HOSTS` to include your custom domain

## Post-Deployment Checklist

- [ ] Database migrations completed
- [ ] Static files collected (`collectstatic`)
- [ ] Environment variables set correctly
- [ ] Admin user created
- [ ] Application accessible via Railway URL
- [ ] HTTPS working (Railway provides this automatically)
- [ ] Email configuration tested (if using email features)

## Troubleshooting

### Build Fails

- Check build logs in Railway dashboard
- Ensure `requirements.txt` is correct
- Verify Python version in `runtime.txt` (currently set to `python-3.11.0`)

### Database Connection Issues

- Verify `DATABASE_URL` is set automatically by Railway
- Check PostgreSQL service is running
- Ensure migrations have been run

### Static Files Not Loading

- Verify `collectstatic` has been run
- Check WhiteNoise is enabled in `settings.py` (already configured)
- Ensure `STATIC_ROOT` is set correctly

### Application Crashes

- Check application logs in Railway dashboard
- Verify all environment variables are set
- Ensure `ALLOWED_HOSTS` includes your Railway domain
- Check that `SECRET_KEY` is set

### 500 Internal Server Error

- Check Railway logs for detailed error messages
- Verify database migrations are complete
- Ensure all required environment variables are set
- Check that media/static directories have proper permissions

## Monitoring and Logs

- **View Logs:** Railway dashboard → Your service → **"Deployments"** → Click deployment → **"View Logs"**
- **Real-time Logs:** Railway dashboard → Your service → **"Metrics"** tab
- **Application Logs:** Check Django logs (configured in `settings.py`)

## Updating Your Application

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```
3. Railway will automatically detect the push and redeploy
4. Monitor the deployment in Railway dashboard

## Important Notes

1. **Media Files:** Currently, media files are stored locally. For production, consider using:
   - Railway's volume storage (ephemeral)
   - External storage like AWS S3 (recommended for production)
   - See Django documentation for `django-storages`

2. **Cron Jobs:** The `django-crontab` package requires cron. Railway doesn't support cron directly. Consider:
   - Using Railway's scheduled tasks (cron jobs)
   - Using external cron services
   - Using Celery with a message broker (for more complex scheduling)

3. **Database Backups:** Railway provides automatic backups for PostgreSQL. Check your database service settings.

4. **Scaling:** Railway can automatically scale your application. Configure this in the service settings.

## Cost Considerations

- Railway offers a free tier with $5/month credit
- PostgreSQL database usage counts toward your usage
- Monitor your usage in the Railway dashboard

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

---

**Your application should now be live on Railway!** 🚀

