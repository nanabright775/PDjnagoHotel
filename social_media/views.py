import re
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatBot
from .forms import ChatBotForm
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Custom_user, ChatMessage
from telegram import Bot
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import ChatMessage, Custom_user
from telegram import Bot
from room.models import *
from gym.models import *
from Hall.models import *
import re
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models import Count, Sum
from Spa.models import *
from config import BASE_URL,TELEGRAM_BOT_TOKEN
from django.views import View
import os
from dotenv import load_dotenv

load_dotenv()


gemini_api_key = os.getenv("GEMINI_API_KEY")

import google.generativeai as genai

# Configure the Gemini API key
genai.configure(api_key=f'{gemini_api_key}')



class ChatBotViews(LoginRequiredMixin, FormView, ListView):
    model = ChatBot
    form_class = ChatBotForm
    template_name = 'social_media/chat.html'
    success_url = reverse_lazy('chat')
    context_object_name = 'chats'

    def get_queryset(self):
        return ChatBot.objects.filter(user=self.request.user).order_by('timestamp')

    def form_valid(self, form):
        user_message = form.cleaned_data['message']
        response_text = self.get_gemini_response(user_message)
        
        # Save the chat in the database
        ChatBot.objects.create(
            user=self.request.user,
            message=user_message,
            response=response_text
        )
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"data": {"text": response_text}})
        return super().form_valid(form)

    def get_gemini_response(self, user_message):
        # Check for custom commands and pass results to Gemini
        data_to_send = self.handle_custom_commands(user_message)
        
        if data_to_send:  # If there is a custom command result, pass it to Gemini for response
            prompt = f"Here is the data: {data_to_send}. Could you summarize this information in a friendly and helpful tone that is meant for the Staff of of a hotel named ADAR so refer to them as ADAR Team and elaborate on the data? and if the data is empty  for example of its pending bookings just say there are no , and list the data where its suitable to list and use bold for names and values and forget this chats history and dont put your name at the end of your response "
        else:  # Otherwise, send the user's message to Gemini
            prompt = user_message

        # Generate a response using Gemini
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat()
        response = chat.send_message(prompt)
        
        response_content = response.text
        response_content = response_content.replace("\n", "<br>")
        formatted_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response_content)
        
        return formatted_response

    def handle_custom_commands(self, user_message):
        user_message_lower = user_message.lower()

        # Available room commands
        if any(keyword in user_message_lower for keyword in ["available rooms", "show me rooms", "rooms that are available"]):
            return self.get_available_rooms()

        # Pending bookings commands
        if any(keyword in user_message_lower for keyword in ["pending bookings", "show pending bookings"]):
            return self.get_pending_bookings()

        # Total bookings commands
        if any(keyword in user_message_lower for keyword in ["total bookings", "all bookings"]):
            return self.get_total_bookings()

        # Total revenue by room type commands
        if any(keyword in user_message_lower for keyword in ["total revenue by room type", "room revenue"]):
            return self.get_total_revenue_by_room_type()

        # Total revenue by hall type commands
        if any(keyword in user_message_lower for keyword in ["total revenue by hall type", "hall revenue"]):
            return self.get_total_revenue_by_hall_type()

        # Membership commands
        if any(keyword in user_message_lower for keyword in ["total number of memberships", "membership count", "membership statistics"]):
            return self.get_total_memberships()

        # Booking trends
        if any(keyword in user_message_lower for keyword in ["booking trends", "trends for bookings"]):
            return self.get_booking_trends()

        # Room booking trends
        if any(keyword in user_message_lower for keyword in ["room booking trends", "trends for room bookings"]):
            return self.get_room_booking_trends()

        # Hall booking trends
        if any(keyword in user_message_lower for keyword in ["hall booking trends", "trends for hall bookings"]):
            return self.get_hall_booking_trends()

        # Spa-related commands
        if any(keyword in user_message_lower for keyword in ["available spa services", "list spa services"]):
            return self.get_spa_services()

        if any(keyword in user_message_lower for keyword in ["available spa packages", "list spa packages"]):
            return self.get_spa_packages()

        if any(keyword in user_message_lower for keyword in ["pending spa bookings", "spa bookings pending"]):
            return self.get_pending_spa_bookings()

        return None

    # Existing methods for room, hall, and membership-related data
    def get_available_rooms(self):
        available_rooms = Room.objects.filter(room_status='vacant')
        room_data = ""
        for room in available_rooms:
            room_data += f"Room {room.room_number} - {room.room_type.name}. "
        return f"Available rooms: {room_data}"

    def get_pending_bookings(self):
        pending_bookings = Booking.objects.filter(status='pending')
        booking_data = ""
        for booking in pending_bookings:
            booking_data += f"Booking ID: {booking.id}, Room: {booking.room.room_number} ({booking.room.room_type.name}). "
        return f"Pending bookings: {booking_data}"

    def get_total_bookings(self):
        total_bookings = Booking.objects.count()
        return f"Total Bookings: {total_bookings}"

    def get_total_revenue_by_room_type(self):
        room_revenue = Room.objects.values('room_type__name').annotate(total_revenue=Sum('booking__total_amount'))
        room_data = ""
        for room in room_revenue:
            room_data += f"{room['room_type__name']}: ETB {room['total_revenue']}. "
        return f"Total Revenue by Room Type: {room_data}"

    def get_total_revenue_by_hall_type(self):
        hall_revenue = Hall.objects.values('hall_type__name').annotate(total_revenue=Sum('hall_booking__amount_due'))
        hall_data = ""
        for hall in hall_revenue:
            hall_data += f"{hall['hall_type__name']}: ETB {hall['total_revenue']}. "
        return f"Total Revenue by Hall Type: {hall_data}"

    def get_total_memberships(self):
        memberships = Membership.objects.values('plan__name').annotate(total_members=Count('id'))
        membership_data = ""
        for membership in memberships:
            membership_data += f"{membership['plan__name']}: {membership['total_members']} memberships. "
        return f"Total Memberships by Plan: {membership_data}"

    def get_booking_trends(self):
        one_month_ago = timezone.now() - timedelta(days=30)
        room_bookings = Booking.objects.filter(created_at__gte=one_month_ago).count()
        hall_bookings = Hall_Booking.objects.filter(created_at__gte=one_month_ago).count()
        return f"Booking Trends in the Last Month: Room Bookings: {room_bookings}, Hall Bookings: {hall_bookings}"

    def get_room_booking_trends(self):
        one_month_ago = timezone.now() - timedelta(days=30)
        room_bookings = Booking.objects.filter(created_at__gte=one_month_ago).values('created_at__date').annotate(count=Count('id'))
        booking_data = ""
        for booking in room_bookings:
            booking_data += f"{booking['created_at__date']}: {booking['count']} bookings. "
        return f"Room Booking Trends: {booking_data}"

    def get_hall_booking_trends(self):
        one_month_ago = timezone.now() - timedelta(days=30)
        hall_bookings = Hall_Booking.objects.filter(created_at__gte=one_month_ago).values('created_at__date').annotate(count=Count('id'))
        booking_data = ""
        for booking in hall_bookings:
            booking_data += f"{booking['created_at__date']}: {booking['count']} bookings. "
        return f"Hall Booking Trends: {booking_data}"

    # New methods for spa-related data
    def get_spa_services(self):
        services = SpaService.objects.all()
        service_data = ""
        for service in services:
            service_data += f"{service.name} - ETB {service.price}. "
        return f"Available Spa Services: {service_data}"

    def get_spa_packages(self):
        packages = SpaPackage.objects.all()
        package_data = ""
        for package in packages:
            package_data += f"{package.name} - ETB {package.price}. "
        return f"Available Spa Packages: {package_data}"

    def get_pending_spa_bookings(self):
        pending_spa_bookings = SpaBooking.objects.filter(status='pending')
        booking_data = ""
        for booking in pending_spa_bookings:
            service_or_package = booking.service.name if booking.service else booking.package.name
            booking_data += f"Spa Booking ID: {booking.id} - {service_or_package} for {booking.appointment_date}. "
        return f"Pending Spa Bookings: {booking_data}"



