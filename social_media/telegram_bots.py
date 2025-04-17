import os
import sys

# Set the base directory path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the base directory to the Python path
sys.path.append(BASE_DIR)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')

# Import Django and setup
import django
django.setup()

from dotenv import load_dotenv

load_dotenv()
chapa_api_key = os.getenv('CHAPA_API_KEY')
paypal_client_id = os.getenv('PAYPAL_CLIENT_ID')
paypal_client_secret = os.getenv('PAYPAL_CLIENT_SECRET')


from datetime import datetime, date
import requests
import logging
import paypalrestsdk
from telegram import Update
from config import BASE_URL,TELEGRAM_BOT_TOKEN
from social_media.models import ChatMessage
import random,string
from asgiref.sync import sync_to_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from room.models import Room, Booking
from accountss.models import Custom_user

logger = logging.getLogger(__name__)

# Define states
EMAIL, MENU, PASSWORD,ROOM_SELECTION, CHECK_IN_DATE, CHECK_OUT_DATE, GUESTS, PAYMENT_METHOD, MY_BOOKINGS, PENDING_PAYMENT_PROCESS, PENDING_PAYMENTS, CANCEL_BOOKING, CHAT_STATE = range(13)

# Helper function to generate the main menu buttons
# Helper function to generate the main menu buttons
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_buttons():
    buttons = [
        [
            InlineKeyboardButton("Start Booking", callback_data='start_booking'),
            InlineKeyboardButton("My Bookings", callback_data='my_bookings')
        ],
        [
            InlineKeyboardButton("Pending Payments", callback_data='pending_payments'),
            InlineKeyboardButton("Cancel Booking", callback_data='cancel_booking')
        ],
        [
            InlineKeyboardButton("Message Staff", callback_data='start_chat'),
            InlineKeyboardButton("Restart", callback_data='restart')
        ]
    ]
    return InlineKeyboardMarkup(buttons)




# Command to start the conversation and ask for email
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Start", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome to Room Booking Bot! Click "Start" to begin.',
        reply_markup=reply_markup
    )

# Command to start the conversation and ask for email
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text('Please enter your email:')
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text('Please enter your email:')
    return EMAIL
# Handle email input
async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    user = await sync_to_async(Custom_user.objects.filter(email=email).first)()

    if user:
        user.telegram_user_id = update.message.from_user.id
        await sync_to_async(user.save)()
        
    else:
        await update.message.reply_text('Email not found. Please enter your email again .')
        return EMAIL

    context.user_data['user'] = user

    await update.message.reply_text('Please enter your password:')    
    return PASSWORD

MAX_RETRIES = 5

async def request_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = context.user_data.get('user')
    entered_password = update.message.text
    
    # Debug: print the entered password and check_password result
    print(f"Entered password: {entered_password}")
    
    if user:
        is_correct = await sync_to_async(user.check_password)(entered_password)
        print(f"Password correct: {is_correct}")  # Debug: Check password result
    
        if is_correct:
            context.user_data['password_retries'] = 0  # Reset retry count
            await update.message.reply_text(
                'Login successful! Please select an option:',
                reply_markup=get_main_menu_buttons()
            )
            return MENU
    else:
        print("User not found in context")  # Debug: Ensure user exists

    # Handle incorrect password or missing user
    retries = context.user_data.get('password_retries', 0) + 1
    context.user_data['password_retries'] = retries

    if retries >= MAX_RETRIES:
        await update.message.reply_text(
            'Too many incorrect attempts. Please start the process again.'
        )
        return ConversationHandler.END
     
    await update.message.reply_text(
        f'Incorrect password. You have {MAX_RETRIES - retries} attempts left. Please try again:'
    )
    return PASSWORD



# Handle menu selection
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'start_booking':
        return await start_booking(update, context)
    elif action == 'my_bookings':
        return await my_bookings(update, context)
    elif action == 'pending_payments':
        return await pending_payments(update, context)
    elif action == 'cancel_booking':
        return await cancel_booking(update, context)
    elif action == 'start_chat':
        return await start_chat(update, context)
    elif action == 'restart':
        return await restart_bot(update, context)


# Start chat command
async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.message.reply_text('You are now connected to staff. Type your message:')
    return CHAT_STATE

