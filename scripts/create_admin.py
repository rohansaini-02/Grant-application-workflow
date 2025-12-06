import os, sys, django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User

# Create test admin
u = User.objects.create_user('testadmin', 'testadmin@test.com', 'demoPass123')
u.role = 'ADMIN'
u.is_staff = True
u.first_name = 'Test'
u.last_name = 'Admin'
u.save()
print('Created: testadmin / demoPass123')
