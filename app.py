from CWebSocket import initialize_websocket

from Schema import create_database
from threading import Thread
from commands import bot
from os import environ, path, system
import logging
from dotenv import load_dotenv
from webserver import keep_alive
import discord

load_dotenv()

# Logger
LOG_FILENAME = 'storage/tmp/sentinel.log'
if not path.exists(LOG_FILENAME):
    import os
    try:
        os.makedirs("storage/tmp")
    except FileExistsError:
        # directory already exists
        pass
    open(LOG_FILENAME, 'w').close()
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)


def run_bot():
    from config import service_status
    from datetime import datetime
    try:
        bot.run(environ['DISCORD_TOKEN'])
    except discord.errors.HTTPException or RuntimeError:
        service_status['discord']['stopped'] = datetime.now()
        logger.warning("Rate limited")
        system("kill 1")
    except Exception as err:
        service_status['discord']['stopped'] = datetime.now()
        logger.exception(f"Discord Error: {err}")
        # system("kill 1")


def main():
    logger.info("---------- Main func initialized ----------")
    keep_alive()
    create_database()
    Thread(target=initialize_websocket, name='websocket', args=[]).start()
    t2 = Thread(target=run_bot, name='discord', args=())
    t2.start()
    t2.join()


if __name__ == '__main__':
    main()
