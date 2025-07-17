import telebot
from src import config, llm, retriever
from googletrans import Translator

# Initialize the translator once
translator = Translator()

def run_bot(llm_model, tokenizer, db):
    bot = telebot.TeleBot(config.TELEGRAM_API_TOKEN)
    
    print("Telegram bot is running...")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # Your welcome handler logic...
        bot.send_message(message.chat.id, "Welcome! I am your AI Personal Stylist.")

    # --- Add all your other handlers here ---
    # Example:
    @bot.message_handler(func=lambda message: message.text == '👕 پیشنهاد لباس')
    def handle_recommendation_request(message):
        # ... your conversation logic ...
        # When you need a recommendation:
        # output = llm.get_outfit_recommendation(details, event, llm_model, tokenizer)
        # translated_output = translator.translate(output, dest='fa').text
        # bot.send_message(message.chat.id, translated_output)
        bot.send_message(message.chat.id, "Outfit recommendation feature is under construction.")

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        bot.reply_to(message, "Command not recognized. Use /start to begin.")

    bot.infinity_polling()