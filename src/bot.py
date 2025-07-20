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
translator = Translator()
user_states = {}

# --- UI Helper Functions (Keyboards/Menus) ---
def generate_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('🔍 جستجوی محصولات'), types.KeyboardButton('👕 پیشنهاد لباس'), types.KeyboardButton('❓ راهنما'))
    return markup

def generate_gender_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('زن'), types.KeyboardButton('مرد'))
    return markup

# --- Main Bot Logic ---
def run_bot(llm_model, tokenizer, db):
    bot = telebot.TeleBot(config.TELEGRAM_API_TOKEN, parse_mode='Markdown')
    print("🤖 Telegram bot is running...")

    # --- Handlers (Welcome, Help, Product Search) ---
    # These handlers are already correct and do not need changes.
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_states[message.chat.id] = {}
        bot.send_message(message.chat.id, "سلام! من ربات مشاور لباس هستم. چگونه می‌توانم کمکتان کنم؟", reply_markup=generate_main_menu())

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

    @bot.message_handler(func=lambda msg: msg.text == '🔍 جستجوی محصولات')
    def handle_search_products(message):
        user_states[message.chat.id] = {"step": "awaiting_search_gender"}
        bot.send_message(message.chat.id, "لطفاً جنسیت را انتخاب کنید:", reply_markup=generate_gender_menu())
        
    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_search_gender")
    def process_search_gender(message):
        user_states[message.chat.id]["gender"] = message.text
        user_states[message.chat.id]["step"] = "awaiting_search_description"
        prompt_text = (
            "عالی! حالا لطفاً *توضیحاتی از یک لباس* را وارد کنید تا موارد مشابه را برایتان پیدا کنم.\n\n"
            "✅ *مثال‌های خوب:*\n"
            " - `کفش راحتی مردانه چرم قهوه‌ای`\n"
            " - `پیراهن زنانه آستین بلند سفید`\n\n"
            "❌ *مثال‌های بد:*\n"
            " - `لباس برای مهمانی` (خیلی کلی است)\n"
            " - `یک کلمه` (توضیحات کافی نیست)"
        )
        bot.send_message(message.chat.id, prompt_text, reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_search_description")
    def process_product_description(message):
        chat_id = message.chat.id
        description = message.text
        persian_gender = user_states[chat_id].get("gender", "زن")
        gender_filter = "Women" if persian_gender == "زن" else "Men"
        bot.send_message(chat_id, "در حال جستجو... لطفاً صبر کنید ⏳")
        search_prompt = translator.translate(description, dest='en').text
        final_img, final_txt = search_for_products(prompt=search_prompt, gender_filter=gender_filter, db=db)
        if final_img and final_txt:
            img_io = BytesIO()
            final_img.save(img_io, 'PNG')
            img_io.seek(0)
            bot.send_photo(chat_id, photo=img_io, caption=final_txt)
        else:
            bot.send_message(chat_id, "متاسفانه محصولی با این مشخصات پیدا نشد. لطفاً دوباره تلاش کنید.")
        user_states[chat_id] = {}
        bot.send_message(chat_id, "چه کار دیگری می‌توانم برایتان انجام دهم؟", reply_markup=generate_main_menu())

    # --- Outfit Recommendation Handlers (WITH IMPROVEMENTS) ---
    @bot.message_handler(func=lambda msg: msg.text == '👕 پیشنهاد لباس')
    def handle_outfit_recommendation(message):
        user_states[message.chat.id] = {"step": "awaiting_outfit_gender"}
        bot.send_message(message.chat.id, "برای پیشنهاد لباس، لطفاً جنسیت را انتخاب کنید:", reply_markup=generate_gender_menu())
        
    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_gender")
    def process_outfit_gender(message):
        user_states[message.chat.id]["gender"] = message.text
        user_states[message.chat.id]["step"] = "awaiting_outfit_details"
        
        # --- IMPROVEMENT 1: A more helpful and readable prompt ---
        prompt_text = (
            "عالی! حالا لطفاً مشخصات خود را وارد کنید تا بهترین پیشنهادها را برایتان پیدا کنم.\n\n"
            "می‌توانید مواردی مثل *نوع بدن، قد، سبک و رنگ‌های مورد علاقه* را ذکر کنید.\n\n"
            "*چند مثال:*\n"
            "- `بدنی گلابی شکل، قد ۱۶۵، سبک مینیمال و ساده، رنگ‌های خنثی`\n"
            "- `کمی شکم دارم، قد ۱۸۰، سبک اسپرت و راحت، رنگ‌های تیره`"
        )
        bot.send_message(message.chat.id, prompt_text, reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_details")
    def process_outfit_details(message):
        user_states[message.chat.id]["details"] = message.text
        user_states[message.chat.id]["step"] = "awaiting_outfit_event"
        
        # --- IMPROVEMENT 2: A clearer prompt with suggested event buttons ---
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            types.KeyboardButton('محیط کاری'),
            types.KeyboardButton('مهمانی دوستانه'),
            types.KeyboardButton('استفاده روزمره'),
            types.KeyboardButton('قرار رسمی')
        )
        bot.send_message(message.chat.id, "بسیار خب. حالا *نوع رویداد یا موقعیت* مورد نظر را انتخاب کنید یا تایپ کنید:", reply_markup=markup)

    @bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("step") == "awaiting_outfit_event")
    def process_outfit_event(message):
        chat_id = message.chat.id
        event = message.text
        details = user_states[chat_id].get("details", "a person")
        bot.send_message(chat_id, "در حال آماده کردن پیشنهادات... این فرآیند ممکن است کمی طول بکشد 🧠", reply_markup=types.ReplyKeyboardRemove())
        try:
            outfits = get_outfit_recommendation(details, event, llm_model, tokenizer)
            if not outfits:
                bot.send_message(chat_id, "متاسفانه در تولید پیشنهاد مشکلی پیش آمد. لطفاً دوباره تلاش کنید.", reply_markup=generate_main_menu())
                user_states[chat_id] = {}
                return
            
            user_states[chat_id]['outfits'] = outfits
            user_states[chat_id]['step'] = "awaiting_outfit_selection"

            # --- IMPROVEMENT 3: Translate the preview text BEFORE creating the button ---
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
            for i, outfit in enumerate(outfits[:4]):
                preview_en = outfit.get('Top', 'پیشنهاد بدون عنوان')
                # Translate the English preview to Farsi
                preview_fa = translator.translate(preview_en, dest='fa').text
                # Use the Farsi preview in the button text for correct rendering
                markup.add(types.KeyboardButton(f"گزینه {i+1}: {preview_fa[:40]}..."))
            markup.add(types.KeyboardButton("بازگشت به منوی اصلی"))
            
            bot.send_message(chat_id, "چند پیشنهاد برای شما آماده شد. لطفاً یکی را برای دیدن جزئیات انتخاب کنید:", reply_markup=markup)
        except Exception as e:
            print(f"Error during outfit generation or parsing: {e}")
            bot.send_message(chat_id, "متاسفانه در پردازش درخواست شما خطایی رخ داد.", reply_markup=generate_main_menu())
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
                key_map = {'Top':'👕 *بالا:*','Bottom':'👖 *پایین:*','Shoe':'👟 *کفش:*','Shoes':'👟 *کفش:*','Accessories':'👜 *اکسسوری:*'}
                response_parts = [f"✨ *جزئیات گزینه {index + 1}* ✨"]
                for key_en, value_en in chosen_outfit.items():
                    key_fa_formatted = key_map.get(key_en.capitalize(), f"*{key_en.capitalize()}:*")
                    value_fa = translator.translate(value_en, dest='fa').text
                    response_parts.append(f"{key_fa_formatted}\n{value_fa}")
                final_response = "\n\n".join(response_parts)
                bot.send_message(chat_id, final_response)
            else:
                bot.send_message(chat_id, "گزینه انتخاب شده نامعتبر است.")
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error processing selection: {e}")
            bot.send_message(chat_id, "خطایی در نمایش جزئیات رخ داد.")
        user_states[chat_id] = {}
        bot.send_message(chat_id, "امیدوارم مفید بوده باشد! برای ادامه از منو استفاده کنید.", reply_markup=generate_main_menu())

    @bot.message_handler(func=lambda message: True)
    def handle_unknown(message):
        bot.send_message(message.chat.id, "دستور شناسایی نشد. لطفاً از دکمه‌های منو استفاده کنید یا /start را برای شروع مجدد بزنید.")

    print("Bot polling started. It will now run indefinitely.")
    bot.infinity_polling(none_stop=True)