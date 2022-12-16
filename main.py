from CWebSocket import initialize_websocket

from Schema import create_database
from threading import Thread
from commands import bot
from os import environ, path, system
import logging
import logging.handlers
from dotenv import load_dotenv
from webserver import keep_alive

load_dotenv()
LOG_FILENAME = 'tmp/sentinel.log'
if not path.exists(LOG_FILENAME):
    open(LOG_FILENAME, 'w').close()
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=5)
logger = logging.getLogger(__name__)
logger.addHandler(handler)


def run_bot():
  try:
    bot.run(environ['DISCORD_TOKEN'])
  except Exception as e:
    logger.exception(f"Discord not connecting: {e} {e.status}")
    if e.status == 429:
      logger.warning("Killing container")
      system("kill 1")
    

def main():
  create_database()
  Thread(target=initialize_websocket, args=[]).start()
  t2 = Thread(target=run_bot, args=())
  t2.start()
  t2.join()
  keep_alive()
  
if __name__ == '__main__':
    main()
