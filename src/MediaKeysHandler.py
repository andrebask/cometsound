##
#    Project: CometSound - A Music player written in Python 
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

import dbus.mainloop.glib

class MediaKeys():
    """Handles the multimedia keys using dbus, requires Gnome and dbus"""
    
    def __init__(self, control):
        
        self.actions = {'Play': control.playStopSelected,
                         'Next': control.nextTrack,
                          'Previous': control.previousTrack}
        
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
        self.gsettingsDaemon = self.bus.get_object(
            'org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')
 
        self.gsettingsDaemon.GrabMediaPlayerKeys(
            'CometSound', 0, dbus_interface='org.gnome.SettingsDaemon.MediaKeys')
 
        self.gsettingsDaemon.connect_to_signal(
            'MediaPlayerKeyPressed', self.onMediaKey)
        
    def onMediaKey(self, application, mmkey):
        """Executes the action associated to the media key"""   
        if application == 'CometSound':
            try:
                self.actions[mmkey]()
            except:
                return