# Handle chat messages
async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user = await sync_to_async(Custom_user.objects.filter(telegram_user_id=user_id).first)()

    if user:
        message_text = update.message.text

        # Save message to database
        await sync_to_async(ChatMessage.objects.create)(user=user, message=message_text)

        # Notify the user
        await update.message.reply_text('Your message has been sent to staff.', reply_markup=get_main_menu_buttons())
        return MENU
    else:
        await update.message.reply_text('User not found. Please restart the bot and provide your email.', reply_markup=get_main_menu_buttons())
        return MENU



async def fetch_all_rooms():
    def get_rooms():
        return Room.objects.all().order_by('-price_per_night')
    return await sync_to_async(get_rooms)()

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Fetch available rooms asynchronously
    available_rooms = await fetch_all_rooms()
    
    keyboard = []

    for room in available_rooms:
        button_text = f"{room.room_number} - {room.room_type.name}\nPrice: ${room.price_per_night}\n"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=str(room.id))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text('Please select a room:', reply_markup=reply_markup)
    return ROOM_SELECTION

# Handle room selection
async def room_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    room_id = int(query.data)
    room = await sync_to_async(Room.objects.get)(id=room_id)
    context.user_data['room'] = room

    await query.message.reply_text(
        f'You selected Room {room.room_number}\nType: {room.room_type.name}\nPrice: ${room.price_per_night}\nCapacity: {room.capacity}\n\nPlease enter your check-in date (YYYY-MM-DD):',
    )
    return CHECK_IN_DATE

# Handle check-in date input
async def check_in_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    check_in_date_str = update.message.text

    try:
        check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d').date()

        if check_in_date < date.today():
            await update.message.reply_text(
                'Check-in date cannot be in the past. Please enter a valid check-in date:',
            )
            return CHECK_IN_DATE

        user_data['check_in_date'] = check_in_date
    except ValueError:
        await update.message.reply_text(
            'Invalid date format. Please use YYYY-MM-DD. Enter again, example 2022-12-31.',
        )
        return CHECK_IN_DATE

    await update.message.reply_text(
        'Great! Now, please enter your check-out date (YYYY-MM-DD):',
    )
    return CHECK_OUT_DATE

# Handle check-out date input
# Handle check-out date input with availability check
async def check_out_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    check_out_date_str = update.message.text

    try:
        check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d').date()

        if check_out_date <= user_data['check_in_date']:
            await update.message.reply_text(
                'Check-out date must be after the check-in date. Please re-enter a valid check-out date:'
            )
            return CHECK_OUT_DATE

        # Store the check-out date temporarily
        user_data['check_out_date'] = check_out_date

        # Perform availability check
        check_in_date = user_data['check_in_date']
        room = context.user_data.get('room')  # Assuming room data is stored in context

        # Check if there are existing bookings that conflict with the selected dates
        existing_bookings = await sync_to_async(Booking.objects.filter)(
            room=room,
            status__in=['pending', 'confirmed'],
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        )

        if await sync_to_async(existing_bookings.exists)():
            # If the room is already booked, prompt the user to re-enter the dates
            await update.message.reply_text(
                'The room is booked for the selected dates. Please choose different check-in and check-out dates.'
            )
            return CHECK_IN_DATE

    except ValueError:
        await update.message.reply_text(
            'Invalid date format. Please use YYYY-MM-DD. Enter again, example 2022-12-31.'
        )
        return CHECK_OUT_DATE

    # If the room is available, proceed to asking for the number of guests
    await update.message.reply_text(
        'Almost there! How many guests will be staying?'
    )
    return GUESTS


