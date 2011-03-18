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

from AF import AudioFile
from threading import Thread
from Queue import Queue

API_KEY = "" 
API_SECRET = ""

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
    
    def __init__(self, username, password_hash):
        self.connected = False
        self.thread = Thread(target=self.__connect, args=(username, password_hash,))
        self.thread.start()
        
    def __connect(self, username, password_hash):
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
    
    def nowPlaying(self, filename):
        if self.connected:
            t = Thread(target=self.__nowPlaying, args=(filename,))
            t.start()
        
    def __nowPlaying(self, filename):
        self.thread.join()
        a, t = getArtistTitle(filename)
        self.network.update_now_playing(a, t)
    
    def scrobble(self, filename, timestamp):
        if self.connected:
            t = Thread(target=self.__scrobble, args=(filename, timestamp,))
            t.start()
        
    def __scrobble(self, filename, timestamp):
        self.thread.join()
        a, t = getArtistTitle(filename)
        self.network.scrobble(a, t, timestamp)
    
    def love(self, filename):
        if self.connected:
            t = Thread(target=self.__love, args=(filename,))
            t.start()
        
    def __love(self, filename):
        self.thread.join()
        a, t = getArtistTitle(filename)
        track = self.network.get_track(a, t)
        track.love()
        