from CWebSocket import initialize_websocket

from Schema import create_database
from threading import Thread
from commands import bot
from os import environ, path, system
import logging
import logging.handlers
from dotenv import load_dotenv
from webserver import keep_alive
import discord
from time import sleep

load_dotenv()

# Logger
LOG_FILENAME = 'tmp/sentinel.log'
if not path.exists(LOG_FILENAME):
    import os
    try:
        os.makedirs("tmp")
    except FileExistsError:
    # directory already exists
        pass
    open(LOG_FILENAME, 'w').close()
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.INFO,                
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logger = logging.getLogger(__name__)


def run_bot():
  import config
  while True:
    try:
      bot.run(environ['DISCORD_TOKEN'])
    except discord.errors.HTTPException:
      config.discord_status = None
      logger.info("Rate limited, sleeping")
      sleep(300)
      logger.info("Restarting discord")
      continue
    except Exception as err:
      config.discord_status = None
      logger.exception(f"Discord Error: {err}")
      sleep(300)
      logger.info("Restarting discord")
      continue


def main():
    logger.info("Main func initialized")
    keep_alive()
    create_database()
    Thread(target=initialize_websocket, args=[]).start()
    t2 = Thread(target=run_bot, args=())
    t2.start()
    t2.join()
  
  
if __name__ == '__main__':
    main()
