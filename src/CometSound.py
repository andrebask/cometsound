##
#    Project: CometSound - A music player written in Python 
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010-2011 Andrea Bernardini
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

import AF, cerealizer, gtk, fcntl, sys, os, dbus, dbus.service, dbus.glib, time
import mutagen.asf as mtgasf
cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")  
from Model import Model, isAudio
from View import View
from Controller import Controller

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

#Controls if the program is already running
#Is allowed a single instance
dir = os.path.join(os.environ.get('HOME', None), '.CometSound')
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
            addTrack = dbus.SessionBus().get_object('com.thelinuxroad.CometSound', '/com/thelinuxroad/CometSound').get_dbus_method("addTrack")
            addTrack(arg)        
    play = dbus.SessionBus().get_object('com.thelinuxroad.CometSound', '/com/thelinuxroad/CometSound').get_dbus_method("play")
    play()
    sys.exit(0)

class DbusService(dbus.service.Object):
    """Dbus service class to send commands to CometSound from other programs"""
    def __init__(self, control):
        self.control = control
        busName = dbus.service.BusName('com.thelinuxroad.CometSound', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/com/thelinuxroad/CometSound')

    @dbus.service.method(dbus_interface='com.thelinuxroad.CometSound')
    def play(self):
        self.control.dbusPlay()
     
    @dbus.service.method(dbus_interface='com.thelinuxroad.CometSound')    
    def addTrack(self, cfname):
        self.control.dbusAddTrack(cfname)

#Gives a Name to the main process
import setproctitle as spt
spt.setproctitle('CometSound')
        
def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    registerClasses()
    m = Model(getArg())
    c = Controller(m)
    View(m, c)
    DbusService(c)
    main()     
