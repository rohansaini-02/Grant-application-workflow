# Quick Start Guide

## Prerequisites Check
- ✅ Python 3.10+ installed
- ✅ PostgreSQL 12+ installed and running
- ✅ Git installed (optional)

## 5-Minute Setup

### 1. Create PostgreSQL Database (2 minutes)

**Windows PowerShell:**
```powershell
psql -U postgres
CREATE USER grant_user WITH PASSWORD 'demoPass123';
CREATE DATABASE grant_db OWNER grant_user;
GRANT ALL PRIVILEGES ON DATABASE grant_db TO grant_user;
\q
```

**Linux/Mac:**
```bash
sudo -u postgres createuser grant_user
sudo -u postgres createdb grant_db --owner=grant_user
sudo -u postgres psql -c "ALTER USER grant_user WITH PASSWORD 'demoPass123';"
```

### 2. Setup Python Environment (1 minute)

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure & Initialize (1 minute)

```bash
# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Run migrations
python manage.py migrate

# Seed demo data
python scripts/seed_demo.py
```

### 4. Start Server (30 seconds)

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## Demo Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | demoPass123 |
| Reviewer | reviewer1 | demoPass123 |
| Applicant | applicant1 | demoPass123 |

## Next Steps

1. **Explore Admin Panel**: http://localhost:8000/admin
2. **View Applications**: Login as applicant1
3. **Review Interface**: Login as reviewer1
4. **Analytics Dashboard**: Login as admin

## Troubleshooting

**Database connection error:**
- Verify PostgreSQL is running
- Check DATABASE_URL in .env file
- Ensure grant_user has correct permissions

**Import errors:**
- Activate virtual environment
- Run `pip install -r requirements.txt` again

**Migration errors:**
- Delete db (if test environment)
- Run `python manage.py migrate` again

## Development Workflow

```bash
# Make model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
pytest

# Run cron jobs manually
python manage.py runcrons
```

For full documentation, see [README.md](README.md)
