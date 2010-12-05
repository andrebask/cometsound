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

import gtk, urllib , os, time
from HTMLParser import HTMLParser
from CometSound import cacheDir
#from threading import Thread


class AlbumImage(gtk.Image):
    
    def __init__(self):
        gtk.Image.__init__(self)
        self.setDefaultCover()
    
    def setDefaultCover(self):
        self.set_from_file(os.path.join(cacheDir, 'tmp', 'default.jpg'))
        pix = self.get_pixbuf().scale_simple(115, 115, gtk.gdk.INTERP_BILINEAR)
        self.set_from_pixbuf(pix)
            
    def update(self, artist, album):
        artist = artist.replace(' ', '+')
        album = album.replace(' ', '+')
        link = 'http://www.last.fm/music/%s/%s' % (artist, album)
        sock = urllib.urlopen(link)
        parser = CoverParser()
        try:
            parser.feed(sock.read(5000))
            sock.close()
            parser.close()
        except:
            pass
        if parser.image == None:
            self.setDefaultCover()
            return
        tmpPath = os.path.join(cacheDir, 'tmp')
        if not os.path.exists(tmpPath):
            os.makedirs(tmpPath)
        cover = os.path.join(tmpPath,'cover.jpg')
        urllib.urlretrieve(parser.image, cover)
        self.set_from_file(cover)
        pix = self.get_pixbuf().scale_simple(115, 115, gtk.gdk.INTERP_BILINEAR)
        self.set_from_pixbuf(pix)
        
class CoverParser(HTMLParser):
    image = None
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            if ('property', 'og:image') in attrs:
                for (att, val) in attrs:
                    if att == 'content':
                        self.image = val

#class CoverUpdater(Thread):
#    
#    def __init__(self, artist, album, albumImage):
#        Thread.__init__(self)
#        self.albumImage = albumImage
#        self.artist = artist
#        self.album = album
#        
#    def run(self):
#        self.albumImage.update(self.artist, self.album)
