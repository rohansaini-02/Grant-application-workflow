#!/usr/bin/env python
"""Reset demo user passwords."""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User

def reset_passwords():
    users = ['admin', 'reviewer1', 'reviewer2', 'reviewer3', 'applicant1', 'applicant2', 'applicant3']
    for username in users:
        try:
            user = User.objects.get(username=username)
            user.set_password('demoPass123')
            user.save()
            print(f"✓ Reset password for {username}")
        except User.DoesNotExist:
            print(f"✗ User {username} not found")

if __name__ == '__main__':
    reset_passwords()
    print("\nAll passwords reset to: demoPass123")
