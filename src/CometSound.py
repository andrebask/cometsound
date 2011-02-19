##
#    Project: CometSound - A music player written in Python 
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010 Andrea Bernardini
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

import AF, cerealizer, gtk, fcntl, sys, os, dbus, dbus.service, dbus.glib
import mutagen.asf as mtgasf
cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")  
from Model import Model, isAudio
from View import View
from Controller import Controller
    
def registerClasses():
    cerealizer.register(AF.AudioFileInfos)            

def getArg():
    if len(sys.argv) > 1 and sys.argv[1] != '':
        dir = sys.argv[1]
        if dir[0] != '/':
            dir = os.path.join(os.environ.get('HOME', None), dir)
    else:
        dir = ''
    return dir

dir = os.path.join(os.environ.get('HOME', None), '.CometSound')
pidFile = os.path.join(dir, 'program.pid') 
if not os.path.exists(dir):
    os.makedirs(dir)
fp = open(pidFile, 'w')
try:
    fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print 'CometSound is already running'
    if isAudio(getArg()):
        addTrack = dbus.SessionBus().get_object('com.thelinuxroad.CometSound', '/com/thelinuxroad/CometSound').get_dbus_method("addTrack")
        addTrack(getArg())
    sys.exit(0)

class DbusService(dbus.service.Object):
    def __init__(self, control):
        self.control = control
        busName = dbus.service.BusName('com.thelinuxroad.CometSound', bus = dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/com/thelinuxroad/CometSound')

    @dbus.service.method(dbus_interface='com.thelinuxroad.CometSound')
    def addTrack(self, cfname):
        self.control.dbusPlay(cfname)


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
