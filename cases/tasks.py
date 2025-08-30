"""
Celery tasks for charity management system
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_donation_confirmation_email(donation_id):
    """Send confirmation email after successful donation"""
    try:
        from donations.models import Donation

        donation = Donation.objects.get(id=donation_id)

        subject = f"Donation Confirmation - {donation.case.title}"
        message = f"""
        Dear {donation.donor.first_name},
        
        Thank you for your generous donation of NPR {donation.amount} to "{donation.case.title}".
        
        Your donation will make a real difference in someone's life.
        
        Transaction Details:
        - Amount: NPR {donation.amount}
        - Payment Reference: {donation.payment_reference}
        - Case: {donation.case.title}
        - Date: {donation.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        You can track the progress of this case at our website.
        
        Best regards,
        Charity Nepal Team
        """

        recipient_email = (
            donation.donor_email if donation.is_anonymous else donation.donor.email
        )

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )

        logger.info(f"Donation confirmation email sent for donation {donation_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send donation confirmation email: {str(e)}")
        return False


@shared_task
def send_case_approval_notification(case_id):
    """Send notification when case is approved"""
    try:
        from cases.models import CharityCase

        case = CharityCase.objects.get(id=case_id)

        subject = f"Your charity case has been approved - {case.title}"
        message = f"""
        Dear {case.created_by.first_name},
        
        Great news! Your charity case "{case.title}" has been approved and is now live on our platform.
        
        Case Details:
        - Title: {case.title}
        - Target Amount: NPR {case.target_amount}
        - Category: {case.get_category_display()}
        
        People can now discover and donate to your cause. We'll keep you updated on the progress.
        
        Best regards,
        Charity Nepal Team
        """

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [case.created_by.email],
            fail_silently=False,
        )

        logger.info(f"Case approval notification sent for case {case_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send case approval notification: {str(e)}")
        return False


@shared_task
def send_periodic_updates():
    """Send periodic updates to donors about cases they've supported"""
    try:
        from cases.models import CharityCase
        from donations.models import Donation

        # Get donors who have made donations in the last 6 months
        cutoff_date = timezone.now() - timedelta(days=180)
        recent_donors = User.objects.filter(
            donations__created_at__gte=cutoff_date, donations__status="completed"
        ).distinct()

        update_count = 0

        for donor in recent_donors:
            # Get cases they've donated to that are still active
            donated_cases = CharityCase.objects.filter(
                donations__donor=donor,
                donations__status="completed",
                verification_status="approved",
            ).distinct()

            if donated_cases.exists():
                # Prepare update email
                case_updates = []
                for case in donated_cases:
                    case_updates.append(
                        {
                            "title": case.title,
                            "progress": case.completion_percentage,
                            "collected": case.collected_amount,
                            "target": case.target_amount,
                            "status": "Completed" if case.is_completed else "Active",
                        }
                    )

                # Send email
                subject = "Update on the causes you've supported"
                message = f"""
                Dear {donor.first_name},
                
                Here's an update on the charity cases you've generously supported:
                
                """

                for update in case_updates:
                    message += f"""
                📋 {update['title']}
                   Progress: {update['progress']:.1f}%
                   Collected: NPR {update['collected']} of NPR {update['target']}
                   Status: {update['status']}
                
                """

                message += """
                Thank you for making a difference in people's lives!
                
                Best regards,
                Charity Nepal Team
                """

                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [donor.email],
                    fail_silently=True,
                )

                update_count += 1

        logger.info(f"Sent periodic updates to {update_count} donors")
        return update_count

    except Exception as e:
        logger.error(f"Failed to send periodic updates: {str(e)}")
        return 0


@shared_task
def update_case_collected_amounts():
    """Update collected amounts for all cases based on completed donations"""
    try:
        from cases.models import CharityCase
        from donations.models import Donation

        cases = CharityCase.objects.all()
        updated_count = 0

        for case in cases:
            # Calculate total from completed donations
            total_collected = (
                case.donations.filter(status="completed").aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            )

            if case.collected_amount != total_collected:
                case.collected_amount = total_collected
                case.save(update_fields=["collected_amount"])
                updated_count += 1

        logger.info(f"Updated collected amounts for {updated_count} cases")
        return updated_count

    except Exception as e:
        logger.error(f"Failed to update case collected amounts: {str(e)}")
        return 0


@shared_task
def generate_recommendation_report():
    """Generate and cache recommendation statistics"""
    try:
        from donations.models import Donation
        from recommendations.models import RecommendationHistory

        # Calculate recommendation effectiveness
        total_recommendations = RecommendationHistory.objects.count()
        clicked_recommendations = RecommendationHistory.objects.filter(
            clicked=True
        ).count()
        donated_from_recommendations = RecommendationHistory.objects.filter(
            donated=True
        ).count()

        click_through_rate = (
            (clicked_recommendations / total_recommendations * 100)
            if total_recommendations > 0
            else 0
        )
        conversion_rate = (
            (donated_from_recommendations / total_recommendations * 100)
            if total_recommendations > 0
            else 0
        )

        # Algorithm performance comparison
        algorithms = RecommendationHistory.objects.values("algorithm_used").annotate(
            total_recs=Count("id"),
            clicks=Count("id", filter={"clicked": True}),
            donations=Count("id", filter={"donated": True}),
        )

        report = {
            "total_recommendations": total_recommendations,
            "click_through_rate": click_through_rate,
            "conversion_rate": conversion_rate,
            "algorithm_performance": list(algorithms),
            "generated_at": timezone.now().isoformat(),
        }

        # Cache the report (you might want to store this in Redis or database)
        # For now, just log it
        logger.info(f"Recommendation report generated: {report}")

        return report

    except Exception as e:
        logger.error(f"Failed to generate recommendation report: {str(e)}")
        return None


