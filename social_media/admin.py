from django.contrib import admin
from .models import SocialMediaPost, ChatMessage, ChatBot

admin.site.register(SocialMediaPost)
admin.site.register(ChatMessage)
admin.site.register(ChatBot)