# Handle guests input
async def guests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    guests_str = update.message.text

    try:
        guests = int(guests_str)
        room_capacity = user_data['room'].capacity

        if guests < 1:
            await update.message.reply_text(
                'The number of guests must be at least 1. Please enter a valid number of guests:',
            )
            return GUESTS
        elif guests > room_capacity:
            await update.message.reply_text(
                f'The number of guests cannot exceed the room capacity which is {room_capacity} for this room. Please enter a valid number of guests:',
            )
            return GUESTS

        user_data['guests'] = guests
    except ValueError:
        await update.message.reply_text(
            'Invalid input. Please enter a number.',
        )
        return GUESTS

    keyboard = [
        [InlineKeyboardButton("Chapa", callback_data='chapa')],
        [InlineKeyboardButton("PayPal", callback_data='paypal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Please select a payment method:',
        reply_markup=reply_markup
    )

    return PAYMENT_METHOD

# Handle payment method selection
# Handle payment method selection
async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payment_method = query.data
    user_data = context.user_data
    user = user_data['user']

    booking_id = user_data.get('pending_booking_id')

    if booking_id:
        booking = await sync_to_async(Booking.objects.get)(id=booking_id)
    else:
        booking = await sync_to_async(Booking.objects.create)(
            user=user,
            room=user_data['room'],
            check_in_date=user_data['check_in_date'],
            check_out_date=user_data['check_out_date'],
            guests=user_data['guests'],
            tx_ref=f"booking-{user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}",
            total_amount=user_data['room'].price_per_night * (user_data['check_out_date'] - user_data['check_in_date']).days
        )
    user_data['booking'] = booking

    if payment_method == 'chapa':
        new_tx_ref = f"booking-{user.first_name}-tx-{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"
        await query.message.reply_text('Please proceed with Chapa payment.')
        booking = context.user_data['booking']
        amount = str(booking.total_amount)
        redirect_url = f'{BASE_URL}/room/bookings'
        webhook_url = f'{BASE_URL}/room/chapa-webhook/'

        payload = {
            "amount": amount,
            "currency": "ETB",
            "email": booking.user.email,
            "first_name": booking.user.first_name,
            "last_name": booking.user.last_name,
            "phone_number": booking.user.phone_number,
            "redirect_url": redirect_url,
            "tx_ref": new_tx_ref,
            "callback_url": webhook_url,
        }
        headers = {
            'Authorization': f'Bearer {chapa_api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post("https://api.chapa.co/v1/transaction/initialize", json=payload, headers=headers)
        result = response.json()

        if response.status_code == 200:
            checkout_url = result['data']['checkout_url']
            booking.tx_ref = new_tx_ref
            await sync_to_async(booking.save)()
            await update.callback_query.message.reply_text(f'Please complete the payment: {checkout_url}')
        else:
            await update.callback_query.message.reply_text('Error creating Chapa payment.')

        await update.callback_query.message.reply_text(
            'What would you like to do next?',
            reply_markup=get_main_menu_buttons()
        )
        return MENU

    elif payment_method == 'paypal':
        paypalrestsdk.configure({
            "mode": "sandbox",
            "client_id": f'{paypal_client_id}',
            "client_secret": f'{paypal_client_secret}'
        })

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{BASE_URL}/room/paypal-return/?booking_id={booking.id}",
                "cancel_url": f"{BASE_URL}/room/paypal-cancel/?booking_id={booking.id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Booking {booking.id}",
                        "sku": "001",
                        "price": str(booking.total_amount),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(booking.total_amount),
                    "currency": "USD"
                },
                "description": "Room booking payment."
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.method == "REDIRECT":
                    approval_url = str(link.href)
                    await query.message.reply_text(f'Please complete the payment: {approval_url}')
        else:
            await query.message.reply_text('Error creating PayPal payment.')

    await query.message.reply_text(
        'What would you like to do next?',
        reply_markup=get_main_menu_buttons()
    )
    return MENU



# Handle pending payments selection
async def pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user = context.user_data.get('user')

    if not user:
        await query.message.reply_text('User not found. Please restart the bot and enter your email.')
        return MENU

    try:
        bookings = await sync_to_async(list)(Booking.objects.filter(user=user, status='pending'))

        if not bookings:
            await query.message.reply_text('You have no pending payments.')
            await query.message.reply_text(
            'What would you like to do next?',
            reply_markup=get_main_menu_buttons()
                )
            return MENU
            

        for booking in bookings:
            room = booking.room
            message = (
                f"Booking ID: {booking.id}\n"
                f"Room Number: {room.room_number}\n"
                f"Room Type: {room.room_type.name}\n"
                f"Check-in Date: {booking.check_in_date}\n"
                f"Check-out Date: {booking.check_out_date}\n"
                f"Total Amount: ${booking.total_amount}\n"
                f"Payment Status: {booking.status}\n\n"
            )
            await query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Pay Now", callback_data=f'pay_pending_{booking.id}')]
                ])
            )
            

        return PENDING_PAYMENT_PROCESS

    except Exception as e:
        logger.error(f"Error fetching pending payments: {e}")
        await query.message.reply_text('An error occurred while fetching your pending payments. Please try again later.')
        await query.message.reply_text(
            'What would you like to do next?',
            reply_markup=get_main_menu_buttons()
        )
        return MENU
        
