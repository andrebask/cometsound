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

import threading, os, gst, gtk, gobject, random, pynotify
from AlbumCover import CoverUpdater, NotifyUpdate

class PlayerThread(threading.Thread):
    """Thread that manages all the player's operations"""
    
    def __init__(self, playlist, control):
        threading.Thread.__init__(self)
        self.playlist = playlist
        self.control = control
        self.shuffle = False  
        self.repeat = False
        self.shuffleList = []
        self.player = None
        self.playing = False
        self.started = False
        self.labelUpdated = False
        self.notify = NotifyUpdate()
        self.trackNum = -1        
        self.__createPlayer()
        self.stopevent = threading.Event()
    
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
        self.started = True
        self.setTimeout()
        self.control.view.slider.set_sensitive(True)
        self.next()
        while not self.stopevent.isSet():    
            self.stopevent.wait(2)
        gtk.main_quit()
    
    def setTimeout(self):
        self.timeoutID = gobject.timeout_add(100, self.control.updateSlider)
                
    def onMessage(self, bus, message):
        """Handles the change of streaming, 
           updating the label or calling the stop() method
            to shut down the player at the end of playback"""
        t = message.type
        if t == gst.MESSAGE_ELEMENT and self.playing:
            if self.trackNum > -1 and self.started:
                self.control.updateLabel(self.playlist[self.getNum()], self.playing)
                CoverUpdater(self.playlist[self.getNum()])
                self.labelUpdated = True
            self.control.updatePlaylist()
        elif t == gst.MESSAGE_EOS:
            self.trackNum = 0 
            self.control.updatePlaylist()
            self.stop()
            self.player.set_property("uri", "file://" + self.playlist[0])
        elif t == gst.MESSAGE_ERROR:
            self.stop()
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
        elif t == gst.MESSAGE_NEW_CLOCK:
            if not self.labelUpdated:
                self.control.updateLabel(self.playlist[self.getNum()], self.playing)
                CoverUpdater(self.playlist[self.getNum()])
                self.labelUpdated = False

    def onFinish(self, player):
        """Handles the end of a stream, 
           preparing the player to play an other track"""
        if self.trackNum < len(self.playlist)-1 or self.shuffle:
            self.trackNum += 1
            num = self.getNum()
            player.set_property("uri", "file://" + self.playlist[num])   
        elif self.repeat:
            self.trackNum = 0
            num = self.getNum()
            player.set_property("uri", "file://" + self.playlist[num])  
            
    def pause(self, button = True):
        """Pauses playing"""
        self.playing = False
        self.player.set_state(gst.STATE_PAUSED)
        if button:
            self.control.view.setButtonPlay()
            self.control.updatePlaylist()
            
    def play(self):
        """Starts playing"""
        self.playing = True
        self.player.set_state(gst.STATE_PLAYING)
        self.control.view.setButtonPause()
        self.control.updatePlaylist()
        
    def stop(self):
        """Stops playing"""
        self.playing = False
        self.player.set_state(gst.STATE_NULL)   
        self.control.resetSlider()
        self.control.view.setButtonPlay()
        self.control.updateLabel(None)
        
    def next(self, notify = True):
        """Starts playing of the next track in the playlist"""
        if self.trackNum < len(self.playlist)-1:
            self.trackNum += 1
            num = self.getNum()
            self.stop()
            if os.path.isfile(self.playlist[num]):
                self.player.set_property("uri", "file://" + self.playlist[num])
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
            if os.path.isfile(self.playlist[num]):
                self.player.set_property("uri", "file://" + self.playlist[num])
                self.play()
        else:
            self.trackNum += 1   
    
    def getNum(self):
        if self.shuffle:
            num = self.trackNum
            if self.trackNum == len(self.playlist)-1:
                self.trackNum = -1             
            return self.shuffleList[num]
        else:
            return self.trackNum
        
    def setRand(self):
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
