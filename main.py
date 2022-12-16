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

# Logger
LOG_FILENAME = 'tmp/sentinel.log'
if not path.exists(LOG_FILENAME):
    open(LOG_FILENAME, 'w').close()
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.ERROR,                
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

def run_bot():
  try:
    bot.run(environ['DISCORD_TOKEN'])
  except Exception as e:
    logger.exception(f"Discord not connecting: {e} {e.status}")
    if e.status == 429:
      logger.info("Killing container")
      system("kill 1")
    

def main():
    logger.warning("Main func initialized")
    keep_alive()
    create_database()
    Thread(target=initialize_websocket, args=[]).start()
    t2 = Thread(target=run_bot, args=())
    t2.start()
    t2.join()
  
  
if __name__ == '__main__':
    main()
