import requests
from django.core.management.base import BaseCommand
from aggregator.models import Article
from datetime import datetime
from newspaper import Article as NewsArticle
from transformers import pipeline
from django.contrib.auth.models import User
from webpush import send_user_notification
from django.utils import timezone

# NLP summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def classify_category(title, summary):
    text = f"{title} {summary}".lower()
    if any(kw in text for kw in ['election', 'government', 'president']):
        return 'Politics'
    elif any(kw in text for kw in ['football', 'nba', 'cricket']):
        return 'Sports'
    elif any(kw in text for kw in ['ai', 'technology', 'tech', 'startup']):
        return 'Tech'
    elif any(kw in text for kw in ['market', 'stocks', 'economy']):
        return 'Business'
    else:
        return 'General'

def is_breaking_news(title, summary):
    keywords = ['breaking', 'alert', 'emergency', 'just in', 'exclusive']
    text = f"{title} {summary}".lower()
    return any(k in text for k in keywords)

class Command(BaseCommand):
    help = 'Fetch news from NewsAPI and notify users of breaking news'

    def handle(self, *args, **kwargs):
        url = 'https://newsapi.org/v2/top-headlines?country=us&pageSize=100&apiKey=YOUR_NEWSAPI_KEY'
        response = requests.get(url)
        data = response.json()

        if 'articles' not in data:
            self.stderr.write("❌ Failed to fetch articles")
            return

        sent_notifications = set()

        for item in data['articles']:
            try:
                news_article = NewsArticle(item['url'])
                news_article.download()
                news_article.parse()
                content = news_article.text[:5000]
                summary = summarizer(content, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            except Exception:
                content = item.get('content', '')
                summary = item.get('description', '')

            category = classify_category(item['title'], summary)

            article, created = Article.objects.get_or_create(
                title=item['title'],
                url=item['url'],
                source=item['source']['name'],
                published_at=item['publishedAt'],
                defaults={
                    'content': content,
                    'summary': summary,
                    'category': category,
                    'image_url': item.get('urlToImage')
                }
            )

            # Send push notification only for new articles
            if created and is_breaking_news(item['title'], summary):
                for user in User.objects.all():
                    if user in sent_notifications:
                        continue
                    try:
                        send_user_notification(
                            user=user,
                            payload={
                                "head": "🚨 Breaking News!",
                                "body": item['title'],
                                "url": item['url']
                            },
                            ttl=1000
                        )
                        sent_notifications.add(user)
                        self.stdout.write(self.style.SUCCESS(f"✅ Notified {user.username}"))
                    except Exception as e:
                        self.stderr.write(f"⚠️ Failed to notify {user.username}: {e}")

        self.stdout.write(self.style.SUCCESS("✅ Fetch completed."))
