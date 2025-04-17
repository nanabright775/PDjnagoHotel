from django.db import models
from accountss.models import Custom_user
from multiselectfield import MultiSelectField

class SocialMediaPost(models.Model):
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('x', 'X'),
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
    )

    user = models.ForeignKey(Custom_user, on_delete=models.CASCADE)  # Use the custom User model
    platforms = MultiSelectField(choices=PLATFORM_CHOICES,default='telegram')
    message = models.TextField()
    image = models.ImageField(upload_to='media/social_media/', blank=True, null=True)
    post_date = models.DateTimeField(auto_now_add=True)
    posted = models.BooleanField(default=False)
    posted_by = models.CharField(max_length=100, blank=True, null=True)
    facebook_post_id = models.CharField(max_length=100, blank=True, null=True)
    instagram_post_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_message_id = models.CharField(max_length=100, blank=True, null=True)
    x_post_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.platform} post by {self.user.username} on {self.post_date}'


class ChatMessage(models.Model):
    user = models.ForeignKey(Custom_user, on_delete=models.CASCADE,blank=True,null=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message by {self.user.username} on {self.timestamp}'


    

class ChatBot(models.Model):
    user = models.ForeignKey(Custom_user, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Chat with {self.user.username} on {self.timestamp}'