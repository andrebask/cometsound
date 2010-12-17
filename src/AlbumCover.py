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

import gtk, urllib , os, time, pynotify, setproctitle as spt
from multiprocessing import Process, Manager
from HTMLParser import HTMLParser
from AF import AudioFile

cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")

manager = Manager()
Global = manager.Namespace()
Global.cover = None
Global.stop = False
Global.coverChanged = False
Global.filename = ''

class AlbumImage(gtk.Image):
    
    def __init__(self):
        gtk.Image.__init__(self)
        self.setDefaultCover()
        
    def updateImage(self, widget = None, event = None):
        if Global.coverChanged:
            coverFile = Global.cover
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

class NotifyUpdate(Process):
    def __init__(self):
        Process.__init__(self)
        self.notify = pynotify.Notification(' ',' ')
        self.start()
        
    def run(self):
        spt.setproctitle('CometSound Notifier')
        try:
            while not Global.stop:
                time.sleep(0.5)
                if Global.coverChanged:
                    self.update()
                    Global.coverChanged = False
        except:
            return
           
    def update(self):
        filename = Global.filename
        index = filename.rfind("/")    
        directory = filename[:index]
        filename = filename[index+1:]
        af = AudioFile(directory, filename)
        self.directory = directory
        title = af.getTagValue('title')
        album = af.getTagValue('album')
        artist = af.getTagValue('artist')
        self.notify.update(title, "%s\n%s" % (album, artist), Global.cover)
        self.notify.show()

class CoverUpdater(Process):
    def __init__(self, filename):
        Process.__init__(self)
        self.stop = False
        self.filename = filename
        self.start()
        
    def run(self):
        spt.setproctitle('CS Cover Finder')
        filename = self.filename
        index = filename.rfind("/")    
        directory = filename[:index]
        filename = filename[index+1:]
        af = AudioFile(directory, filename)
        self.directory = directory
        self.album = af.getTagValue('album')
        self.artist = af.getTagValue('artist')
        if not self.getLocalCover():
            self.downloadCover(self.artist, self.album)  
        Global.filename = self.filename
        Global.coverChanged = True
        
    def getLocalCover(self):            
        images = [file for file in os.listdir(self.directory) if file.split('.')[-1].lower() in ['jpg', 'jpeg', 'png']]
        if len(images) > 0:
            Global.cover = os.path.join(self.directory, images[0])
            return True
        else:
            Global.cover = os.path.join(cacheDir, 'tmp', 'cover.jpg')
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
            Global.cover = os.path.join(cacheDir, 'tmp', 'default.jpg')
            return
        tmpPath = os.path.join(cacheDir, 'tmp')
        if not os.path.exists(tmpPath):
            os.makedirs(tmpPath)
        Global.cover = os.path.join(tmpPath,'cover.jpg')
        urllib.urlretrieve(parser.image, Global.cover)
        