async def pay_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Extract booking ID from callback data
    callback_data = query.data
    booking_id = int(callback_data.split('_')[-1])
    context.user_data['pending_booking_id'] = booking_id
    
    # Find the booking with the given ID
    booking = await sync_to_async(Booking.objects.get)(id=booking_id)
    context.user_data['booking'] = booking
    
    # Provide payment options again
    keyboard = [
        [InlineKeyboardButton("Chapa", callback_data='chapa')],
        [InlineKeyboardButton("PayPal", callback_data='paypal')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        'Please select a payment method to complete your pending payment:',
        reply_markup=reply_markup
    )
    
    return PAYMENT_METHOD

# Handle user's bookings



async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user = context.user_data.get('user')

    if not user:
        await query.message.reply_text(
            'What would you like to do next?',
            reply_markup=get_main_menu_buttons()
        )
        return MENU

    try:
        bookings = await sync_to_async(list)(Booking.objects.filter(user=user).exclude(status__in=['cancelled']))

        if not bookings:
            await query.message.reply_text(
            'No bookings to show.What would you like to do next?',
            reply_markup=get_main_menu_buttons()
        )
            return MENU

        for booking in bookings:
            room = booking.room
            message = (
                f"Booking ID: {booking.id}\n"
                f"Room Number: {room.room_number}\n"
                f"Room Type: {room.room_type.name}\n"
                f"Check-in Date: {booking.check_in_date}\n"
                f"Check-out Date: {booking.check_out_date}\n"
                f"Total Amount: ${booking.total_amount}\n"
                f"Payment Status: {booking.status}\n\n"
            )
            await query.message.reply_text(message)

        await query.message.reply_text(
            'What would you like to do next?',
            reply_markup=get_main_menu_buttons()
        )
        return MENU

    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        await query.message.reply_text('An error occurred while fetching your bookings. Please try again later.',reply_markup=get_main_menu_buttons())
        return MENU

# Handle cancellation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Booking cancelled. To start over, type /start.',
        reply_markup=get_main_menu_buttons()
    )
    return MENU


# Display user's bookings and ask which one to cancel
async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user = context.user_data.get('user')

    if not user:
        await query.message.reply_text('User not found. Please restart the bot and enter your email.')
        return MENU

    try:
        bookings = await sync_to_async(list)(Booking.objects.filter(user=user, status__in=['pending', 'confirmed']))

        if not bookings:
            await query.message.reply_text(
        'You have no confirmed bookings to cancel. What would you like to do next?',
        reply_markup=get_main_menu_buttons()
    )
    
            return MENU
            
        for booking in bookings:
            room = booking.room
            message = (
                f"Booking ID: {booking.id}\n"
                f"Room Number: {room.room_number}\n"
                f"Room Type: {room.room_type.name}\n"
                f"Check-in Date: {booking.check_in_date}\n"
                f"Check-out Date: {booking.check_out_date}\n"
                f"Total Amount: ${booking.total_amount}\n"
                f"Payment Status: {booking.status}\n\n"
            )
            await query.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Cancel Booking", callback_data=f'cancel_{booking.id}')]
                ])
            )

        return CANCEL_BOOKING

    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        await query.message.reply_text('An error occurred while fetching your bookings. Please try again later.', reply_markup=get_main_menu_buttons())
        return MENU

# Handle the actual cancellation
async def confirm_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Extract booking ID from callback data
    callback_data = query.data
    booking_id = int(callback_data.split('_')[-1])
    
    # Find the booking with the given ID
    booking = await sync_to_async(Booking.objects.get)(id=booking_id)
    
    # Change the status to 'cancelled'
    
    booking.status = 'cancelled'
    await sync_to_async(booking.save)()
    
    await query.message.reply_text(f'Booking ID {booking.id} has been cancelled successfully.')
    
    await query.message.reply_text(
        'What would you like to do next?',
        reply_markup=get_main_menu_buttons()
    )
    
    return MENU





async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.message.reply_text('Bot restarted. Please enter your email to start booking:')
    return EMAIL



def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers to the application
    application.add_handler(CommandHandler('welcome', welcome))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(start, pattern='^start$')],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_password)],
            MENU: [CallbackQueryHandler(menu)],
            ROOM_SELECTION: [CallbackQueryHandler(room_selection)],
            CHECK_IN_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_in_date)],
            CHECK_OUT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_out_date)],
            GUESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, guests)],
            PAYMENT_METHOD: [CallbackQueryHandler(payment_method)],
            MY_BOOKINGS: [CallbackQueryHandler(my_bookings)],
            PENDING_PAYMENTS: [CallbackQueryHandler(pending_payments)],
            PENDING_PAYMENT_PROCESS: [CallbackQueryHandler(pay_pending)],
            CANCEL_BOOKING: [CallbackQueryHandler(confirm_cancellation)],
            CHAT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message)]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()