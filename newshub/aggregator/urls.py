from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('bookmarks/', views.view_bookmarks, name='view_bookmarks'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('preferences/', views.preferences, name='preferences'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('keywords/', views.manage_keywords, name='manage_keywords'),
    path('keywords/delete/<str:keyword>/', views.delete_keyword, name='delete_keyword'),
    path('bookmark/add/<int:article_id>/', views.add_bookmark, name='add_bookmark'),
    path('bookmark/remove/<int:article_id>/', views.remove_bookmark, name='remove_bookmark'),
    path('follow/<str:category>/', views.follow_topic, name='follow_topic'),
    path('unfollow/<str:category>/', views.unfollow_topic, name='unfollow_topic'),
    path('alert-click/<int:article_id>/<str:keyword>/', views.alert_click, name='alert_click'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