@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        if "message" in data:
            message = data["message"]
            user_id = message["from"]["id"]
            username = message["from"]["username"]
            text = message["text"]

            # Create or get the user
            user, created = Custom_user.objects.get_or_create(telegram_id=user_id, defaults={'username': username})

            # Save the message
            ChatMessage.objects.create(user=user, message=text, timestamp=timezone.now())

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "invalid request"}, status=400)


def send_message_to_telegram(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        message_text = request.POST.get("message")

        user = get_object_or_404(Custom_user, id=user_id)
        telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

        telegram_bot.send_message(chat_id=user.telegram_id, text=message_text)
        
        # Save the message in the ChatMessage model
        ChatMessage.objects.create(user=user, message=message_text, timestamp=timezone.now())

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "invalid request"}, status=400)


from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SocialMediaPost
from .forms import SocialMediaPostForm
import requests
from requests_oauthlib import OAuth1
import json
from tempfile import NamedTemporaryFile




# Functions to handle posting to various platforms

facebook_app_secret = f'{os.getenv("FACEBOOK_APP_SECRET")}'
facebook_app_id = f'{os.getenv("FACEBOOK_APP_ID")}'

meta_access_token = f'{os.getenv("META_ACCESS_TOKEN")}'


import requests

def post_to_facebook(message, media_path=None):
    access_token = meta_access_token
    print(f"Access Token: {access_token}")
    page_id = f'{os.getenv("FACEBOOK_PAGE_ID")}'
    api_version = 'v17.0'  

    if media_path:
        post_url = f'https://graph.facebook.com/{api_version}/{page_id}/photos'
        post_data = {'caption': message, 'access_token': access_token}
        files = {'source': open(media_path, 'rb')}
        response = requests.post(post_url, data=post_data, files=files)
    else:
        post_url = f'https://graph.facebook.com/{api_version}/{page_id}/feed'
        post_data = {'message': message, 'access_token': access_token}
        response = requests.post(post_url, data=post_data)

    # Detailed logging for debugging
    if response.status_code in (200, 201):
        post_id = response.json().get('id')
        print("Successfully posted to Facebook.")
        return post_id
    else:
        print(f"Failed to post to Facebook: {response.status_code}")
        print(f"Response content: {response.text}")
        return None







