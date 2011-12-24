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

from AF import AudioFile
from threading import Thread
from Queue import Queue

# This api key is assigned to Andrea Bernardini <andrebask@gmail.com>
# if you reuse this code in a different application, please
# register your own api and secret key with last.fm
API_KEY = "ae63b9f4c40a190ca059d5b5170acc69" 
API_SECRET = "3092aec9dfa6e643b1ea910cc12e2e12"

def getArtistTitle(filename):
    index = filename.rfind("/")    
    directory = filename[:index]
    filename = filename[index+1:]
    af = AudioFile(directory, filename)
    return af.getTagValue('artist'), af.getTagValue('title')

try:
    import pylast
    md5 = pylast.md5
    pylastInstalled = True
except:
    def foo(arg):return ''
    md5 = foo
    pylastInstalled = False
    
class Scrobbler():
    """Scrobbler class: Every action is executed in a separated thread"""
    
    def __init__(self, username, password_hash):
        self.connected = False
        self.thread = Thread(target=self.__connect, args=(username, password_hash,))
        self.thread.start()
        
    def __connect(self, username, password_hash):
        """Tries to connect to the server"""
        try:
            import pylast
            self.network = pylast.LastFMNetwork(api_key = API_KEY, 
                                                     api_secret = API_SECRET, 
                                                     username = username, 
                                                     password_hash = password_hash)
            self.session_key = pylast.SessionKeyGenerator(self.network).get_session_key(username, password_hash)
            self.connected = True
        except:
            self.connected = False
    
    def nowPlaying(self, (cfname, title, album, artist)):
        if self.connected:
            t = Thread(target=self.__nowPlaying, args=(artist, title,))
            t.start()
        
    def __nowPlaying(self, a, t):
        self.thread.join()
        self.network.update_now_playing(a, t)
    
    def scrobble(self, (cfname, title, album, artist), timestamp):
        if self.connected:
            t = Thread(target=self.__scrobble, args=(artist, title, timestamp,))
            t.start()
        
    def __scrobble(self, a, t, timestamp):
        self.thread.join()
        self.network.scrobble(a, t, timestamp)
    
    def love(self, (cfname, title, album, artist)):
        if self.connected:
            t = Thread(target=self.__love, args=(artist, title,))
            t.start()
        
    def __love(self, a, t):
        self.thread.join()
        track = self.network.get_track(a, t)
        track.love()
        