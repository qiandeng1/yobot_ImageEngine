import configparser
from pathlib import Path
import os
import sys

ginipath = Path.cwd().resolve().joinpath("./yobot_data/groups.ini") if "_MEIPASS" in dir(sys) else Path(os.path.dirname(__file__)).parents[2] / 'yobot_data' / 'groups.ini'
config = configparser.ConfigParser()
config.read(str(ginipath),  encoding='utf-8')


def who_am_i(GID):
    '''Gimme a GID(int), return you a selfID(int) :)'''
    # config = configparser.ConfigParser()
    # config.read(str(ginipath))
    global config
    sid = config.get('GROUPS', str(GID))
    return int(sid)


def refresh():
    global config
    config.read(str(ginipath), encoding='utf-8')
