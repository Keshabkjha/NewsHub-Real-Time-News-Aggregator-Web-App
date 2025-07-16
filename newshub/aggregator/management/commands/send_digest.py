from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from aggregator.models import (
    UserPreference, KeywordAlert, TopicFollow, Article, AlertClick
)
from django.contrib.auth.models import User
from django.db.models import Q

class Command(BaseCommand):
    help = "Send daily or weekly digest emails based on user preferences"

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            prefs = UserPreference.objects.filter(user=user).first()
            if not prefs or prefs.email_frequency == 'none':
                continue

            now = timezone.now()
            if prefs.email_frequency == 'daily' and now.hour != prefs.preferred_hour:
                continue
            if prefs.email_frequency == 'weekly' and (now.weekday() != 0 or now.hour != prefs.preferred_hour):
                continue

            categories = TopicFollow.objects.filter(user=user).values_list('category', flat=True)
            keyword_alerts = KeywordAlert.objects.filter(user=user).values_list('keyword', flat=True)

            articles = Article.objects.none()
            keyword_articles = Article.objects.none()

            if categories:
                articles = Article.objects.filter(
                    category__in=categories,
                    published_at__gte=now - timedelta(days=7)
                )

            if keyword_alerts:
                keyword_q = Q()
                for keyword in keyword_alerts:
                    keyword_q |= Q(title__icontains=keyword) | Q(summary__icontains=keyword)

                keyword_articles = Article.objects.filter(
                    keyword_q,
                    published_at__gte=now - timedelta(days=7)
                )

            if not articles and not keyword_articles:
                continue

            message = ""
            if articles.exists():
                message += "🗂️ Based on your followed categories:\n"
                for a in articles.order_by('-published_at')[:10]:
                    message += f"\n{a.title}\n{a.url}"

            if keyword_articles.exists():
                message += "\n\n🔔 Keyword Matches:\n"
                for a in keyword_articles.order_by('-published_at')[:10]:
                    keyword_hit = next((k for k in keyword_alerts if k.lower() in (a.title + a.summary).lower()), 'alert')
                    tracked_url = f"https://newshub.herokuapp.com/alert-click/{a.id}/{keyword_hit}/"
                    message += f"\n{a.title}\n{tracked_url}"

            send_mail(
                subject="📰 Your NewsHub Digest",
                message=message,
                from_email="developerkeshab@gmail.com",
                recipient_list=[user.email],
                fail_silently=True
            )

        self.stdout.write(self.style.SUCCESS("Email digests sent successfully."))
