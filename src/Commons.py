##
#    Project: CometSound - A music player written in Python
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010-2012 Andrea Bernardini
#    License: GPL-2+
#
#    This file is part of CometSound.
#
#    CometSound is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    CometSound is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with CometSound.  If not, see <http://www.gnu.org/licenses/>.
##

import gtk
#gtk.threads_init()

import pygtk
pygtk.require('2.0')

import gobject
gobject.threads_init()

import pango
import gst

import threading

import os
import sys
import stat
import time
import fcntl
import urllib
import commands
import setproctitle

import string
import random


import pynotify
import cerealizer

import dbus

import locale
import gettext

import SortFunctions
import AF

from threading import Thread, Lock, Event
from multiprocessing import Manager, cpu_count
from HTMLParser import HTMLParser
from Queue import Queue

from Translator import t

APP_VERSION = '0.4'
APP_NAME = "cometsound"

_ = t.getTranslationFunc()

cacheDir = os.path.join(os.environ.get('HOME', None), ".cometsound")

defaultSettings = {'audiosink': 'autoaudiosink',
                    'statusicon': 0,
                    '#': True,
                     _('Title'): True,
                     _('Artist'): True,
                      _('Album'): True,
                       _('Genre'): True,
                        _('Year'): True,
                        'lastplaylist': True,
                        'foldercache': True,
                        'scrobbler': False,
                        'user': '',
                        'pwdHash': '',
                        'fakepwd': '',
                        'view': 0,
                        'libraryMode': True,
                        'libraryFolder': os.environ.get('HOME', None),
                        'notify': True
                         }

def readSettings():
    """Loads the settings from the settings file"""
    try:
        FILE = open(os.path.join(cacheDir, 'settings'),'rb')
        settings = cerealizer.load(FILE)
        FILE.close()
        for key in defaultSettings:
            if key not in settings:
                settings = defaultSettings
                return
    except:
        #print sys.exc_info()
        settings = defaultSettings
    return settings

def gtkTrick():
    while gtk.events_pending():
        gtk.main_iteration()

def registerClasses():
    """Registers the classes to serialize"""
    cerealizer.register(AF.AudioFileInfos)

def getArg():
    """Gets the arguments passed to the program"""
    list = []
    if len(sys.argv) > 1 and sys.argv[1] != '':
        for dir in sys.argv[1:]:
            if dir[0] != '/':
                dir = os.path.join(os.environ.get('COMETSOUND_DIR', None), dir)
            list.append(dir)
    else:
        list.append('')
    return list

audioTypes = ['.mp3', '.wma', '.ogg', '.flac',
            '.m4a', '.mp4', '.aac', '.wav',
             '.ape', '.mpc', '.wv']

def isAudio(fileName):
    i = fileName.rfind('.')
    ext = string.lower(fileName[i:])
    return ext in audioTypes


#Loading settings
settings = readSettings()

# The Manager is used to exchange information between threads
manager = Manager()
Global = manager.Namespace()
Global.cover = None
Global.stop = False
Global.trackChanged = False
Global.coverChanged = False
Global.notificationChanged = False
Global.filename = ()
Global.albumArtist = '', ''
Global.PBcount = 0
Global.scanCount = 0
globalLock = Lock()

cpunum = cpu_count()

def writeSettings(newsettings):
    """Stores the settings to a file serializing the settings dict"""
    dir = cacheDir
    if not os.path.exists(dir):
        os.makedirs(dir)
    cachefile = os.path.join(dir, 'settings')
    FILE = open(cachefile,'w')
    cerealizer.dump(newsettings, FILE)
    FILE.close()
    settings = newsettings

#Controls if the program is already running
#Is allowed a single instance
dir = os.path.join(os.environ.get('HOME', None), '.cometsound')
pidFile = os.path.join(dir, 'program.pid')
if not os.path.exists(dir):
    os.makedirs(dir)
fp = open(pidFile, 'w')
try:
    fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print 'CometSound is already running'
    time.sleep(1)
    for arg in getArg():
        if isAudio(arg):
            addTrack = dbus.SessionBus().get_object('com.thelinuxroad.cometsound', '/com/thelinuxroad/CometSound').get_dbus_method("addTrack")
            addTrack(arg)
    if len(getArg()) == 1:
        if getArg()[0]=='':
            sys.exit(0)
    play = dbus.SessionBus().get_object('com.thelinuxroad.cometsound', '/com/thelinuxroad/CometSound').get_dbus_method("play")
    play()
    sys.exit(0)
