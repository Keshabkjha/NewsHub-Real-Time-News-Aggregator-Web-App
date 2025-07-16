from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from .models import (
    Article, Bookmark, TopicFollow, UserPreference,
    KeywordAlert, AlertClick
)
from .forms import PreferenceForm
from collections import Counter
from aggregator.models import Bookmark
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'aggregator/signup.html', {'form': form})


def home(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    articles = Article.objects.all()

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query)
        )

    if category:
        articles = articles.filter(category__iexact=category)

    articles = articles.order_by('-published_at')[:100]
    categories = Article.objects.values_list('category', flat=True).distinct()
    bookmarked_ids = []
    if request.user.is_authenticated:
        bookmarked_ids = Bookmark.objects.filter(user=request.user).values_list('article_id', flat=True)
    return render(request, 'aggregator/home.html', {
        'articles': articles,
        'query': query,
        'selected_category': category,
        'categories': categories,
        'bookmarked_ids': bookmarked_ids
    })


@login_required
def add_bookmark(request, article_id):
    article = Article.objects.get(id=article_id)
    Bookmark.objects.get_or_create(user=request.user, article=article)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_bookmark(request, article_id):
    article = Article.objects.get(id=article_id)
    Bookmark.objects.filter(user=request.user, article=article).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def view_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('article').order_by('-created_at')
    return render(request, 'aggregator/bookmarks.html', {'bookmarks': bookmarks})


@login_required
def recommendations(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('article')
    categories = [b.article.category for b in bookmarks]

    if not categories:
        recommended = Article.objects.order_by('-published_at')[:20]
    else:
        top_categories = [cat for cat, _ in Counter(categories).most_common(2)]
        recommended = Article.objects.filter(category__in=top_categories).exclude(
            id__in=[b.article.id for b in bookmarks]
        ).order_by('-published_at')[:20]

    return render(request, 'aggregator/recommendations.html', {'recommended': recommended})


@login_required
def preferences(request):
    pref, _ = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PreferenceForm(request.POST, instance=pref)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PreferenceForm(instance=pref)

    return render(request, 'aggregator/preferences.html', {'form': form})


@login_required
def manage_keywords(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '').strip().lower()
        if keyword:
            KeywordAlert.objects.get_or_create(user=request.user, keyword=keyword)
        return redirect('manage_keywords')

    keywords = KeywordAlert.objects.filter(user=request.user)
    return render(request, 'aggregator/manage_keywords.html', {'keywords': keywords})


@login_required
def delete_keyword(request, keyword):
    KeywordAlert.objects.filter(user=request.user, keyword=keyword).delete()
    return redirect('manage_keywords')


@login_required
def follow_topic(request, category):
    TopicFollow.objects.get_or_create(user=request.user, category=category)
    return redirect('home')


@login_required
def unfollow_topic(request, category):
    TopicFollow.objects.filter(user=request.user, category=category).delete()
    return redirect('home')


@login_required
def alert_click(request, article_id, keyword):
    article = Article.objects.get(id=article_id)
    AlertClick.objects.create(user=request.user, article=article, keyword=keyword)
    return redirect(article.url)


@login_required
def user_dashboard(request):
    bookmarks_count = Bookmark.objects.filter(user=request.user).count()
    alerts_count = KeywordAlert.objects.filter(user=request.user).count()
    clicks_count = AlertClick.objects.filter(user=request.user).count()

    most_clicked = (
        AlertClick.objects.filter(user=request.user)
        .values('keyword')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    return render(request, 'aggregator/user_dashboard.html', {
        'bookmarks_count': bookmarks_count,
        'alerts_count': alerts_count,
        'clicks_count': clicks_count,
        'most_clicked': most_clicked
    })
