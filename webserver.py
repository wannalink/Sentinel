#!/usr/bin/env python
"""
Replit Keep Alive is a Python script wrapper meant to, with the help of UptimeRobot, keep Replit
from terminating the bot when the browser tab is closed.
"""

import logging
import subprocess
import sys
import threading
from threading import Thread
from time import sleep

from flask import Flask, abort

SYNTAX                        = 'Syntax: python {0} <script>'
WEB_SERVER_KEEP_ALIVE_MESSAGE = 'Keeping the repl alive!'

flask: Flask          = Flask('replit_keep_alive')
log:   logging.Logger = logging.getLogger('werkzeug')

@flask.route('/')
def index() -> str:
    """ Method for handling the base route of '/'. """
    return WEB_SERVER_KEEP_ALIVE_MESSAGE

# logger as index
@flask.route('/logs')
def stream():
    def generate():
        with open('tmp/sentinel.log') as f:
            while True:
                yield f.read()
                sleep(1)

    return flask.response_class(generate(), mimetype='text/plain')


@flask.route('/discord')
def discord_status():
  def generate():
    import config
    if config.discord_status != None:
      return flask.response_class(str(config.discord_status), mimetype='text/plain')
    else:
      return abort(404)
  return generate()


@flask.route('/status')
def stack_status():
  def generate():
    import config
    d_status = 'off'
    w_status = 'off'
    if config.discord_status != None:
      d_status = str(config.discord_status)
    if config.websocket_status != None:
      w_status = str(config.websocket_status)
    threads = str(threading.enumerate())
    result = (d_status, w_status, threads)
    return flask.response_class(result, mimetype='text/plain')
  return generate()
  

@flask.route('/websocket')
def websocket_status():
  def generate():
    import config
    if config.websocket_status != None:
      return flask.response_class(str(config.websocket_status), mimetype='text/plain')
    else:
      return abort(404)
  return generate()


def keep_alive() -> None:
    """ Wraps the web server run() method in a Thread object and starts the web server. """
    def run() -> None:
        log.setLevel(logging.ERROR)
        flask.run(host = '0.0.0.0', port = 8080)
    thread = Thread(target = run, name='webserver')
    thread.start()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(SYNTAX.format(sys.argv[0]), file = sys.stderr)
    else:
        keep_alive()
        subprocess.call(['python', sys.argv[1]])