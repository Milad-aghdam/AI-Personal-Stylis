import telebot
import re
from telebot import types
from googletrans import Translator
from io import BytesIO

# Import our project modules
from src import config
from src.llm import get_outfit_recommendation, format_instruction 
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

    # In src/bot.py

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_search_gender")
    def process_search_gender(message):
        gender = message.text
        if gender not in ['زن', 'مرد']:
            bot.send_message(message.chat.id, "انتخاب نامعتبر است. لطفاً 'زن' یا 'مرد' را انتخاب کنید.")
            return

        user_states[message.chat.id]["gender"] = gender
        user_states[message.chat.id]["step"] = "awaiting_search_description"
        
        # --- NEW, MORE HELPFUL PROMPT ---
        prompt_text = (
            "عالی! حالا لطفاً *توضیحاتی از یک لباس* را وارد کنید تا موارد مشابه را برایتان پیدا کنم.\n\n"
            "✅ *مثال‌های خوب:*\n"
            " - `کفش راحتی مردانه چرم قهوه‌ای`\n"
            " - `پیراهن زنانه آستین بلند سفید`\n"
            " - `شلوار جین آبی تیره زنانه`\n\n"
            "❌ *مثال‌های بد:*\n"
            " - `لباس برای مهمانی` (خیلی کلی است)\n"
            " - `یک کلمه` (توضیحات کافی نیست)"
        )
        # -----------------------------------
    
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
        bot.send_message(message.chat.id, "بسیار خب. حالا نوع رویداد را وارد کنید (مثلا: `جلسه کاری`، `مهمانی` ,`دوستانه`)")

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_event")
    def process_outfit_event(message):
        chat_id = message.chat.id
        event = message.text
        details = user_states[chat_id].get("details", "a person")

        bot.send_message(chat_id, "در حال آماده کردن پیشنهادات... این فرآیند ممکن است کمی طول بکشد 🧠")

        try:
            # 1. Get the structured list of outfits from the LLM
            outfits = get_outfit_recommendation(details, event, llm_model, tokenizer)
            
            if not outfits:
                bot.send_message(chat_id, "متاسفانه در تولید پیشنهاد مشکلی پیش آمد. لطفاً درخواست خود را کمی تغییر دهید و دوباره تلاش کنید.", reply_markup=generate_main_menu())
                user_states[chat_id] = {}
                return

            # 2. Store the outfits and update the user's state
            user_states[chat_id]['outfits'] = outfits
            user_states[chat_id]['step'] = "awaiting_outfit_selection"

            # 3. Create a dynamic keyboard with a preview of each option
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            for i, outfit in enumerate(outfits[:4]): # Show up to 4 options
                # Use the 'Top' description as a preview
                preview = outfit.get('Top', 'بدون عنوان')
                markup.add(types.KeyboardButton(f"گزینه {i+1}: {preview[:30]}..."))
            markup.add(types.KeyboardButton("بازگشت به منوی اصلی"))

            bot.send_message(chat_id, "چند پیشنهاد برای شما آماده شد. لطفاً یکی را برای دیدن جزئیات انتخاب کنید:", reply_markup=markup)

        except Exception as e:
            print(f"Error during outfit generation or parsing: {e}")
            bot.send_message(chat_id, "متاسفانه در پردازش درخواست شما خطایی رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=generate_main_menu())
            user_states[chat_id] = {}
    

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_selection")
    def process_outfit_selection(message):
        chat_id = message.chat.id
        
        if message.text == "بازگشت به منوی اصلی":
            user_states[chat_id] = {}
            bot.send_message(chat_id, "چه کار دیگری می‌توانم برایتان انجام دهم؟", reply_markup=generate_main_menu())
            return

        match = re.match(r'گزینه (\d+):', message.text)
        if not match:
            bot.send_message(chat_id, "لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=generate_main_menu())
            return

        try:
            index = int(match.group(1)) - 1
            outfits = user_states[chat_id].get('outfits', [])
            
            if 0 <= index < len(outfits):
                chosen_outfit = outfits[index]
                
                # --- START: New Formatting Logic ---

                # Dictionary to map English keys to Farsi and an emoji
                key_map = {
                    'Top': '👕 *بالا:*',
                    'Bottom': '👖 *پایین:*',
                    'Shoe': '👟 *کفش:*',
                    'Shoes': '👟 *کفش:*',  # Handle both singular and plural
                    'Accessories': '👜 *اکسسوری:*'
                }
                
                response_parts = [f"✨ *جزئیات گزینه {index + 1}* ✨"]
                
                for key_en, value_en in chosen_outfit.items():
                    # Get the formatted Farsi key, or just bold the original if not found
                    key_fa_formatted = key_map.get(key_en.capitalize(), f"*{key_en.capitalize()}:*")
                    
                    # Translate the description
                    value_fa = translator.translate(value_en, dest='fa').text
                    
                    # Combine the formatted key and the translated value
                    response_parts.append(f"{key_fa_formatted}\n{value_fa}")
                
                # Join the parts with double newlines for clear spacing
                final_response = "\n\n".join(response_parts)
                
                bot.send_message(chat_id, final_response)
                
                # --- END: New Formatting Logic ---

            else:
                bot.send_message(chat_id, "گزینه انتخاب شده نامعتبر است.")

        except (KeyError, IndexError, ValueError) as e:
            print(f"Error processing selection: {e}")
            bot.send_message(chat_id, "خطایی در نمایش جزئیات رخ داد.")

        # Reset state and return to main menu
        user_states[chat_id] = {}
        bot.send_message(chat_id, "امیدوارم مفید بوده باشد! برای ادامه از منو استفاده کنید.", reply_markup=generate_main_menu())