import requests
from urllib.parse import quote

from urllib.parse import quote

def post_to_instagram(message, image_path):
    instagram_access_token = meta_access_token
    instagram_account_id = f'{os.getenv("INSTAGRAM_ACCOUNT_ID")}'
    
    # Assuming image_path is something like "/media/social_media/"
    relative_image_path = image_path.split('media')[-1].replace('\\', '/').lstrip('/')
    
    # Construct the full image URL
    image_url = f'{BASE_URL.rstrip("/")}/media/media/social_media/{relative_image_path.split("/")[-1]}'
    image_url = quote(image_url, safe=':/')
    
    print(f"Constructed Image URL: {image_url}")
    
    # Instagram API calls
    media_url = f'https://graph.facebook.com/v12.0/{instagram_account_id}/media'
    data = {
        'image_url': image_url,
        'caption': message,
        'access_token': instagram_access_token
    }
    response = requests.post(media_url, data=data)
    
    if response.status_code != 200:
        print(f"Media Creation Response: {response.status_code} - {response.text}")
        return None

    creation_id = response.json().get('id')
    if not creation_id:
        return None

    # Now publish the media
    publish_url = f'https://graph.facebook.com/v12.0/{instagram_account_id}/media_publish'
    data = {
        'creation_id': creation_id,
        'access_token': instagram_access_token
    }
    response = requests.post(publish_url, data=data)

    if response.status_code == 200:
        return creation_id  # Return the media ID as the post ID
    else:
        print(f"Failed to publish media: {response.status_code} - {response.text}")
        return None








