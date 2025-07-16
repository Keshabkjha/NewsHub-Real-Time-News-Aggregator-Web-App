from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Article, Bookmark
from django.urls import reverse

class ArticleModelTest(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Test Article",
            url="https://example.com",
            summary="Test Summary"
        )

    def test_article_creation(self):
        self.assertEqual(self.article.title, "Test Article")
        self.assertEqual(self.article.url, "https://example.com")
        self.assertEqual(self.article.summary, "Test Summary")

class BookmarkModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.article = Article.objects.create(
            title="Test Article",
            url="https://example.com",
            summary="Test Summary"
        )
        self.bookmark = Bookmark.objects.create(user=self.user, article=self.article)

    def test_bookmark_creation(self):
        self.assertEqual(self.bookmark.user.username, 'testuser')
        self.assertEqual(self.bookmark.article.title, "Test Article")

# class KeywordPreferenceModelTest(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='testpass')
#         self.keyword = KeywordPreference.objects.create(user=self.user, keyword="Django")

#     def test_keyword_creation(self):
#         self.assertEqual(self.keyword.keyword, "Django")
#         self.assertEqual(self.keyword.user.username, 'testuser')

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.article = Article.objects.create(
            title="Test Article",
            url="https://newshub.render.com",
            summary="Test Summary"
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Article")

    def test_signup_view(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_bookmark_view_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('bookmarks'))
        self.assertEqual(response.status_code, 200)

    def test_bookmark_view_unauthenticated(self):
        response = self.client.get(reverse('bookmarks'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
