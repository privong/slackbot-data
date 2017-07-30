#!/usr/bin/env python
#
# databot.py
#
# Slack bot for the dualAGN channel to handle data queries.
#
# Copyright 2016 George C. Privon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import configparser
import sys
import time
import re
import os
import signal
from slackclient import SlackClient
import MySQLdb


def shutdown():
    """
    Cleanly close MySQL connection.
    """
    try:
        sys.stdout.write("Closing database connection.\n")
        scon.close()
    except:
        sys.stderr.write("Error closing database connection.\n")


def signal_handler(signal, frame):
    sys.stderr.write("Bot killed.\n")
    shutdown()
    sys.exit(1)

        
def handlemsg(slackmsg):
    """
    """
    commands = ['when is the next observing run',
                'what data are we waiting on',
                'how many objects have been observed with',
                'what datasets are available for',
                'list all future observing runs',
                'kill']

    BOTID = 'U1EJ9GBJM'
    ATBOT = "<@" + BOTID + ">"
    msg = slackmsg[0]
    response = {'type': 'message',
                'channel': '',
                'user': '',
                'team': '',
                'text': ''}
    reply = ''

    if not('text' in msg.keys()):
        return 0
    if msg['type'] == 'message' and ATBOT in msg['text']:
        inquiry = msg['text']
        scon.commit()
        if re.search('<@', inquiry[:2]):
            # reply to the user who asked
            reply = '<@' + msg['user'] + '>: '
        if re.search(commands[0],
                     inquiry,
                     re.I):
            query = 'SELECT * FROM observing_runs WHERE start > NOW() \
ORDER BY start;'
            scur.execute(query)
            recs = scur.fetchall()
            recs = recs[0]
            reply = reply + ' The next observing run starts on ' + \
                    recs[3].isoformat() + ' at ' + recs[1]
        elif re.search(commands[1],
                       inquiry,
                       re.I):
            query = 'SELECT telescope,instrument,name FROM datasets WHERE status="pending" ORDER BY name;'
            scur.execute(query)
            recs = scur.fetchall()
            nwait = len(recs)
            reply = reply + 'We are waiting on {0:d} observations:'.format(nwait)
            csrc = recs[0][2]
            reply = reply + '\n' + csrc + ': '
            for rec in recs:
                if rec[2] != csrc:
                    csrc = rec[2]
                    reply = reply[:-2] + '\n' + csrc + ': '
                reply = reply + '+'.join([rec[0], rec[1]]) + ', '
            reply = reply[:-2]
        elif re.search(commands[2],
                       inquiry,
                       re.I):
            ti = inquiry.split('observed with ')[1].split('?')[0]
            query = 'SELECT * FROM datasets WHERE (status = "observed" or \
status = "reduced" or status = "published") and ((telescope = "' + ti + \
'") or (instrument = "' + ti + '"));'
            scur.execute(query)
            recs = scur.fetchall()
            nobj = len(recs)
            reply = reply + \
                    '{0:d} objects have been observed with '.format(nobj) + \
                    ti + '.'
        elif re.search(commands[3],
                       inquiry,
                       re.I):
            obj = inquiry.split('available for ')[1].split('?')[0]
            query = 'SELECT * FROM datasets WHERE name = "' + obj + \