twitter_api_key = f'{os.getenv("TWITTER_API_KEY")}'
twitter_api_key_secret = f'{os.getenv("TWITTER_API_KEY_SECRET")}'
twitter_bearer_token = f'{os.getenv("TWITTER_BEARER_TOKEN")}'
twitter_access_token = f'{os.getenv("TWITTER_ACCESS_TOKEN")}'
twitter_access_token_secret = f'{os.getenv("TWITTER_ACCESS_TOKEN_SECRET")}'
twitter_client_id = f'{os.getenv("TWITTER_CLIENT_ID")}'
twitter_client_secret = f'{os.getenv("TWITTER_CLIENT_SECRET")}'






def post_to_x_v2(message, image_url=None):
    auth = OAuth1(twitter_api_key, twitter_api_key_secret, twitter_access_token, twitter_access_token_secret)
    media_id = None

    if image_url:
        response = requests.get(image_url)
        if response.status_code == 200:
            with NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            with open(tmp_file_path, 'rb') as image_file:
                files = {'media': image_file}
                upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
                response = requests.post(upload_url, auth=auth, files=files)
                if response.status_code == 200:
                    media_id = response.json().get('media_id_string')
                else:
                    return None

    tweet_data = {'text': message}
    if media_id:
        tweet_data['media'] = {'media_ids': [media_id]}

    post_url = 'https://api.twitter.com/2/tweets'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(post_url, auth=auth, json=tweet_data, headers=headers)

    if response.status_code in (200, 201):
        tweet_id = response.json().get('data', {}).get('id')  # Get the tweet ID
        print("Successfully posted to X.")
        return tweet_id
    else:
        print(f"Failed to post to X: {response.status_code} - {response.text}")
        return None








import requests
from urllib.parse import quote

import requests
from urllib.parse import quote

def post_to_telegram(message, relative_image_path=None):
    bot_token = TELEGRAM_BOT_TOKEN
    channel_id = '@adarhotel'
    
    image_url = None
    if relative_image_path:
        # Ensure relative_image_path does not contain the full URL
        if relative_image_path.startswith('http://') or relative_image_path.startswith('https://'):
            # Strip the base part of the URL if it accidentally contains it
            relative_image_path = relative_image_path.split('/media/')[-1]
            relative_image_path = f'/media/{relative_image_path}'
        
        # Construct the image URL
        image_url = f'{BASE_URL.rstrip("/")}{relative_image_path}'
        
        # Ensure the image URL is encoded
        image_url = quote(image_url, safe=':/')

    if image_url:
        # Send a photo with a caption using the constructed image URL
        base_url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
        data = {
            'chat_id': channel_id,
            'photo': image_url,
            'caption': message
        }
        response = requests.post(base_url, data=data)
    else:
        # Send a text message if no image
        base_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        data = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(base_url, data=data)

    if response.status_code == 200:
        message_id = response.json().get('result', {}).get('message_id')  # Get the message ID
        return message_id
    else:
        print(f"Failed to post to Telegram: {response.status_code} - {response.text}")
        return None


    




