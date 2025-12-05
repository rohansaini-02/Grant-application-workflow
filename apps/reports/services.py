"""
Services for report generation, exports, and analytics.
"""

import csv
import os
import zipfile
from io import BytesIO, StringIO
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from apps.applications.models import Application
from apps.reviews.models import Review, ReviewAssignment
from apps.reviews.services import ScoringService
from .models import Export


class CSVExportService:
    """Service for CSV export generation."""
    
    @staticmethod
    def export_applications(applications, created_by):
        """
        Export applications to CSV.
        
        Args:
            applications: QuerySet of applications
            created_by: User creating the export
        
        Returns:
            Export instance
        """
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Title', 'Applicant', 'Status', 'Requested Amount',
            'Created At', 'Submitted At', 'Deadline', 'Mean Score', 'Review Count'
        ])
        
        # Write data
        for app in applications:
            stats = ScoringService.calculate_application_statistics(app)
            
            writer.writerow([
                str(app.id),
                app.title,
                app.applicant.get_full_name() or app.applicant.username,
                app.get_status_display(),
                app.requested_amount,
                app.created_at.strftime('%Y-%m-%d %H:%M'),
                app.submitted_at.strftime('%Y-%m-%d %H:%M') if app.submitted_at else '',
                app.deadline.strftime('%Y-%m-%d') if app.deadline else '',
                f"{stats['mean_score']:.2f}" if stats['mean_score'] else '',
                stats['review_count']
            ])
        
        # Save to file
        filename = f"applications_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(settings.EXPORTS_DIR, filename)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        # Create export record
        return Export.create_export(
            export_type=Export.ExportType.CSV_SUMMARY,
            filename=filename,
            file_path=file_path,
            created_by=created_by
        )
    
    @staticmethod
    def export_reviews(reviews, created_by):
        """Export reviews to CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Application', 'Reviewer', 'Status', 'Overall Score',
            'Submitted At', 'Strengths', 'Weaknesses', 'Recommendation'
        ])
        
        for review in reviews:
            writer.writerow([
                review.assignment.application.title,
                review.assignment.reviewer.get_full_name(),
                review.get_status_display(),
                f"{review.overall_score:.2f}" if review.overall_score else '',
                review.submitted_at.strftime('%Y-%m-%d %H:%M') if review.submitted_at else '',
                review.strengths[:100],
                review.weaknesses[:100],
                review.recommendation[:100]
            ])
        
        filename = f"reviews_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(settings.EXPORTS_DIR, filename)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.write(output.getvalue())
        
        return Export.create_export(
            export_type=Export.ExportType.CSV_SUMMARY,
            filename=filename,
            file_path=file_path,
            created_by=created_by
        )


class PDFExportService:
    """Service for PDF generation."""
    
    @staticmethod
    def generate_feedback_packet(application, created_by):
        """
        Generate PDF feedback packet for an application.
        
        Args:
            application: Application instance
            created_by: User creating the export
        
        Returns:
            Export instance
        """
        # Create PDF
        filename = f"feedback_{application.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(settings.EXPORTS_DIR, filename)
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"<b>Feedback Packet: {application.title}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Application info
        info_text = f"""
        <b>Applicant:</b> {application.applicant.get_full_name()}<br/>
        <b>Status:</b> {application.get_status_display()}<br/>
        <b>Submitted:</b> {application.submitted_at.strftime('%Y-%m-%d') if application.submitted_at else 'N/A'}<br/>
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Reviews summary
        reviews = Review.objects.filter(
            assignment__application=application,
            status=Review.ReviewStatus.SUBMITTED
        )
        
        if reviews.exists():
            story.append(Paragraph("<b>Review Summary</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            # Statistics
            stats = ScoringService.calculate_application_statistics(application)
            stats_text = f"""
            <b>Number of Reviews:</b> {stats['review_count']}<br/>
            <b>Mean Score:</b> {stats['mean_score']:.2f if stats['mean_score'] else 'N/A'}<br/>
            <b>Score Range:</b> {stats['min_score']:.2f if stats['min_score'] else 'N/A'} - {stats['max_score']:.2f if stats['max_score'] else 'N/A'}<br/>
            <b>Standard Deviation:</b> {stats['std_dev']:.2f if stats['std_dev'] else 'N/A'}<br/>
            """
            story.append(Paragraph(stats_text, styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Individual reviews (anonymized)
            for i, review in enumerate(reviews, 1):
                story.append(Paragraph(f"<b>Review {i}</b>", styles['Heading3']))
                story.append(Paragraph(f"<b>Overall Score:</b> {review.overall_score:.2f if review.overall_score else 'N/A'}", styles['Normal']))
                story.append(Spacer(1, 6))
                
                if review.strengths:
                    story.append(Paragraph("<b>Strengths:</b>", styles['Normal']))
                    story.append(Paragraph(review.strengths, styles['Normal']))
                    story.append(Spacer(1, 6))
                
                if review.weaknesses:
                    story.append(Paragraph("<b>Weaknesses:</b>", styles['Normal']))
                    story.append(Paragraph(review.weaknesses, styles['Normal']))
                    story.append(Spacer(1, 6))
                
                if review.recommendation:
                    story.append(Paragraph("<b>Recommendation:</b>", styles['Normal']))
                    story.append(Paragraph(review.recommendation, styles['Normal']))
                    story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        return Export.create_export(
            export_type=Export.ExportType.FEEDBACK_PACKET,
            filename=filename,
            file_path=file_path,
            created_by=created_by
        )


class ZIPExportService:
    """Service for ZIP package generation."""
    
    @staticmethod
    def create_feedback_package(application, created_by):
        """
        Create comprehensive feedback package as ZIP.
        
        Args:
            application: Application instance
            created_by: User creating the export
        
        Returns:
            Export instance
        """
        filename = f"feedback_package_{application.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
        file_path = os.path.join(settings.EXPORTS_DIR, filename)
        
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add PDF feedback packet
            pdf_export = PDFExportService.generate_feedback_packet(application, created_by)
            zipf.write(pdf_export.file_path, os.path.basename(pdf_export.file_path))
            
            # Add CSV with review details
            reviews = Review.objects.filter(
                assignment__application=application,
                status=Review.ReviewStatus.SUBMITTED
            )
            
            csv_output = StringIO()
            csv_writer = csv.writer(csv_output)
            csv_writer.writerow(['Review #', 'Overall Score', 'Strengths', 'Weaknesses', 'Recommendation'])
            
            for i, review in enumerate(reviews, 1):
                csv_writer.writerow([
                    i,
                    f"{review.overall_score:.2f}" if review.overall_score else '',
                    review.strengths,
                    review.weaknesses,
                    review.recommendation
                ])
            
            zipf.writestr('reviews_detail.csv', csv_output.getvalue())
            
            # Add metadata file
            metadata = f"""
Application Feedback Package
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Application: {application.title}
Applicant: {application.applicant.get_full_name()}
Status: {application.get_status_display()}
Submitted: {application.submitted_at.strftime('%Y-%m-%d') if application.submitted_at else 'N/A'}

Number of Reviews: {reviews.count()}
            """
            zipf.writestr('README.txt', metadata)
        
        return Export.create_export(
            export_type=Export.ExportType.FEEDBACK_PACKET,
            filename=filename,
            file_path=file_path,
            created_by=created_by
        )


class AnalyticsService:
    """Service for analytics and statistics."""
    
    @staticmethod
    def calculate_cohens_kappa_placeholder(reviews):
        """
        Placeholder for Cohen's kappa inter-rater reliability calculation.
        
        This is a simplified placeholder. Full implementation would require
        pairwise comparison of all reviewers' scores across all criteria.
        
        Args:
            reviews: QuerySet of Review instances
        
        Returns:
            Dictionary with kappa statistics
        """
        # This is a placeholder with sample values
        # Real implementation would calculate actual Cohen's kappa
        
        if reviews.count() < 2:
            return {
                'kappa': None,
                'interpretation': 'Insufficient data (need at least 2 reviews)',
                'note': 'Placeholder implementation'
            }
        
        # Sample placeholder value
        # Real kappa ranges from -1 to 1, where:
        # < 0: Poor agreement
        # 0.01-0.20: Slight agreement
        # 0.21-0.40: Fair agreement
        # 0.41-0.60: Moderate agreement
        # 0.61-0.80: Substantial agreement
        # 0.81-1.00: Almost perfect agreement
        
        sample_kappa = 0.65  # Placeholder: "Substantial agreement"
        
        return {
            'kappa': sample_kappa,
            'interpretation': 'Substantial agreement',
            'note': 'This is a placeholder implementation. Full Cohen\'s kappa calculation requires pairwise reviewer comparison.',
            'sample_data': True
        }
    
    @staticmethod
    def generate_score_distribution(applications):
        """
        Generate score distribution data for visualization.
        
        Args:
            applications: QuerySet of applications
        
        Returns:
            Dictionary with distribution data
        """
        distribution = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }
        
        for app in applications:
            stats = ScoringService.calculate_application_statistics(app)
            if stats['mean_score'] is not None:
                score = stats['mean_score']
                if score <= 20:
                    distribution['0-20'] += 1
                elif score <= 40:
                    distribution['21-40'] += 1
                elif score <= 60:
                    distribution['41-60'] += 1
                elif score <= 80:
                    distribution['61-80'] += 1
                else:
                    distribution['81-100'] += 1
        
        return distribution
