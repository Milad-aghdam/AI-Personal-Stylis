import telebot
import re
from telebot import types
from googletrans import Translator
from io import BytesIO

# Import our project modules
from src import config
from src.llm import get_outfit_recommendation, format_instruction_for_llm # Assuming we rename the function
from src.retriever import search_for_products

# --- Globals and Initializations ---

# Initialize the translator once to be efficient
translator = Translator()

# A simple dictionary to hold the state of each user's conversation
user_states = {}

# --- UI Helper Functions (Keyboards/Menus) ---

def generate_main_menu():
    """Creates the main menu keyboard with primary options."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🔍 جستجوی محصولات')
    btn2 = types.KeyboardButton('👕 پیشنهاد لباس')
    btn3 = types.KeyboardButton('❓ راهنما')
    markup.add(btn1, btn2, btn3)
    return markup

def generate_gender_menu():
    """Creates a keyboard for gender selection."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('زن'), types.KeyboardButton('مرد'))
    return markup

def generate_feedback_menu():
    """Creates a keyboard for user feedback."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('✅ بله، عالی بود'), types.KeyboardButton('🔄 خیر، دوباره امتحان کنم'))
    return markup

# --- Main Bot Logic ---

def run_bot(llm_model, tokenizer, db):
    """
    Initializes and runs the Telegram bot.
    Passes the loaded AI models and database to the bot handlers.
    """
    bot = telebot.TeleBot(config.TELEGRAM_API_TOKEN, parse_mode='Markdown')
    print("🤖 Telegram bot is running...")

    # --- Utility and Welcome Handlers ---

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_states[message.chat.id] = {} # Clear any previous state
        welcome_text = "سلام! من ربات مشاور لباس هستم. چگونه می‌توانم کمکتان کنم؟"
        bot.send_message(message.chat.id, welcome_text, reply_markup=generate_main_menu())

    @bot.message_handler(func=lambda msg: msg.text == '❓ راهنما')
    def send_help(message):
        help_text = (
            "✨ *راهنمای ربات مشاور لباس*\n\n"
            "از دکمه‌های زیر برای تعامل با من استفاده کنید:\n"
            "1. *🔍 جستجوی محصولات*: برای پیدا کردن لباس بر اساس توضیحات شما.\n"
            "2. *👕 پیشنهاد لباس*: برای دریافت ست‌های لباس بر اساس مشخصات و رویداد.\n\n"
            "برای شروع مجدد، دستور /start را ارسال کنید."
        )
        bot.send_message(message.chat.id, help_text)

    # --- Product Search Handlers ---

    @bot.message_handler(func=lambda msg: msg.text == '🔍 جستجوی محصولات')
    def handle_search_products(message):
        user_states[message.chat.id] = {"step": "awaiting_search_gender"}
        bot.send_message(message.chat.id, "لطفاً جنسیت را انتخاب کنید:", reply_markup=generate_gender_menu())

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_search_gender")
    def process_search_gender(message):
        gender = message.text
        if gender not in ['زن', 'مرد']:
            bot.send_message(message.chat.id, "انتخاب نامعتبر است. لطفاً 'زن' یا 'مرد' را انتخاب کنید.")
            return

        user_states[message.chat.id]["gender"] = gender
        user_states[message.chat.id]["step"] = "awaiting_search_description"
        
        prompt_text = (
            "لطفاً توضیحات محصول مورد نظر را وارد کنید.\n\n"
            "*مثال‌ها:*\n"
            " - `کفش راحتی شرابی رنگ`\n"
            " - `کتانی اسپرت مشکی با کفی نرم`\n"
            " - `کیف چرم قهوه‌ای با بند بلند`"
        )
        bot.send_message(message.chat.id, prompt_text, reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_search_description")
    def process_product_description(message):
        chat_id = message.chat.id
        description = message.text
        gender = user_states[chat_id].get("gender", "woman") # Default to woman
        
        bot.send_message(chat_id, "در حال جستجو... لطفاً صبر کنید ⏳")
        
        # Translate to English for the model
        translated_desc = translator.translate(description, dest='en').text
        search_prompt = f"For {gender}, {translated_desc}"

        # Call the retriever function
        final_img, final_txt = search_for_products(search_prompt, db)

        if final_img and final_txt:
            img_io = BytesIO()
            final_img.save(img_io, format='PNG')
            img_io.seek(0)
            
            bot.send_photo(chat_id, photo=img_io, caption=final_txt)
        else:
            bot.send_message(chat_id, "متاسفانه محصولی با این مشخصات پیدا نشد. لطفاً دوباره تلاش کنید.")
        
        # Reset state and show main menu
        user_states[chat_id] = {}
        bot.send_message(chat_id, "چه کار دیگری می‌توانم برایتان انجام دهم؟", reply_markup=generate_main_menu())


    # --- Outfit Recommendation Handlers ---

    @bot.message_handler(func=lambda msg: msg.text == '👕 پیشنهاد لباس')
    def handle_outfit_recommendation(message):
        user_states[message.chat.id] = {"step": "awaiting_outfit_gender"}
        bot.send_message(message.chat.id, "برای پیشنهاد لباس، لطفاً جنسیت را انتخاب کنید:", reply_markup=generate_gender_menu())
        
    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_gender")
    def process_outfit_gender(message):
        gender = message.text
        if gender not in ['زن', 'مرد']:
            bot.send_message(message.chat.id, "انتخاب نامعتبر است. لطفاً 'زن' یا 'مرد' را انتخاب کنید.")
            return

        user_states[message.chat.id]["gender"] = gender
        user_states[message.chat.id]["step"] = "awaiting_outfit_details"
        
        prompt_text = (
            "عالی! حالا لطفاً مشخصات خود را وارد کنید.\n\n"
            "*مثال:*\n"
            "`بدنی مستطیلی، قد ۱۷۱، سبک روزمره، رنگ‌های تیره`"
        )
        bot.send_message(message.chat.id, prompt_text, reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_details")
    def process_outfit_details(message):
        user_states[message.chat.id]["details"] = message.text
        user_states[message.chat.id]["step"] = "awaiting_outfit_event"
        bot.send_message(message.chat.id, "بسیار خب. حالا نوع رویداد را وارد کنید (مثلا: `جلسه کاری`، `مهمانی دوستانه`)")

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_event")
    def process_outfit_event(message):
        chat_id = message.chat.id
        event = message.text
        details = user_states[chat_id].get("details", "a person")

        bot.send_message(chat_id, "در حال آماده کردن پیشنهادات... این فرآیند ممکن است کمی طول بکشد 🧠")

        try:
            # Call the LLM function
            recommendation_en = get_outfit_recommendation(details, event, llm_model, tokenizer)
            
            # Translate the final result
            recommendation_fa = translator.translate(recommendation_en, dest='fa').text
            
            # Simple formatting for the response
            # A more robust solution would parse the output properly
            formatted_response = f"✨ *پیشنهادات لباس برای {event}:*\n\n{recommendation_fa}"
            
            bot.send_message(chat_id, formatted_response)

        except Exception as e:
            print(f"Error during LLM generation: {e}")
            bot.send_message(chat_id, "متاسفانه در پردازش درخواست شما خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        
        # Reset state and show main menu
        user_states[chat_id] = {}
        bot.send_message(chat_id, "امیدوارم مفید بوده باشد! چه کار دیگری می‌توانم انجام دهم؟", reply_markup=generate_main_menu())


    # --- Fallback Handler ---
    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        bot.send_message(message.chat.id, "دستور شناسایی نشد. لطفاً از دکمه‌های منو استفاده کنید یا /start را برای شروع مجدد بزنید.")

    # Start polling
    bot.infinity_polling()