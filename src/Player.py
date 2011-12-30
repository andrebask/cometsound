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

from Common import gtk
from Common import gobject
from Common import gst
from Common import threading
from Common import os
from Common import random
from Common import time
from Common import Global
from Common import Queue

from AlbumCover import CoverUpdater
from AlbumCover import NotifyUpdater
from Scrobbler import Scrobbler

class PlayerThread(threading.Thread):
    """Thread that manages all the player's operations"""
    
    def __init__(self, playlist, control):
        threading.Thread.__init__(self)
        self.playlist = playlist
        self.control = control
        s = self.control.settings
        self.scrobbler = Scrobbler(s['user'], s['pwdHash'])
        self.timestamp = int(time.time())
        self.queue = Queue()
        self.shuffle = False  
        self.repeat = False
        self.shuffleList = []
        self.player = None
        self.playing = False
        self.played = 0
        self.started = False
        self.updater = CoverUpdater()
        self.labelUpdated = False
        self.notify = NotifyUpdater()
        self.trackNum = -1        
        self.__createPlayer()
        self.stopevent = threading.Event()
        self.start()
    
    def isStarted(self):
        return self.started
    
    def __createPlayer(self):
        """Creates and prepares the Gstreamer play bin"""
        self.player = gst.element_factory_make("playbin2", "player")
        try:
            sink = gst.element_factory_make(self.control.settings['audiosink'], "output")
        except:
            print 'Audio output not found, using gstreamer default sink'
            sink = gst.element_factory_make('autoaudiosink', "output")    
        self.player.set_property("audio-sink", sink)
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.onMessage)    
        self.player.connect("about-to-finish", self.onFinish)    
        
    def setPlaylist(self, playlist):
        self.playlist = playlist
        self.control.playlist = self.playlist
        
    def clearPlaylist(self):
        """Removes all the files from the playlist"""
        if self.started:
            self.playlist = [self.playlist[self.getNum()]]
            self.trackNum = 0
        if self.control.view.slider.get_value() == 0:
            self.playlist = []
        self.control.playlist = self.playlist
            
    def run(self):
        """Starts the thread"""
        while not self.stopevent.isSet():  
            time.sleep(0.1)
            try:  
                Global.filename = self.queue.get_nowait()
                Global.trackChanged = True
            except:
                pass
        gtk.main_quit()
    
    def go(self):
        """Start"""
        self.started = True
        self.setTimeout()
        self.next()
    
    def setTimeout(self):
        self.timeoutID = gobject.timeout_add(100, self.control.updateSlider)
                
    def onMessage(self, bus, message):
        """Handles the change of streaming, 
           updating the label or calling the stop() method
            to shut down the player at the end of playback"""
        t = message.type
        if t == gst.MESSAGE_ELEMENT and self.playing:
            if self.trackNum > -1 and self.started:
                self.queue.put(self.playlist[self.getNum()])
                self.labelUpdated = True
            self.updateGUI()
        elif t == gst.MESSAGE_NEW_CLOCK:
            if not self.labelUpdated:
                self.queue.put(self.playlist[self.getNum()])
                self.labelUpdated = False
        elif t == gst.MESSAGE_EOS:
            self.trackNum = 0 
            self.stop()
            self.updatePlaylist()
            self.labelUpdated = False
            self.player.set_property("uri", "file://" + self.playlist[0][0])
        elif t == gst.MESSAGE_ERROR:
            self.stop()
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
    
    def updatePlaylist(self):
        gobject.idle_add(self.control.updatePlaylistSafe, self.playing, self.getNum())
                
    def updateGUI(self):
        """Updates the GUI when the playing track changes"""
        p = self.playing
        num = self.getNum()
        gobject.idle_add(self.control.updatePlaylistSafe, p, num)
        gobject.idle_add(self.control.updateLabel, self.playlist[num], p)
        if self.control.settings['scrobbler']:
            self.scrobbler.nowPlaying(self.playlist[self.getNum()])
            self.timestamp = str(int(time.time()))
            self.scrobbled = False
            self.played = 0
        
    def onFinish(self, player):
        """Handles the end of a stream, 
           preparing the player to play an other track"""
        if self.trackNum < len(self.playlist)-1 or self.shuffle:
            self.trackNum += 1
            num = self.getNum()
            player.set_property("uri", "file://" + self.playlist[num][0])   
        elif self.repeat:
            self.trackNum = 0
            num = self.getNum()
            player.set_property("uri", "file://" + self.playlist[num][0])  
            
    def pause(self, button = True):
        """Pauses playing"""
        self.playing = False
        self.player.set_state(gst.STATE_PAUSED)
        if button:
            self.control.view.setButtonPlay()
            self.updatePlaylist()
            
    def play(self):
        """Starts playing"""
        self.playing = True
        self.control.view.setButtonPause()
        self.updatePlaylist()
        self.player.set_state(gst.STATE_PLAYING)
        
    def stop(self):
        """Stops playing"""
        self.playing = False
        self.player.set_state(gst.STATE_NULL)   
        self.control.resetSlider()
        self.control.view.setButtonPlay()
        self.control.updateLabel((None, None, None, None))
        
    def next(self, notify = True):
        """Starts playing of the next track in the playlist"""
        if self.trackNum < len(self.playlist)-1:
            self.trackNum += 1
            num = self.getNum()
            self.stop()
            if os.path.isfile(self.playlist[num][0]):
                self.player.set_property("uri", "file://" + self.playlist[num][0])
                self.play()
        elif self.repeat:
            self.trackNum = -1
            self.next()   
        
    def previous(self, notify = True):
        """Starts playing of the previous track in the playlist"""
        self.trackNum -= 1
        try:
            num = self.getNum()
        except:
            num = -1
        if num > -1:
            self.stop()  
            if os.path.isfile(self.playlist[num][0]):
                self.player.set_property("uri", "file://" + self.playlist[num][0])
                self.play()
        else:
            self.trackNum += 1   
    
    def getNum(self):
        """Returns the correct track number according to the self.shuffle state"""
        if self.shuffle:
            num = self.trackNum
            if self.trackNum == len(self.playlist)-1:
                self.trackNum = -1             
            return self.shuffleList[num]
        else:
            return self.trackNum
    
    #Scrobbling methods
    def love(self, o):
        self.scrobbler.love(self.playlist[self.getNum()])
        
    def scrobble(self):
        if not self.scrobbled:
            self.scrobbler.scrobble(self.playlist[self.getNum()], self.timestamp)
            self.scrobbled = True
    ######
       
    def setRand(self):
        """Creates a random playback order"""
        self.trackNum = -1
        options = range(len(self.playlist))
        random.shuffle(options)
        self.shuffleList = options
    
    def getVolume(self):
        return self.player.get_property('volume')
        
    def onSliderChange(self, slider):
        """Handles the position changes of the slider"""
        seekTimeSecs = slider.get_value()
        self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | 
                                gst.SEEK_FLAG_KEY_UNIT, seekTimeSecs * gst.SECOND)
    
    def onVolumeChanged(self, widget, value=0.5):
        """Handles the position changes of the volume control"""
        self.player.set_property('volume', float(value))
        return True
    
    def terminate(self, timeout=None):
        """Terminates the thread"""
        self.stopevent.set()
        threading.Thread.join(self)