class SocialMediaPostCreateView(LoginRequiredMixin, CreateView):
    model = SocialMediaPost
    form_class = SocialMediaPostForm
    template_name = 'social_media/post_form.html'
    success_url = reverse_lazy('post_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        local_media_path = form.instance.image.path if form.instance.image else None
        image_url = self.request.build_absolute_uri(form.instance.image.url) if form.instance.image else None
        platforms = form.cleaned_data['platforms']
        success = True

        for platform in platforms:
            if platform == 'facebook':
                post_id = post_to_facebook(form.instance.message, local_media_path)
                if post_id:
                    form.instance.facebook_post_id = post_id  # Save Facebook post ID
                success &= bool(post_id)
            elif platform == 'x':
                post_id = post_to_x_v2(form.instance.message, image_url)
                if post_id:
                    form.instance.x_post_id = post_id  # Save X post ID
                success &= bool(post_id)
            elif platform == 'instagram':
                post_id = post_to_instagram(form.instance.message, local_media_path)
                if post_id:
                    form.instance.instagram_post_id = post_id  # Save Instagram post ID
                success &= bool(post_id)
            elif platform == 'telegram':
                post_id = post_to_telegram(form.instance.message, image_url)
                if post_id:
                    form.instance.telegram_message_id = post_id  # Save Telegram message ID
                success &= bool(post_id)

        if success:
            form.instance.posted = True
            form.instance.save()

        return response


class SocialMediaPostRetryView(LoginRequiredMixin, View):
    def post(self, request, pk):
        # Get the social media post
        post = get_object_or_404(SocialMediaPost, pk=pk)

        failed_platforms = []
        success_platforms = []

        # Track success/failure of each platform
        platform_success = {
            'facebook': post.facebook_post_id is not None,
            'x': post.x_post_id is not None,
            'instagram': post.instagram_post_id is not None,
            'telegram': post.telegram_message_id is not None
        }

        # Retry posting to platforms that failed
        if 'facebook' in post.platforms and not platform_success['facebook']:
            post_id = post_to_facebook(post.message, post.image.path if post.image else None)
            if post_id:
                post.facebook_post_id = post_id
                success_platforms.append('Facebook')
            else:
                failed_platforms.append('Facebook')

        if 'x' in post.platforms and not platform_success['x']:
            post_id = post_to_x_v2(post.message, request.build_absolute_uri(post.image.url) if post.image else None)
            if post_id:
                post.x_post_id = post_id
                success_platforms.append('X')
            else:
                failed_platforms.append('X')

        if 'instagram' in post.platforms and not platform_success['instagram']:
            post_id = post_to_instagram(post.message, post.image.path if post.image else None)
            if post_id:
                post.instagram_post_id = post_id
                success_platforms.append('Instagram')
            else:
                failed_platforms.append('Instagram')

        if 'telegram' in post.platforms and not platform_success['telegram']:
            post_id = post_to_telegram(post.message, request.build_absolute_uri(post.image.url) if post.image else None)
            if post_id:
                post.telegram_message_id = post_id
                success_platforms.append('Telegram')
            else:
                failed_platforms.append('Telegram')

        # Only update the posted flag if all retry attempts were successful
        if len(success_platforms) == len(post.platforms) - len(failed_platforms):
            post.posted = True
        else:
            post.posted = False
        
        post.save()

        # Set appropriate messages for success and failure
        if success_platforms:
            messages.success(request, f"Post successfully retried for: {', '.join(success_platforms)}.")
        if failed_platforms:
            messages.error(request, f"Post failed to retry for: {', '.join(failed_platforms)}.")

        # Redirect to the post list view
        return redirect(reverse_lazy('post_list'))



from django.views.generic import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import SocialMediaPost

class DeletePostFromPlatformsView(View):
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(SocialMediaPost, pk=pk)

        # Get selected platforms from the form data
        selected_platforms = [platform.lower() for platform in request.POST.getlist('platforms')]

        if not selected_platforms:
            messages.error(request, "You must select at least one platform to delete from.")
            return redirect('post_list')

        
        platforms = post.platforms if isinstance(post.platforms, list) else post.platforms.split(',')

        success = True

        # Loop through selected platforms and call the respective delete function
        for platform in selected_platforms:
            if platform == 'facebook':
                success &= delete_from_facebook(post)
            elif platform == 'x':
                success &= delete_from_x(post)
            elif platform == 'telegram':
                success &= delete_from_telegram(post)
            elif platform == 'instagram':
                pass  

        if success:
            # Remove the selected platforms from the post's platforms list
            remaining_platforms = [p for p in platforms if p not in selected_platforms]
            post.platforms = remaining_platforms

            # If no platforms remain, mark the post as not posted
            if not remaining_platforms:
                post.posted = False
                messages.success(request, 'Post has been deleted from all selected platforms and is now marked as not posted.')
            else:
                messages.success(request, 'Post has been deleted from the selected platforms.')

            post.save()
        else:
            messages.error(request, 'Failed to delete the post from some platforms.')

        return redirect('post_list')



def delete_from_facebook(post):
    facebook_post_id = post.facebook_post_id
    access_token = meta_access_token

    if not facebook_post_id:
        return False

    url = f'https://graph.facebook.com/v17.0/{facebook_post_id}'
    params = {'access_token': access_token}

    response = requests.delete(url, params=params)

    if response.status_code == 200:
        # Keep the facebook_post_id, just return success
        return True
    else:
        print(f"Failed to delete Facebook post: {response.text}")
        return False



def delete_from_x(post):
    x_post_id = post.x_post_id

    if not x_post_id:
        return False

    api_key = twitter_api_key
    api_secret_key = twitter_api_key_secret
    access_token = twitter_access_token
    access_token_secret = twitter_access_token_secret

    oauth = OAuth1(api_key, api_secret_key, access_token, access_token_secret)
    url = f'https://api.twitter.com/2/tweets/{x_post_id}'

    response = requests.delete(url, auth=oauth)

    if response.status_code == 200:
        # Keep the x_post_id, just return success
        return True
    else:
        print(f"Failed to delete tweet on X: {response.text}")
        return False



def delete_from_instagram(post):
    instagram_post_id = post.instagram_post_id
    access_token = meta_access_token

    if not instagram_post_id:
        print("Instagram post ID is missing.")
        return False

    url = f'https://graph.facebook.com/v17.0/{instagram_post_id}'
    params = {'access_token': access_token}

    response = requests.delete(url, params=params)

    if response.status_code == 200:
        # Successfully deleted the post
        return True
    else:
        error_info = response.json().get('error', {})
        error_message = error_info.get('message', 'Unknown error')
        error_code = error_info.get('code', 'Unknown code')
        error_subcode = error_info.get('error_subcode', 'Unknown subcode')
        print(f"Failed to delete Instagram post: {error_message} (Code: {error_code}, Subcode: {error_subcode})")
        
        # Handling specific errors
        if error_code == 100 and error_subcode == 33:
            print("The post does not exist, or the action is not supported.")
        
        return False









def delete_from_telegram(post):
    telegram_message_id = post.telegram_message_id
    telegram_chat_id = '@adarhotel'
    telegram_token = TELEGRAM_BOT_TOKEN

    if not telegram_message_id:
        return False

    url = f'https://api.telegram.org/bot{telegram_token}/deleteMessage'
    params = {
        'chat_id': telegram_chat_id,
        'message_id': telegram_message_id
    }

    response = requests.post(url, params=params)

    if response.status_code == 200:
        # Keep the telegram_message_id, just return success
        return True
    else:
        print(f"Failed to delete Telegram message: {response.text}")
        return False






class SocialMediaPostListView(LoginRequiredMixin, ListView):
    model = SocialMediaPost
    template_name = 'social_media/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10  # Pagination: Show 10 posts per page

    def get_queryset(self):
        # Get the user's posts and filter them
        queryset = SocialMediaPost.objects.all().order_by('-post_date')
        
        # Get search query from the request
        search_query = self.request.GET.get('search', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(platform__icontains=search_query) |  # Search within the 'platform' field
                Q(message__icontains=search_query)  # Search within the 'message' field
            )
        return queryset


from django.views.generic import DetailView
from .models import SocialMediaPost

class SocialMediaPostDetailView(DetailView):
    model = SocialMediaPost
    template_name = 'social_media/post_detail.html'
    context_object_name = 'object'
