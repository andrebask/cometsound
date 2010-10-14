##
#    Project: CometSound - A Music player written in Python 
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

import gtk, os, pwd, AF, Model, gst, threading, gobject, pynotify, cerealizer, random

class Controller:
    """This Class Handles the interactions between the GUI(View) and the Model"""
    folder = ''
    
    def __init__(self, model):
        self.model = model
        self.playlist = []
        self.playerThread = PlayerThread(self.playlist, self)
        self.position = 0
        self.duration = 0
        try:
            self.folder = self.model.getOldDir()
        except:
            self.folder = "/home/" + pwd.getpwuid(os.getuid())[0] + "/"
            
    def registerView(self,view):
        """Connects the View to the Controller"""
        self.view = view
        
    def openFolder(self, o):
        """Creates the dialog window that permits to choose the folder to scan"""
        old = self.folder
        self.__openDialog()
        if old != self.folder:
            if os.stat(self.folder).st_uid == os.getuid():
                self.__reBuildViewTree()
        else:
            try:
                self.view.vbox.remove(self.view.progressBar) 
            except:
                pass
            
    def __openDialog(self):
        folderChooser = gtk.FileChooserDialog('Select Folder...', None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        folderChooser.set_current_folder(self.folder)
        folderChooser.set_default_response(gtk.RESPONSE_OK)
        response = folderChooser.run()
        if response == gtk.RESPONSE_OK:
            self.view.vbox.pack_start(self.view.progressBar, False)
            self.view.show_all()
            self.folder = folderChooser.get_current_folder()
            folderChooser.hide()
        else:
            folderChooser.hide()    
        while gtk.events_pending():
            gtk.main_iteration()    
    
    def __reBuildViewTree(self):
        """Creates a new Model using the current folder"""
        self.model = Model.Model(self.folder, self.view.progressBar)
        dir = "/home/" + pwd.getpwuid(os.getuid())[0] + "/.CometSound/"
        if not os.path.exists(dir):
            os.makedirs(dir)
        cachefile = dir + "cache"
        FILE = open(cachefile,'w')
        cerealizer.dump(self.model.getAudioFileList(), FILE)
        FILE.close()
        self.__refreshViewTree()
        self.view.vbox.remove(self.view.progressBar)
        
    def __refreshViewTree(self): 
        """Refreshes the treeview"""  
        self.view.filesTree.setModel(self.model)
    
    def refreshTree(self, widget):
        self.view.vbox.pack_start(self.view.progressBar, False)
        self.view.show_all()
        self.__reBuildViewTree()
            
    def toggle(self, cell, path, rowModel, cfnameList = None):
        """Adds or removes the selected files to the playlist and updates the treeview"""
        completeFilename = rowModel[path][8]
        if cfnameList != None:
            try:
                cfnameList.index(completeFilename)
                found = True
            except ValueError:
                found = False    
        else:
            found = True       
        if found:
            rowModel[path][7] = not rowModel[path][7]
            toggled = rowModel[path][7]
            self.__addRemove(toggled, completeFilename)
        self.__recursiveToggle(path, rowModel, cfnameList)
        self.updatePlaylist()
        
    def __recursiveToggle(self, path, rowModel, cfnameList = None):
        i=0
        rowexists = True
        while True:
            try:
                completeFilename = rowModel[path + (":%d" % (i))][8]
                if cfnameList != None:
                    try:
                        cfnameList.index(completeFilename)
                        found = True
                        deleteMode = True
                    except ValueError:
                        found = False    
                else:
                    found = True
                    deleteMode = False       
                if found:
                    rowModel[path + (":%d" % (i))][7] = rowModel[path][7] and not deleteMode
                    toggled = rowModel[path + (":%d" % (i))][7]
                    self.__addRemove(toggled, completeFilename)   
                self.__recursiveToggle((path + (":%d" % (i))), rowModel, cfnameList)
                i+=1
            except:
                rowexists = False
                #print sys.exc_info()                    
            if not rowexists:
                break
    
    def addAll(self, widget, add):
        """Adds to the playlist all the files of the current folder"""
        rowModel = self.view.filesTree.treeStore
        i=0
        rowexists = True
        while True:
            try:
                path = str(i)
                if rowModel[path][8] != '':
                    rowModel[path][7] = add 
                    toggled = add
                    self.__addRemove(toggled, rowModel[path][8])
                elif rowModel[path][7] != add:
                    self.toggle(None, path, rowModel)  
                i+=1
            except:
                rowexists = False
                #print sys.exc_info()                     
            if not rowexists:
                break
        self.updatePlaylist()
        
    def __addRemove(self, toggled, cfname):
        """Handles the addition and the removal of the files in the playlist"""
        if toggled and cfname != '':
            self.playlist.append(cfname)
        elif cfname != '':
            try:
                if self.playlist[self.playerThread.trackNum] == cfname:
                    if self.playerThread.playing:
                        self.playerThread.next(False)
                        if len(self.playlist) == 1:
                            self.playerThread.stop()
                    else:
                        self.playerThread.next(False)
                        self.playerThread.pause()
                if self.playerThread.trackNum > self.playlist.index(cfname):
                    self.playerThread.trackNum -= 1    
                self.playlist.remove(cfname)                                
            except:
                pass
                #print sys.exc_info()
        
    def doubleClickSelect(self, tree, event):
        """Detects double click on the treeview and updates the selection"""
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.__detectPath(tree, event)
            self.toggle(None, path, tree.get_model())
        
    def doubleClickPlay(self, tree, event):
        """Detects double click on the playlist and play the selected track"""
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.__detectPath(tree, event) 
            if self.playerThread.trackNum == -1:
                self.view.slider.set_sensitive(True)
            self.playerThread.trackNum = int(path) - 1
            if self.playerThread.isAlive():    
                self.playerThread.next()    
            else:
                self.playStopSelected(None)
                
    def __detectPath(self, tree, event): 
        """Determines the path corresponding to the area of the double click"""              
        x = int(event.get_coords()[0])
        y = int(event.get_coords()[1])
        pathinfo = tree.get_path_at_pos(x, y)
        path = ''
        for i in range(len(pathinfo[0])):
            if i == 0:
                sep = ''
            else:
                sep = ':'    
            path = path + sep + str(pathinfo[0][i])
        return path 
    
    def drag(self, treeview, context, selection, target_id, etime):
        """Starts DnD removing the selected file from the playlist"""
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        path = model.get_path(iter)[0]
        self.current = self.playlist[self.playerThread.trackNum]
        self.movedTrack = self.playlist[path]
        self.startIndex = self.playlist.index(self.movedTrack)
        self.playlist.remove(self.playlist[path])       

    def drop(self, treeview, context, x, y, selection, info, etime):
        """"Starts DnD inserting the selected file in the playlist"""
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            if position == gtk.TREE_VIEW_DROP_BEFORE or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
                if self.startIndex > path[0]:
                    i = 0
                else:
                    i = -1    
            elif position == gtk.TREE_VIEW_DROP_AFTER or position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
                if self.startIndex > path[0]:
                    i = 1
                else:
                    i = 0 
            else:
                i = 0    
            index = path[0] + i
            self.playlist.insert(index, self.movedTrack)
        else:
            self.playlist.append(self.movedTrack)
        context.finish(True, True, etime)       
        self.playerThread.trackNum = self.playlist.index(self.current)     
        self.updatePlaylist()
            
    def toggleMp3(self, data):
        """Enables/disables mp3 filtering"""
        self.view.getFormatDict()['.mp3'] = self.view.actiongroup.get_action('Mp3').get_active()
        self.__refreshViewTree()
        return
    
    def toggleWma(self, data):
        """Enables/disables wma filtering"""
        self.view.getFormatDict()['.wma'] = self.view.actiongroup.get_action('Wma').get_active()
        self.__refreshViewTree()
        return
    
    def toggleOgg(self, data):
        """Enables/disables Ogg filtering"""
        self.view.getFormatDict()['.ogg'] = self.view.actiongroup.get_action('Ogg').get_active()
        self.__refreshViewTree()
        return
    
    def playStopSelected(self, o):
        """Handles the click on the Play/Pause button"""
        if self.view.actiongroup.get_action('Play/Stop').get_stock_id() == gtk.STOCK_MEDIA_PLAY:
            if len(self.playlist) > 0:
                if not self.playerThread.is_alive():
                    self.playerThread.setPlaylist(self.playlist)
                    self.playerThread.start()
                    self.playerThread.join(0.1)
                else: 
                    self.playerThread.play()  
        elif self.view.actiongroup.get_action('Play/Stop').get_stock_id() == gtk.STOCK_MEDIA_PAUSE: 
            self.playerThread.pause()            
     
    def nextTrack(self, o):
        """Handles the click on the Next button"""
        self.playerThread.next()
     
    def previousTrack(self, o):
        """Handles the click on the Previous button"""
        self.playerThread.previous()
        
    def updateLabel(self, completefilename, notify = True):
        """Updates the track label with the tags values"""
        t = self.extractTags(completefilename)
        if t['title'] != '' and t['title'] != ' ':
            label = "Title:\t%s\nAlbum:\t%s\nArtist:\t%s" % (t['title'], t['album'], t['artist'])
            winTitle = "%s - %s - %s" % (t['title'], t['album'], t['artist'])
            self.view.label.set_text(label)
            self.view.set_title(winTitle)
            tooltip = label + "\nYear:\t%s\nGenre:\t%s\nNum:\t%s" % (t['year'], t['genre'], t['num'])
            self.view.label.set_tooltip_text(tooltip)
            if notify:
                pynotify.init('label')
                #imageURI = 'file://' + os.path.abspath(os.path.curdir) + '/logo.png'
                n = pynotify.Notification(t['title'], "%s\n%s" % (t['album'], t['artist']))
                n.show()
        else:
            winTitle = t['filename']
            label = "File:\t" + winTitle 
            self.view.label.set_text(label)
            self.view.set_title(winTitle)    
    
    def updatePlaylist(self):
        """Refreshes playlist view"""
        self.view.playlistFrame.listStore.clear()        
        for track in self.playlist:
            
            if self.playlist.index(track) == self.playerThread.trackNum:
                if self.playerThread.playing:
                    icon = gtk.STOCK_MEDIA_PLAY
                else:
                    icon = gtk.STOCK_MEDIA_PAUSE
            else:
                icon = None        
            t = self.extractTags(track)['title']
            if t != '' and t != ' ':
                self.view.playlistFrame.listStore.append([icon, t])             
            else:
                f = self.extractTags(track)['filename']
                self.view.playlistFrame.listStore.append([icon, f])        
    
    def clearPlaylist(self, widget, data=None):
        """Removes all the files from the playlist"""
        #self.addAll(None, False) #slow
        self.view.filesTree.setModel(self.model) #fast
        self.playerThread.clearPlaylist()
        self.updatePlaylist()
    
    def removeSelected(self, widget):
        """Removes only the selected files from the playlist"""
        rowList = self.view.playlistFrame.treeview.get_selection().get_selected_rows()[1]
        cfnameList = []
        for row in rowList:
            cfname = self.playlist[row[0]]
            cfnameList.append(cfname)
            self.__addRemove(False, cfname)        
        rowModel = self.view.filesTree.treeStore
        i=0
        rowexists = True
        while True:
            try:
                path = str(i)
                self.toggle(None, path, rowModel, cfnameList) 
                i+=1
            except:
                rowexists = False
                #print sys.exc_info()        
            if not rowexists:
                break            
        self.updatePlaylist()
            
    def shufflePlaylist(self, widget, data=None):
        """Mixes the songs in the playlist"""
        if self.playerThread.trackNum > -1:
            current = self.playlist[self.playerThread.trackNum]
            random.shuffle(self.playlist)
            self.playlist.remove(current)
            self.playlist.insert(0, current)
            self.playerThread.trackNum = 0
        else:
            random.shuffle(self.playlist)    
        self.updatePlaylist()
    
    def extractTags(self, completefilename):
        """Extracts tags from a given filename.
           Returns a dictionary with the following keys:
           filename, title, artist, album, genre, year, num"""
        index = completefilename.rfind("/")    
        directory = completefilename[:index]
        filename = completefilename[index+1:]
        af = AF.AudioFile(directory, filename)
        title = af.getTagValue('title')
        album = af.getTagValue('album')
        artist = af.getTagValue('artist')
        genre = af.getTagValue('genre')
        year = af.getTagValue('year')
        num = af.getTagValue('num')
        
        return {'filename':filename, 'title':title, 'album':album, 'artist':artist, 'genre':genre, 'year':year, 'num':num }
        
    def updateSlider(self):
        """Updates the slider position on the current playing time"""    
        try:
            positionNanosecs, format = self.playerThread.player.query_position(gst.FORMAT_TIME)
            durationNanosecs, format = self.playerThread.player.query_duration(gst.FORMAT_TIME)

            # block seek handler so we don't seek when we set_value()
            self.view.slider.handler_block_by_func(self.playerThread.onSliderChange)
            
            self.position = float(positionNanosecs) / gst.SECOND
            self.duration = float(durationNanosecs) / gst.SECOND
            
            self.view.slider.set_range(0, self.duration)
            self.view.slider.set_value(self.position)

            self.view.slider.handler_unblock_by_func(self.playerThread.onSliderChange)

        except gst.QueryError:
            # pipeline must not be ready and does not know position
            pass

        return True # continue calling every 30 milliseconds
    
    def resetSlider(self):
        """Resets the slider position to 0"""
        self.playerThread.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, 0)
        self.view.slider.set_value(0)
        self.position = 0
        
    def sliderFormat(self, scale, value): 
        """Sets the time format shown on the slider"""  
        return "%02d:%02d/%02d:%02d" % (self.position / 60, self.position % 60, self.duration / 60, self.duration % 60)
                                
