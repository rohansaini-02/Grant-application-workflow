# Grant Application Workflow

A complete, production-ready Grant Application Workflow system built with Django, PostgreSQL, and server-rendered templates. Implements end-to-end grant application management from submission through review, decision, and feedback delivery.

## Features

- **Role-Based Access Control**: Applicant, Reviewer, and Admin roles with object-level permissions
- **State Machine**: 13-state workflow with validated transitions and audit logging
- **Blinded Review System**: Reviewers see anonymized applications with rubric-based scoring
- **Intelligent Assignment**: Expertise matching and load balancing for reviewer assignments
- **Conflict of Interest Management**: COI declaration and automatic reviewer removal
- **Version Control**: Full application version history with diff tracking
- **Document Management**: Secure file uploads with MIME validation and time-limited downloads
- **Notifications**: In-app and email notifications with editable templates
- **Automated Scheduling**: Deadline reminders (7/3/1 days) via django-crontab
- **Reports & Analytics**: CSV/PDF/ZIP exports, scoring statistics, Cohen's kappa placeholder
- **Accessibility**: WCAG AA compliant templates with semantic HTML and ARIA attributes
- **Comprehensive Admin**: Django Admin with pagination (50/page), filtering, search, and bulk actions

## Technology Stack

- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL (required)
- **Scheduling**: django-crontab (no Celery/Redis)
- **File Storage**: Local filesystem (documented S3 migration path)
- **PDF Generation**: ReportLab
- **Testing**: pytest-django

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Virtual environment tool (venv)

## PostgreSQL Setup

### Windows

1. Install PostgreSQL from https://www.postgresql.org/download/windows/

2. Open PowerShell and create database and user:

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE USER grant_user WITH PASSWORD 'demoPass123';
CREATE DATABASE grant_db OWNER grant_user;
GRANT ALL PRIVILEGES ON DATABASE grant_db TO grant_user;
\q
```

### Linux/Mac

```bash
# Create user
sudo -u postgres createuser grant_user

# Create database
sudo -u postgres createdb grant_db --owner=grant_user

# Set password
sudo -u postgres psql -c "ALTER USER grant_user WITH PASSWORD 'demoPass123';"
```

## Installation

### 1. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update with your PostgreSQL credentials:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://grant_user:demoPass123@localhost:5432/grant_db
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Seed Demo Data

```bash
python scripts/seed_demo.py
```

This creates:
- Admin user: `admin` / `demoPass123`
- 3 Reviewers: `reviewer1`, `reviewer2`, `reviewer3` / `demoPass123`
- 3 Applicants: `applicant1`, `applicant2`, `applicant3` / `demoPass123`
- Sample rubrics, applications, and reviews

### 6. Run Development Server

```bash
python manage.py runserver
```

Access the application at: http://localhost:8000
Access admin panel at: http://localhost:8000/admin

## Cron Jobs Setup

### Windows (Task Scheduler)

Since django-crontab uses Unix cron, on Windows you can:

**Option 1: Manual Testing**
```bash
python manage.py runcrons
```

**Option 2: Windows Task Scheduler**

Create scheduled tasks to run:
```bash
python manage.py runcrons
```

### Linux/Mac

Add cron jobs:

```bash
python manage.py crontab add
```

View active cron jobs:
```bash
python manage.py crontab show
```

Remove cron jobs:
```bash
python manage.py crontab remove
```

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=apps --cov-report=html
```

Run Django tests:

```bash
python manage.py test
```

## VS Code Integration

The project includes VS Code configuration:

- **Debug Django Server**: Press F5 to debug
- **Tasks**: Ctrl+Shift+B for quick tasks
  - Migrate
  - Make Migrations
  - Run Server
  - Seed Demo Data
  - Run Tests

## Project Structure

```
grant-workflow/
├── apps/
│   ├── users/              # User model, roles, permissions
│   ├── applications/       # Applications, versions, documents, state machine
│   ├── reviews/            # Reviews, rubrics, assignments, COI
│   ├── notifications/      # In-app and email notifications
│   └── reports/            # Analytics, exports, PDF generation
├── config/                 # Django settings and configuration
├── templates/              # Django templates
├── static/                 # CSS, JavaScript, images
├── media/                  # User-uploaded files
├── exports/                # Generated exports
├── scripts/                # Utility scripts
│   └── seed_demo.py       # Demo data seeding
├── .vscode/                # VS Code configuration
├── manage.py
├── requirements.txt
└── README.md
```

