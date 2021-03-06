# Data Bot

A Slack bot to provide information on aspects of the Dual AGN project.

## Features

The bot queries a local MySQL database which has been populated with information about the project.
Note that not all of the information contained within the database is accessible through the bot.

### Current

- Query which targets have been observed with specific instruments.
- Query which observations have been taken for a specific target.
- Return some information on future observing runs.

### Wishlist

- Some information about the status of reductions.

## Dependencies

* python2 (because python-slackclient does not yet support python 3).
* [MySQL-python](https://pypi.python.org/pypi/MySQL-python/) for python 2.X
- [python-slackclient](https://github.com/slackhq/python-slackclient)
