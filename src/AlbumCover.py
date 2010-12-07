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

import gtk, urllib , os, time, pynotify
from multiprocessing import Process
from HTMLParser import HTMLParser
from AF import AudioFile

cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")

class AlbumImage(gtk.Image):
    
    def __init__(self):
        gtk.Image.__init__(self)
        self.setDefaultCover()
    
    def updateImage(self, widget = None, event = None):
        pathFile = os.path.join(cacheDir, 'tmp', 'coverpath')
        FILE = open(pathFile,'r')
        lines = []
        for line in FILE:
            lines.append(line[:-1]) 
        FILE.close()
        coverFile = lines[0]
        tmpImage = gtk.Image()
        tmpImage.set_from_file(coverFile)
        try:
            pix = tmpImage.get_pixbuf().scale_simple(115, 115, gtk.gdk.INTERP_BILINEAR)
            self.set_from_pixbuf(pix)
        except:
            return
        
    def setDefaultCover(self):
        self.set_from_file(os.path.join(cacheDir, 'tmp', 'default.jpg'))
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


notification = pynotify.Notification(' ',' ')                        
class CoverDownloader(Process):
    def __init__(self, filename):
        Process.__init__(self)
        self.cover = None
        index = filename.rfind("/")    
        directory = filename[:index]
        filename = filename[index+1:]
        af = AudioFile(directory, filename)
        self.directory = directory
        self.title = af.getTagValue('title')
        self.album = af.getTagValue('album')
        self.artist = af.getTagValue('artist')
        self.start()
        
    def run(self):
        if not self.getLocalCover():
            self.downloadCover(self.artist, self.album)
        notification.update(self.title, "%s\n%s" % (self.album, self.artist), self.cover)
        notification.show()
                
    def write(self, cover):
        dir = os.path.join(cacheDir, 'tmp')
        if not os.path.exists(dir):
            os.makedirs(dir)
        pathFile = os.path.join(dir, 'coverpath')
        FILE = open(pathFile,'w')
        FILE.write(cover + '\n')
        FILE.close()
    
    def getLocalCover(self):            
        images = [file for file in os.listdir(self.directory) if file.split('.')[-1].lower() in ['jpg', 'jpeg', 'png']]
        if len(images) > 0:
            self.cover = os.path.join(self.directory, images[0])
            self.write(self.cover)
            return True
        else:
            self.cover = os.path.join(cacheDir, 'tmp', 'cover.jpg')
            self.write(self.cover)
            return False
                            
    def downloadCover(self, artist, album):
        artist = artist.replace(' ', '+')
        album = album.replace(' ', '+')
        link = 'http://www.last.fm/music/%s/%s' % (artist, album)
        parser = CoverParser()
        try:
            sock = urllib.urlopen(link)
            parser.feed(sock.read(5000))
            sock.close()
            parser.close()
        except:
            pass
        if parser.image == None:
            self.write(os.path.join(cacheDir, 'tmp', 'default.jpg'))
            return
        tmpPath = os.path.join(cacheDir, 'tmp')
        if not os.path.exists(tmpPath):
            os.makedirs(tmpPath)
        cover = os.path.join(tmpPath,'cover.jpg')
        urllib.urlretrieve(parser.image, cover)
        self.cover = cover