## User Roles

### Applicant
- Create and submit applications
- Upload documents
- View application status and feedback
- Receive notifications

### Reviewer
- View assigned applications (blinded)
- Score applications using rubrics
- Submit reviews with comments
- Declare conflicts of interest

### Admin
- Manage all applications
- Assign reviewers (with load balancing suggestions)
- View analytics and reports
- Generate exports (CSV, PDF, ZIP)
- Manage rubrics and criteria
- Configure email templates

## Application States

1. **DRAFT** → Applicant editing
2. **SUBMITTED** → Awaiting triage
3. **IN_TRIAGE** → Admin review
4. **ASSIGNED** → Reviewers assigned
5. **UNDER_REVIEW** → Reviews in progress
6. **REVIEWED** → Reviews complete
7. **DECISION_PENDING** → Admin decision
8. **APPROVED** / **REJECTED** → Final decision
9. **REVISION_REQUESTED** → Applicant revisions needed
10. **UNDER_REVISION** → Applicant editing
11. **APPEAL_PENDING** / **APPEAL_REVIEWED** → Appeal process
12. **ARCHIVED** → Closed

## Key Features

### State Machine
- Validates all state transitions
- Automatic audit log creation
- Prevents invalid transitions

### Reviewer Assignment
- Expertise matching using Jaccard similarity
- Load balancing (60% expertise, 40% load)
- COI detection and prevention
- Bulk assignment support

### Blinded Review
- PI and team information hidden by default
- Admin can temporarily unblind
- Reviewer sees only research content

### Scoring System
- Weighted rubric criteria
- Per-criterion scoring (0-10)
- Automatic overall score calculation
- Statistical analysis (mean, stddev, variance)

### Exports
- CSV summaries of applications and reviews
- PDF feedback packets with anonymized comments
- ZIP packages with multiple files
- Time-limited download URLs (24 hours)

### Notifications
- In-app notification center
- Email notifications with templates
- Deadline reminders (7/3/1 days before)
- Overdue alerts

## Admin Features

### List Views (50 items/page)
- **Applications**: Filter by status, date, program; Search by title, applicant
- **Reviews**: Filter by status, score; Search by reviewer, application
- **Users**: Filter by role, status; Search by username, email
- **Audit Logs**: Filter by action type, date; Search by actor, details

### Bulk Actions
- State transitions
- Reviewer assignment/unassignment
- Export generation
- COI resolution

## Security

- CSRF protection enabled
- Input sanitization
- DRF throttling (100/hour anon, 1000/hour user)
- File upload validation (MIME type, size)
- Signed download URLs
- Object-level permissions
- Append-only audit logs

## Accessibility

- WCAG AA compliant color contrast
- Semantic HTML5 elements
- ARIA labels and roles
- Keyboard navigation support
- Focus indicators
- Screen reader compatible

## Known Limitations

1. **Cohen's Kappa**: Implemented as placeholder with sample values. Full inter-rater reliability calculation requires pairwise reviewer comparison across all criteria.

2. **Windows Cron**: django-crontab requires Unix cron. On Windows, use Task Scheduler or manual `runcrons` command.

3. **File Storage**: Uses local filesystem. For production, migrate to django-storages with S3 (configuration documented in settings.py).

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Generate strong `SECRET_KEY`
3. Configure allowed hosts
4. Set up HTTPS
5. Enable `CSRF_COOKIE_SECURE` and `SESSION_COOKIE_SECURE`
6. Configure production email backend
7. Set up static file serving (nginx/Apache)
8. Configure PostgreSQL connection pooling
9. Set up automated backups
10. Configure logging and monitoring

## Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- django-crontab: https://github.com/kraiz/django-crontab

## License

All rights reserved.

---

**Grant Application Workflow** - Built with Django, PostgreSQL, and ❤️