class PlayerThread(threading.Thread):
    """Thread that manages all the player's operations"""
    
    def __init__(self, playlist, control):
        threading.Thread.__init__(self)
        self.playlist = playlist
        self.control = control
        self.playing = False
        self.trackNum = -1        
        self.__createPlayer()
        self.stopevent = threading.Event()

    def __createPlayer(self):
        """Creates and prepares the Gstreamer play bin"""
        self.player = gst.element_factory_make("playbin2", "player")
        sink = gst.element_factory_make("alsasink", "alsa-output")
        self.player.set_property("audio-sink", sink)
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)
        
    def setPlaylist(self, playlist):
        self.playlist = playlist
    
    def clearPlaylist(self):
        """Removes all the files from the playlist"""
        self.playlist = []
        self.control.playlist = self.playlist
        self.stop()
            
    def run(self):
        """Starts the thread"""
        self.control.view.slider.set_sensitive(True)
        self.next()
        while not self.stopevent.isSet():    
            self.stopevent.wait(2)
        gtk.main_quit()
                
    def on_message(self, bus, message):
        """Handles the end of a stream, 
           calling the next() method to play an other track"""
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.next()
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.playing = False
            
    def pause(self, widget = None, event = None):
        """Pauses playing"""
        self.playing = False
        self.player.set_state(gst.STATE_PAUSED)
        self.control.view.setButtonPlay()
        self.control.updatePlaylist()
            
    def play(self, widget = None, event = None):
        """Starts playing"""
        self.playing = True
        self.player.set_state(gst.STATE_PLAYING)
        self.control.view.setButtonPause()
        gobject.timeout_add(100, self.control.updateSlider)
        self.control.updatePlaylist()
        
    def stop(self):
        """Stops playing"""
        self.playing = False
        self.player.set_state(gst.STATE_NULL)   
        self.control.resetSlider()
        self.control.view.setButtonPlay()
        
    def next(self, notify = True):
        """Starts playing of the next track in the playlist"""
        if self.trackNum < len(self.playlist)-1:
            self.trackNum += 1
            self.stop()
            if os.path.isfile(self.playlist[self.trackNum]):
                self.player.set_property("uri", "file://" + self.playlist[self.trackNum])
                self.play()
                self.control.updateLabel(self.playlist[self.trackNum], notify)
        else:
            if not self.playing:
                self.stop()
        
    def previous(self, notify = True):
        """Starts playing of the previous track in the playlist"""
        if self.trackNum > 0:
            self.trackNum -= 1
            self.stop()  
            if os.path.isfile(self.playlist[self.trackNum]):
                self.player.set_property("uri", "file://" + self.playlist[self.trackNum])
                self.play() 
                self.control.updateLabel(self.playlist[self.trackNum], notify)  
        
    def onSliderChange(self, slider):
        """Handles the position changes of the slider"""
        seekTimeSecs = slider.get_value()
        self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT, seekTimeSecs * gst.SECOND)
    
    def onVolumeChanged(self, widget, value=0.5):
        """Handles the position changes of the volume control"""
        self.player.set_property('volume', float(value))
        return True
    
    def terminate(self, timeout=None):
        """Terminates the thread"""
        self.stopevent.set()
        threading.Thread.join(self)
