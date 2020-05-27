"""Price tracking bot on Telegram."""

import requests
import re
import logging
import threading
import time
import random
from urllib.parse import urlparse
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

threads = {}
patterns = {
    'shop.mango.com': 'salePrice":"([0-9\.]+)","originalPrice":',
    'www.stories.com': '"product:price:amount" content="([0-9\.]+)">',
    'www.urbanoutfitters.com': '"product:price:amount" content="([0-9\.]+)">',
    'www.zara.com': '"price": "([0-9\.]+)"',
    'www2.hm.com': '"price": "([0-9\.]+)"',
}

headers = {
    'User-Agent': 'Mozilla/5.0',
}

class PriceTrackThread(threading.Thread):
    
    def __init__(self, update):
        threading.Thread.__init__(self)
        self.update = update
        self.is_stop = False

    def run(self):
        price_prev = '0'
        while not self.is_stop:
            try:
                url_domain = urlparse(self.update.message.text).netloc
                pat = patterns[url_domain]
            except:
                self.update.message.reply_text('Website not supported.', quote=True)
                msg_id = self.update.message.message_id
                if msg_id in threads:
                    threads.pop(msg_id)
                break
            
            try:
                response = requests.get(self.update.message.text, headers=headers)
            except:
                self.update.message.reply_text('Failed to access the website.', quote=True)
            
            m = re.search(pat, response.text)
            if m:
                price = m.group(1)
                if price != price_prev:
                    if price_prev == '0':
                        self.update.message.reply_text(
                           "Price: $%s" % price,
                           quote=True)
                    else:
                        self.update.message.reply_text(
                           "Price: $%s, was $%s" % (price, price_prev),
                           quote=True)
                    price_prev = price
            else:
                self.update.message.reply_text('No price found!', quote=True)

            time.sleep(random.randint(3600,7200))
    
    def stop(self):
        self.is_stop = True

        
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

    
def stop(update, context):
    """Stop tracking the price of an item by replying the original message"""
    msg_id = update.message.reply_to_message.message_id
    if msg_id in threads:
        threads.pop(msg_id).stop()
    
    update.message.reply_text('Stopped tracking!', quote=True)

    
def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def price(update, context):
    """Start tracking price."""
    t = PriceTrackThread(update)
    threads.update({update.message.message_id: t})
    t.start()
    

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("YOUR_TOKEN_HERE", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("stop", stop))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, price))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()