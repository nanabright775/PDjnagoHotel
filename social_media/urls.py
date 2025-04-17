# urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('chat/', ChatBotViews.as_view(), name='chat'),
    path('telegram/webhook/', telegram_webhook, name='telegram_webhook'),
    path('send-message/', send_message_to_telegram, name='send_message_to_telegram'),
    path('post/', SocialMediaPostCreateView.as_view(), name='post_create'),
    path('posts/', SocialMediaPostListView.as_view(), name='post_list'),
    path('post/delete/<int:pk>/', DeletePostFromPlatformsView.as_view(), name='post_delete_from_platforms'),
    path('post/<int:pk>/', SocialMediaPostDetailView.as_view(), name='post_detail'),
     path('post/retry/<int:pk>/', SocialMediaPostRetryView.as_view(), name='post_retry'),
]
