#!/usr/bin/env python
"""
Demo data seeding script for Grant Application Workflow.
Creates admin user, demo reviewers, applicants, rubrics, and sample applications.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.users.models import User
from apps.applications.models import Application, ApplicationVersion, DeadlineRule, ApplicationStatus
from apps.reviews.models import Rubric, Criterion, ReviewAssignment, Review
from apps.notifications.models import EmailTemplate
from apps.reviews.services import ReviewerAssignmentService


def create_users():
    """Create demo users."""
    print("Creating users...")
    
    # Admin user
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': User.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin.set_password('demoPass123')
        admin.save()
        print(f"  ✓ Created admin: {admin.username}")
    
    # Reviewers
    reviewers = []
    reviewer_data = [
        ('reviewer1', 'Alice', 'Smith', ['biology', 'genetics'], 'University A'),
        ('reviewer2', 'Bob', 'Johnson', ['chemistry', 'materials'], 'University B'),
        ('reviewer3', 'Carol', 'Williams', ['physics', 'astronomy'], 'University C'),
    ]
    
    for username, first, last, tags, org in reviewer_data:
        reviewer, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': first,
                'last_name': last,
                'role': User.Role.REVIEWER,
                'expertise_tags': tags,
                'organization': org,
            }
        )
        if created:
            reviewer.set_password('demoPass123')
            reviewer.save()
            print(f"  ✓ Created reviewer: {reviewer.username}")
        reviewers.append(reviewer)
    
    # Applicants
    applicants = []
    applicant_data = [
        ('applicant1', 'David', 'Brown', 'Research Institute X'),
        ('applicant2', 'Emma', 'Davis', 'University D'),
        ('applicant3', 'Frank', 'Miller', 'Lab Y'),
    ]
    
    for username, first, last, org in applicant_data:
        applicant, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': first,
                'last_name': last,
                'role': User.Role.APPLICANT,
                'organization': org,
            }
        )
        if created:
            applicant.set_password('demoPass123')
            applicant.save()
            print(f"  ✓ Created applicant: {applicant.username}")
        applicants.append(applicant)
    
    return admin, reviewers, applicants


def create_rubrics():
    """Create demo rubrics."""
    print("\nCreating rubrics...")
    
    rubric, created = Rubric.objects.get_or_create(
        name='Standard Research Rubric',
        defaults={
            'description': 'Standard rubric for research grant applications',
            'is_active': True,
        }
    )
    
    if created:
        print(f"  ✓ Created rubric: {rubric.name}")
        
        # Create criteria
        criteria_data = [
            ('Scientific Merit', 'Quality and significance of the research', 30, 0, 10, True, 1),
            ('Innovation', 'Novelty and originality of approach', 25, 0, 10, True, 2),
            ('Feasibility', 'Likelihood of successful completion', 20, 0, 10, True, 3),
            ('Impact', 'Potential impact on the field', 15, 0, 10, True, 4),
            ('Team Qualifications', 'Expertise and track record', 10, 0, 10, True, 5),
        ]
        
        for name, desc, weight, min_s, max_s, req, order in criteria_data:
            Criterion.objects.create(
                rubric=rubric,
                name=name,
                description=desc,
                weight=Decimal(str(weight)),
                min_score=min_s,
                max_score=max_s,
                is_required=req,
                order=order
            )
            print(f"    ✓ Created criterion: {name}")
    
    return rubric


def create_applications(applicants, rubric):
    """Create demo applications."""
    print("\nCreating applications...")
    
    applications = []
    app_data = [
        ('Novel Approach to Cancer Research', 'Biology Research 2024', 'biology', ApplicationStatus.UNDER_REVIEW, 250000),
        ('Advanced Materials for Energy Storage', 'Materials Science 2024', 'chemistry', ApplicationStatus.SUBMITTED, 180000),
        ('Exoplanet Detection Methods', 'Astronomy Grants 2024', 'physics', ApplicationStatus.DRAFT, 320000),
    ]
    
    for i, (title, program, tag, status, amount) in enumerate(app_data):
        applicant = applicants[i % len(applicants)]
        
        app, created = Application.objects.get_or_create(
            title=title,
            applicant=applicant,
            defaults={
                'call_program': program,
                'abstract': f'This is a demo application for {title}. The research aims to advance our understanding in the field.',
                'requested_amount': Decimal(str(amount)),
                'status': status,
                'submitted_at': timezone.now() - timedelta(days=10) if status != ApplicationStatus.DRAFT else None,
                'deadline': timezone.now() + timedelta(days=30),
                'tags': [tag, 'research'],
            }
        )
        
        if created:
            print(f"  ✓ Created application: {app.title}")
            
            # Create version
            ApplicationVersion.objects.create(
                application=app,
                version_number=1,
                data={
                    'title': title,
                    'abstract': app.abstract,
                    'methodology': 'Demo methodology',
                    'timeline': '12 months',
                },
                created_by=applicant,
                change_summary='Initial version'
            )
        
        applications.append(app)
    
    return applications


def create_reviews(applications, reviewers, rubric, admin):
    """Create demo review assignments and reviews."""
    print("\nCreating review assignments...")
    
    # Assign reviewers to first application
    app = applications[0]
    
    for i, reviewer in enumerate(reviewers[:2]):  # Assign 2 reviewers
        assignment, error = ReviewerAssignmentService.assign_reviewer(
            application=app,
            reviewer=reviewer,
            rubric=rubric,
            assigned_by=admin,
            due_days=14,
            is_blinded=True
        )
        
        if assignment:
            print(f"  ✓ Assigned {reviewer.username} to {app.title}")
            
            # Create a completed review for first reviewer
            if i == 0:
                review = Review.objects.create(
                    assignment=assignment,
                    scores={
                        str(c.id): 8 for c in rubric.criteria.all()
                    },
                    strengths='Strong scientific merit and innovative approach.',
                    weaknesses='Timeline could be more detailed.',
                    recommendation='Recommend for funding with minor revisions.',
                    status=Review.ReviewStatus.SUBMITTED,
                    submitted_at=timezone.now() - timedelta(days=2)
                )
                review.calculate_overall_score()
                review.save()
                
                assignment.status = ReviewAssignment.AssignmentStatus.COMPLETED
                assignment.save()
                
                print(f"    ✓ Created completed review")


def create_email_templates():
    """Create email templates."""
    print("\nCreating email templates...")
    
    templates = [
        ('Application Submitted', EmailTemplate.TemplateType.APPLICATION_SUBMITTED,
         'Application Submitted: {{application_title}}',
         'Dear {{applicant_name}},\n\nYour application "{{application_title}}" has been successfully submitted.\n\nThank you!'),
        
        ('Review Assigned', EmailTemplate.TemplateType.REVIEW_ASSIGNED,
         'New Review Assignment: {{application_title}}',
         'Dear {{reviewer_name}},\n\nYou have been assigned to review "{{application_title}}".\n\nDue date: {{due_date}}\n\nThank you!'),
        
        ('Review Reminder', EmailTemplate.TemplateType.REVIEW_REMINDER,
         'Review Reminder: {{application_title}}',
         'Dear {{reviewer_name}},\n\nThis is a reminder that your review for "{{application_title}}" is due on {{due_date}}.\n\nThank you!'),
    ]
    
    for name, template_type, subject, body in templates:
        template, created = EmailTemplate.objects.get_or_create(
            name=name,
            defaults={
                'template_type': template_type,
                'subject': subject,
                'body': body,
                'is_active': True,
            }
        )
        if created:
            print(f"  ✓ Created template: {name}")


def create_deadline_rules():
    """Create deadline rules."""
    print("\nCreating deadline rules...")
    
    rule, created = DeadlineRule.objects.get_or_create(
        name='Standard Review Deadline',
        defaults={
            'description': 'Standard deadline reminders for reviews',
            'reminder_days_before': [7, 3, 1],
            'auto_escalate': False,
            'applies_to_statuses': ['UNDER_REVIEW', 'ASSIGNED'],
            'is_active': True,
        }
    )
    
    if created:
        print(f"  ✓ Created deadline rule: {rule.name}")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Grant Application Workflow - Demo Data Seeding")
    print("=" * 60)
    
    admin, reviewers, applicants = create_users()
    rubric = create_rubrics()
    applications = create_applications(applicants, rubric)
    create_reviews(applications, reviewers, rubric, admin)
    create_email_templates()
    create_deadline_rules()
    
    print("\n" + "=" * 60)
    print("Demo data seeding completed successfully!")
    print("=" * 60)
    print("\nLogin credentials:")
    print("  Admin:      admin / demoPass123")
    print("  Reviewer 1: reviewer1 / demoPass123")
    print("  Reviewer 2: reviewer2 / demoPass123")
    print("  Reviewer 3: reviewer3 / demoPass123")
    print("  Applicant 1: applicant1 / demoPass123")
    print("  Applicant 2: applicant2 / demoPass123")
    print("  Applicant 3: applicant3 / demoPass123")
    print("\nAccess the application at: http://localhost:8000")
    print("Access the admin panel at: http://localhost:8000/admin")
    print("=" * 60)


if __name__ == '__main__':
    main()
