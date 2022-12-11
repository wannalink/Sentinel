from CWebSocket import initialize_websocket

from Schema import create_database
from threading import Thread
from commands import bot
from os import environ
import logging
from dotenv import load_dotenv
# from webserver import keep_alive

load_dotenv()
logging.basicConfig(filename='tmp/sentinel.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def run_bot():
    bot.run(environ['DISCORD_TOKEN'])


def main():
    create_database()
    Thread(target=initialize_websocket, args=[]).start()
    t2 = Thread(target=run_bot, args=())
    t2.start()
    t2.join()
    

if __name__ == '__main__':
    main()

# keep_alive()
