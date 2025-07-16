from django.db import models
from django.contrib.auth.models import User

class Article(models.Model):
    title = models.CharField(max_length=300)
    url = models.URLField()
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    content = models.TextField()
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=50)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.user.username} bookmarked {self.article.title}"


class TopicFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'category')

    def __str__(self):
        return f"{self.user.username} follows {self.category}"


class UserPreference(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('none', 'None'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    preferred_hour = models.IntegerField(default=8)  # 24-hr format

    def __str__(self):
        return f"{self.user.username}'s preferences"


class KeywordAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'keyword')

    def __str__(self):
        return f"{self.user.username} alerts on '{self.keyword}'"


class AlertClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=50)
    clicked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} clicked '{self.keyword}' at {self.clicked_at}"
