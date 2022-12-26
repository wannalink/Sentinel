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
from pygtail import Pygtail
from flask import Flask, abort, Response, render_template
from main import LOG_FILENAME

SYNTAX                        = 'Syntax: python {0} <script>'
WEB_SERVER_KEEP_ALIVE_MESSAGE = 'Keeping the repl alive!'


flask: Flask          = Flask('replit_keep_alive')
log:   logging.Logger = logging.getLogger('werkzeug')

@flask.route('/')
def index() -> str:
    """ Method for handling the base route of '/'. """
    return WEB_SERVER_KEEP_ALIVE_MESSAGE

@flask.route('/status')
def entry_point():
	from datetime import datetime, timedelta
	from threading import enumerate
	from config import service_status
	def service_status_check():
		def thread_checker(service):
			for th in enumerate():
				if th.name == service:
					service_status[service]['thread'] = 'alive'
					return service_status[service]['thread']
			service_status[service]['thread'] = 'down'
			return service_status[service]['thread']
		now = datetime.now()
		for service in service_status.keys():
			thread_checker(service)
			if service_status[service]['started']:
				if service_status[service]['stopped'] == None or service_status[service]['started'] > service_status[service]['stopped']:
					tdelta = now - service_status[service]['started']
					service_status[service]['duration'] = str(timedelta(seconds=tdelta.seconds))
		return service_status
	return render_template('base.html', data=service_status_check())


@flask.route('/log')
def progress_log():
	def generate():
		for line in Pygtail(LOG_FILENAME, every_n=1):
			yield "data:" + str(line) + "\n\n"
			sleep(0.5)
	return Response(generate(), mimetype= 'text/event-stream')


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