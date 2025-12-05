# Grant Application Workflow - Cron Jobs Setup

## Overview

This project uses `django-crontab` for scheduled tasks including deadline reminders, overdue marking, and nightly reports.

## Cron Jobs Configured

The following cron jobs are defined in `config/settings.py`:

1. **Deadline Reminders** - Daily at 9 AM
   - Sends reminders 7/3/1 days before deadlines
   - Notifies reviewers of upcoming review due dates
   
2. **Overdue Marking** - Daily at 10 AM
   - Marks overdue review assignments
   - Notifies applicants of missed deadlines

3. **Nightly Reports** - Daily at midnight
   - Generates summary reports
   - Creates automated exports

## Setup Instructions

### Linux/Mac

1. Add cron jobs to system crontab:
```bash
python manage.py crontab add
```

2. View active cron jobs:
```bash
python manage.py crontab show
```

3. Remove cron jobs:
```bash
python manage.py crontab remove
```

### Windows

Since `django-crontab` uses Unix cron, Windows users have two options:

#### Option 1: Manual Execution (Development)

Run cron jobs manually:
```bash
python manage.py runcrons
```

#### Option 2: Windows Task Scheduler (Production)

1. Open Task Scheduler
2. Create a new task
3. Set trigger to run daily
4. Set action to run:
   ```
   Program: python
   Arguments: manage.py runcrons
   Start in: D:\SEMESTERS DATA😎\SEM 3\Django\Application Grant Workflow
   ```

## Testing Cron Jobs

Test individual cron functions:

```python
python manage.py shell

from apps.notifications.tasks import send_deadline_reminders, mark_overdue_items
from apps.reports.tasks import generate_nightly_reports

# Test deadline reminders
send_deadline_reminders()

# Test overdue marking
mark_overdue_items()

# Test nightly reports
generate_nightly_reports()
```

## Logs

Cron job output is logged to:
- `/tmp/cron_reminders.log` (Linux/Mac)
- `django.log` in project root

## Troubleshooting

**Cron jobs not running:**
- Verify cron jobs are added: `python manage.py crontab show`
- Check system cron is running: `sudo service cron status` (Linux)
- Review log files for errors

**Windows Task Scheduler issues:**
- Ensure Python path is correct
- Verify working directory is set
- Check task history in Task Scheduler

## Customization

To modify cron schedules, edit `CRONJOBS` in `config/settings.py`:

```python
CRONJOBS = [
    ('0 9 * * *', 'apps.notifications.tasks.send_deadline_reminders'),
    # Cron format: minute hour day month day_of_week
]
```

Cron format guide:
- `*` = every
- `*/5` = every 5
- `0 9 * * *` = 9:00 AM daily
- `0 */6 * * *` = every 6 hours
- `0 0 * * 0` = midnight every Sunday