@shared_task
def retrain_recommendation_models():
    """Retrain ML models with latest data"""
    try:
        import pandas as pd

        from cases.models import CharityCase
        from donations.models import Donation
        from recommendations.algorithms import HybridRecommendationSystem
        from recommendations.models import UserProfile

        # Prepare data
        cases_data = pd.DataFrame(
            list(
                CharityCase.objects.filter(verification_status="approved").values(
                    "id", "title", "description", "category", "tags"
                )
            )
        )

        donations_data = pd.DataFrame(
            list(
                Donation.objects.filter(status="completed")
                .select_related("case")
                .values("donor_id", "case_id", "case__category")
            )
        )
        donations_data.rename(columns={"case__category": "case_category"}, inplace=True)

        donor_profiles = pd.DataFrame(
            list(
                UserProfile.objects.select_related("user").values(
                    "user_id",
                    "avg_donation_amount",
                    "total_donations",
                    "total_donated",
                    "preferred_categories",
                    "age_range",
                    "income_range",
                )
            )
        )
        donor_profiles.rename(columns={"user_id": "id"}, inplace=True)

        if not cases_data.empty and not donations_data.empty:
            # Initialize and train hybrid system
            hybrid_system = HybridRecommendationSystem()
            hybrid_system.fit_all_models(donor_profiles, cases_data, donations_data)

            # Save models
            model_path = "/tmp/recommendation_models.pkl"
            hybrid_system.save_models(model_path)

            # Update model version in database
            from recommendations.models import RecommendationModel

            RecommendationModel.objects.filter(is_active=True).update(is_active=False)

            # Create new model version
            RecommendationModel.objects.create(
                name="hybrid_system",
                model_type="collaborative",
                version=f'v{timezone.now().strftime("%Y%m%d_%H%M")}',
                is_active=True,
                training_date=timezone.now(),
            )

            logger.info("Recommendation models retrained successfully")
            return True
        else:
            logger.warning("Insufficient data for model retraining")
            return False

    except Exception as e:
        logger.error(f"Failed to retrain recommendation models: {str(e)}")
        return False


@shared_task
def cleanup_old_search_queries():
    """Clean up old search queries to maintain database performance"""
    try:
        from recommendations.models import SearchQuery

        # Delete search queries older than 6 months
        cutoff_date = timezone.now() - timedelta(days=180)
        deleted_count = SearchQuery.objects.filter(created_at__lt=cutoff_date).delete()[
            0
        ]

        logger.info(f"Cleaned up {deleted_count} old search queries")
        return deleted_count

    except Exception as e:
        logger.error(f"Failed to cleanup search queries: {str(e)}")
        return 0


@shared_task
def send_case_milestone_notifications(case_id, milestone_percentage):
    """Send notifications when cases reach funding milestones"""
    try:
        from cases.models import CharityCase
        from donations.models import Donation

        case = CharityCase.objects.get(id=case_id)

        # Get all donors for this case
        donors = User.objects.filter(
            donations__case=case, donations__status="completed"
        ).distinct()

        subject = f"Great news! {case.title} reached {milestone_percentage}% funding"

        for donor in donors:
            message = f"""
            Dear {donor.first_name},
            
            Exciting update on "{case.title}" - a cause you generously supported!
            
            🎉 We've reached {milestone_percentage}% of our funding goal!
            
            Current Progress:
            - Raised: NPR {case.collected_amount:,.2f}
            - Goal: NPR {case.target_amount:,.2f}
            - Progress: {case.completion_percentage:.1f}%
            
            Your contribution is making this possible. Thank you for being part of this journey!
            
            Best regards,
            Charity Nepal Team
            """

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [donor.email],
                fail_silently=True,
            )

        logger.info(
            f"Milestone notifications sent for case {case_id} at {milestone_percentage}%"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send milestone notifications: {str(e)}")
        return False


@shared_task
def process_pending_donations():
    """Process donations that are stuck in pending status"""
    try:
        from donations.models import Donation
        from payments.models import PaymentIntent

        # Get donations pending for more than 1 hour
        cutoff_time = timezone.now() - timedelta(hours=1)
        pending_donations = Donation.objects.filter(
            status="pending", created_at__lt=cutoff_time
        )

        processed_count = 0

        for donation in pending_donations:
            try:
                # Check payment intent status
                payment_intent = PaymentIntent.objects.get(donation=donation)

                if payment_intent.is_expired:
                    # Mark as failed if expired
                    donation.status = "failed"
                    donation.save()
                    processed_count += 1
                elif payment_intent.is_successful:
                    # Mark as completed if payment succeeded
                    donation.status = "completed"
                    donation.completed_at = timezone.now()
                    donation.save()

                    # Update case collected amount
                    case = donation.case
                    case.collected_amount += donation.amount
                    case.save()

                    # Send confirmation email
                    send_donation_confirmation_email.delay(donation.id)
                    processed_count += 1

            except PaymentIntent.DoesNotExist:
                # No payment intent found, mark as failed
                donation.status = "failed"
                donation.save()
                processed_count += 1

        logger.info(f"Processed {processed_count} pending donations")
        return processed_count

    except Exception as e:
        logger.error(f"Failed to process pending donations: {str(e)}")
        return 0