'" and (status = "observed" or status = "reduced" or status = "published");'
            scur.execute(query)
            recs = scur.fetchall()
            nobs = len(recs)
            if nobs == 0:
                reply = 'There are no datasets available for ' + obj + '.'
            elif nobs == 1:
                reply = obj + \
                        ' has {0:d} available dataset: '.format(nobs) + \
                        ', '.join([entry[0] + '+' + entry[1] for entry in recs])
            else:
                reply = obj + \
                        ' has {0:d} available datasets: '.format(nobs) + \
                        ', '.join([entry[0] + '+' + entry[1] for entry in recs])
        elif re.search(commands[4],
                       inquiry,
                       re.I):
            query = 'SELECT * from observing_runs WHERE end > NOW() ORDER BY start;'
            scur.execute(query)
            recs = scur.fetchall()
            nobs = len(recs)
            if nobs == 0:
                reply = reply + 'There are no upcoming observing runs.'
            elif nobs == 1:
                recs = recs[0]
                reply = reply + 'There is 1 upcoming observing run:\n'
                reply = reply + recs[3].isoformat() + ' to ' + recs[4].isoformat() + ' at ' + \
                        recs[1] + ' with ' + recs[2] + '.'
            elif nobs > 1:
                reply = reply + 'There are {0:d} upcoming observing runs:\n'.format(nobs)
                for i in range(nobs):
                    reply = reply + recs[i][3].isoformat() + ' to ' + recs[i][4].isoformat() + ' at ' + \
                            recs[i][1] + ' with ' + recs[i][2] + '.\n'
        elif re.search('list commands',
                       inquiry,
                       re.I) or \
             re.search('help',
                       inquiry,
                       re.I):
            reply = reply + 'I have the following commands:\n'
            reply = reply + commands[0] + '\n'
            reply = reply + commands[1] + '\n'
            reply = reply + commands[-1] + '\n'
            for i in range(2, len(commands)-1):
                reply = reply + commands[i] + ' _____?\n'
            reply = reply + '\nDon\'t forget to prefix your request with \"@databot\"!'
        elif re.search("kill",
                       inquiry,
                       re.I):
            reply = "Leaving."
        elif re.search("what is your name",
                       inquiry,
                       re.I):
            reply = "I am @databot of Camalot."
        elif re.search("what is your quest",
                       inquiry,
                       re.I):
            reply = "To seek the Holy Grail."
        elif re.search("what is the airspeed velocity of an unladen swallow",
                       inquiry,
                       re.I):
            reply = "African or European?"
        elif re.search("what is your favorite color",
                       inquiry,
                       re.I):
            reply = "Blue"
        else:
            reply = "I'm sorry, I don't understand what you're asking. Type: \"@databot help\" or \"@databot list commands\"."
        sc.api_call("chat.postMessage",
                    channel=msg['channel'],
                    text=reply,
                    as_user=True)

        if re.search("kill",
                     inquiry,
                     re.I):
            shutdown()
            sys.exit(0)


if __name__ == "__main__":
    config = configparser.RawConfigParser()
    if os.path.isfile('slackbot.cfg'):
        config.read('slackbot.cfg')
    else:
        sys.stderr.write('Cannot find slackbot.cfg. Exiting.\n')
        sys.exit(0)
    APIkey = config.get('Slack', 'APIkey')
    SQLdb = config.get('SQL', 'DB')
    SQLserver = config.get('SQL', 'server')
    SQLuser = config.get('SQL', 'user')
    SQLpass = config.get('SQL', 'pass')

    scon = MySQLdb.connect(host=SQLserver,
                           user=SQLuser,
                           passwd=SQLpass,
                           db=SQLdb)
    scur = scon.cursor()

    dcount = 0

    sc = SlackClient(APIkey)
    if sc.rtm_connect():
        sys.stdout.write("@databot is connected to slack. Listening...\n")
        while True:
            try:
                slackmsg = sc.rtm_read()
                # only count retries between successful disconnections
                dcount = 0
                if slackmsg != []:
                    handlemsg(slackmsg)
                time.sleep(0.2)
            except:
                dcount = dcount + 1
                sys.stderr.write('We are not connected.')
                sys.stderr.write(' Sleeping for 10 seconds and reconnecting.')
                sys.stderr.write(' {0:1d} retries to connect.\n'.format(dcount))
                time.sleep(10)
                sc = SlackClient(APIkey)
                sc.rtm_connect()
    else:
        sys.stderr.write("Error: could not connect to slack. Exiting.\n")
