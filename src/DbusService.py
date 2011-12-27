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

import dbus, dbus.service

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