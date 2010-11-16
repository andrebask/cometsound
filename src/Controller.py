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

import gtk, os, Model, gst, pynotify, cerealizer, random, time, sys
from AF import AudioFile
from Player import PlayerThread
from View import CometSound
from Model import audioTypes
_ = CometSound.t.getTranslationFunc()

icons = {'True': gtk.STOCK_MEDIA_PLAY, 'False': gtk.STOCK_MEDIA_PAUSE}

class Controller:
    """This Class Handles the interactions between the GUI(View) and the Model"""
    folder = ''
    cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound") 
    
    def __init__(self, model):
        self.model = model
        self.playlist = self.lastPlaylist()
        self.readSettings()
        self.playerThread = PlayerThread(self.playlist, self)
        self.position = 0
        self.duration = 0
        pynotify.init('label')
        self.notification = pynotify.Notification(' ',' ')
        self.folder = self.model.directory
        if self.folder == '':
            self.folder = os.environ.get('HOME', None)
        
        try:
            from MediaKeysHandler import MediaKeys
            MediaKeys(self)
        except:
            pass
            
    def registerView(self,view):
        """Connects the View to the Controller"""
        self.view = view
    
    def writeSettings(self, settings):
        dir = self.cacheDir
        if not os.path.exists(dir):
            os.makedirs(dir)
        cachefile = os.path.join(dir, 'settings')
        FILE = open(cachefile,'w')
        cerealizer.dump(settings, FILE)
        FILE.close()
        self.settings = settings
        
    def readSettings(self):
        try: 
            FILE = open(os.path.join(self.cacheDir, 'settings'),'rb')
            self.settings = cerealizer.load(FILE)
            FILE.close()
        except:
            #print sys.exc_info()
            self.settings = {'audiosink': 'autoaudiosink',
                    'statusicon': 0,    
                    '#': True,
                     _('Title'): True,
                     _('Artist'): True,
                      _('Album'): True,
                       _('Genre'): True,
                        _('Year'): True,
                         _('Add'): True
                         }      
        
    
    def refreshColumnsVisibility(self):
        self.view.filesTree.setColumnsVisibility()
    
    def refreshStatusIcon(self):
        self.view.setStatusIcon()

    def openFolder(self, o):
        """Creates the dialog window that permits to choose the folder to scan"""
        old = self.folder
        folderChooser = gtk.FileChooserDialog('Select Folder...', None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                               (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        folderChooser.set_current_folder(self.folder)
        folderChooser.set_default_response(gtk.RESPONSE_OK)
        response = folderChooser.run()
        if response == gtk.RESPONSE_OK:
            self.view.vbox.pack_start(self.view.progressBar, False)
            self.view.show_all()
            self.folder = folderChooser.get_current_folder()
            folderChooser.hide()
            if old != self.folder:
                if os.stat(self.folder).st_uid == os.getuid():
                    self.__reBuildViewTree()
            else:
                self.view.vbox.remove(self.view.progressBar)
                self.refreshTree()
        else:
            folderChooser.hide()    
        while gtk.events_pending():
            gtk.main_iteration()   
    
    def __reBuildViewTree(self):
        """Creates a new Model using the current folder"""
        self.model = Model.Model(self.folder, self.view.progressBar)
        self.saveCache()
        self.__refreshViewTree()
        self.view.vbox.remove(self.view.progressBar)
        self.model.lastUpdate = time.time()
    
    def saveCache(self):
        """Saves the model in a cache file, using serialization"""
        dir = self.cacheDir
        if not os.path.exists(dir):
            os.makedirs(dir)
        cachefile = os.path.join(dir, "cache")
        FILE = open(cachefile,'w')
        cerealizer.dump(self.model.getAudioFileList(), FILE)
        FILE.close()
        self.savePlaylist('lastplaylist', '')
    
    def saveWinSize(self, width, height, pos, volume):
        try:
            dir = self.cacheDir
            if not os.path.exists(dir):
                os.makedirs(dir)
            sizeFile = os.path.join(dir, 'size')
            FILE = open(sizeFile,'w')
            for n in (width, height, pos, volume):
                FILE.write(str(n) + '\n')
            FILE.close()
        except:
            return
    
    def readWinSize(self):
        sizeFile = os.path.join(self.cacheDir, 'size')
        FILE = open(sizeFile,'r')
        wh = []
        for line in FILE:
            wh.append(line[:-1]) 
        FILE.close()
        return int(wh[0]), int(wh[1]), int(wh[2]), float(wh[3])
    
    def lastPlaylist(self):
        try:
            dir = self.cacheDir
            playlistFile = os.path.join(dir, 'lastplaylist')
            FILE = open(playlistFile,'r')
            files = []
            for line in FILE:
                files.append(line[:-1]) 
            FILE.close()
            return files
        except:
            return []
    
    def __refreshViewTree(self): 
        """Refreshes the treeview"""  
        self.view.filesTree.setModel(self.model)
        self.view.searchBox.setListStore(self.view.filesTree.listStore)
    
    def refreshTree(self, widget = None, data = None):
        self.model.updateModel()
        self.__refreshViewTree()
            
    def toggle(self, cell, path, rowModel):
        """Adds the selected files to the playlist and updates the treeview"""
        completeFilename = rowModel[path][8]
        self.__addTrack(completeFilename)
        self.__recursiveToggle(path, rowModel)
        self.updatePlaylist()
        
    def __recursiveToggle(self, path, rowModel):
        i=0
        rowexists = True
        while True:
            try:
                completeFilename = rowModel[path + (":%d" % (i))][8]
                self.__addTrack(completeFilename)
                self.__recursiveToggle((path + (":%d" % (i))), rowModel)
                i+=1
            except:
                rowexists = False
                #print sys.exc_info()                    
            if not rowexists:
                break

    def addAll(self, widget, add):
        """Adds to the playlist all the files of the current folder"""
        rowModel = self.view.filesTree.treeStore
        rowModel.foreach(self.__add)
        self.updatePlaylist()
        
    def __add(self, model, path, iter, add = None):
        completeFilename = model[path][8]
        self.__addTrack(completeFilename)
            
    def __addTrack(self, cfname):
        """Handles the addition of the files in the playlist"""
        pt = self.playerThread
        lstore = self.view.playlistFrame.listStore
        append = lstore.append
        if cfname != '':
            self.playlist.append(cfname)
            tags = self.extractTags(cfname)
            icon = None        
            info = (tags['title'], 
                    tags['album'],
                    tags['artist'])
            text = '<b>%s</b>\n%s <i>%s</i> %s <i>%s</i>' % (info[0], _('from'), info[1], _('by'), info[2])
            text = text.replace('&', '&amp;')
            if info[0] != '' and info[0] != ' ':
                append([icon, text])             
            else:
                f = '<b>%s</b>\n' % tags['filename']
                append([icon, f])
            if len(self.playlist) == 1 and pt.trackNum != -1:
                pt.trackNum = -1
                pt.next()
                pt.pause()
            self.__extendShuffleList(len(self.playlist)-1)
    
    def __extendShuffleList(self, num):
        r = range(self.playerThread.trackNum+1,num)
        if len(r) > 0:
            i = random.choice(r)
            self.playerThread.shuffleList.insert(i, num)
        else:
            self.playerThread.shuffleList.append(num)
            
    def doubleClickSelect(self, tree, event):
        """Detects double click on the treeview and updates the selection"""
        pt = self.playerThread
        try:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                path, x, y = self.__detectPath(tree, event)
                model = tree.get_model()
                iter = model.get_iter(path)
                if model.get_value(iter, 8) != '':
                    self.toggle(None, path, model)
                    if pt.trackNum == -1:
                        self.view.slider.set_sensitive(True)
                    if pt.shuffle:
                        i = pt.shuffleList.index(len(self.playlist)-1)
                        pt.trackNum = i - 1
                    else:
                        pt.trackNum = len(self.playlist) - 2
                    if pt.isAlive():  
                        pt.next()  
                    else:
                        self.playStopSelected(None)
                else:
                    if tree.row_expanded(path):
                        tree.collapse_row(path)
                    else:
                        tree.expand_row(path, False)
            elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
                path, x, y = self.__detectPath(tree, event)
                rectangle = tuple(tree.get_cell_area(path, tree.get_column(7)))
                max, min = rectangle[0] + rectangle[2], rectangle[0]
                if max > x > min:
                    model = tree.get_model()
                    iter = model.get_iter(path)    
                    self.toggle(None, path, model)
        except:
            return
        
    def doubleClickPlay(self, tree, event):
        """Detects double click on the playlist and play the selected track"""
        try:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                path, x, y = self.__detectPath(tree, event) 
                if self.playerThread.trackNum == -1:
                    self.view.slider.set_sensitive(True)
                self.playerThread.trackNum = int(path) - 1
                if self.playerThread.isAlive():    
                    self.playerThread.next()    
                else:
                    self.playStopSelected(None)
        except:
            return
    
    def rightClick(self, tree, event, openMenu):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            path, x, y = self.__detectPath(tree, event) 
            openMenu(event.time, path)
                
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
        return path, x, y 
    
    def dragBegin(self, widget, context, selection):
        items = selection.get_selected_rows()
        if len(items[1]) > 1:
            icon = gtk.STOCK_DND_MULTIPLE
        else:
            icon = gtk.STOCK_DND
        context.set_icon_stock(icon, 0, 0)
    
    def drag(self, treeview, context, selection, target_id, etime):
        """Starts DnD removing the selected file from the playlist"""
        treeselection = treeview.get_selection()
        model, rows = treeselection.get_selected_rows()
        self.current = self.playlist[self.playerThread.trackNum]
        self.startIndex = rows[0][0]
        self.movedTracks = []
        count = 0
        for tuple in rows:
            path = tuple[0] - count
            self.movedTracks.append(self.playlist[path])
            del self.playlist[path] 
            count+=1
                  

    def drop(self, treeview, context, x, y, selection, info, etime):
        """"Starts DnD inserting the selected file in the playlist"""
        drop_info = treeview.get_dest_row_at_pos(x, y)
        count = 0
        for row in self.movedTracks:
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
                index = path[0] + i + count
                self.playlist.insert(index, row)
            else:
                self.playlist.append(row)
            count += 1
        context.finish(True, True, etime)       
        self.playerThread.trackNum = self.playlist.index(self.current)     

    def dragEnd(self, widget, context):
        self.createPlaylist()
            
    def toggleFilter(self, data):
        """Enables/disables mp3 filtering"""
        for type in audioTypes:
            self.view.getFormatDict()[type[1:]] = self.view.actiongroup.get_action(type[1:].capitalize()).get_active()
        self.__refreshViewTree()
        return
    
    def playStopSelected(self, obj = None):
        """Handles the click on the Play/Pause button"""
        if self.view.actiongroup.get_action('Play/Stop').get_stock_id() == gtk.STOCK_MEDIA_PLAY:
            if len(self.playlist) > 0:
                if not self.playerThread.isStarted():
                    self.playerThread.setPlaylist(self.playlist)
                    self.playerThread.start()
                    self.playerThread.join(0.1)
                else: 
                    self.playerThread.play()  
        elif self.view.actiongroup.get_action('Play/Stop').get_stock_id() == gtk.STOCK_MEDIA_PAUSE: 
            self.playerThread.pause()            
     
    def nextTrack(self, obj = None):
        """Handles the click on the Next button"""
        self.playerThread.next()
     
    def previousTrack(self, obj = None):
        """Handles the click on the Previous button"""
        self.playerThread.previous()
        
    def updateLabel(self, completefilename, notify = True):
        """Updates the track label with the tags values"""
        try:
            t = self.extractTags(completefilename)
        except:
            label = '\n\n'
            self.view.label.set_text(label)
            self.view.set_title('CometSound')    
            return
        if t['title'] != '' and t['title'] != ' ':
            info = (t['title'][:50], t['album'][:50], t['artist'][:50])
            label = "<b>%s</b>\n%s\n%s" % info
            
            winTitle = "%s - %s - %s" % (t['title'], t['album'], t['artist'])
            label = label.replace('&', '&amp;')
            self.view.label.set_markup(label)
            self.view.set_title(winTitle)
            tooltip = "%s:   %s\n%s:   %s\n%s:   %s\n%s:   %s\n%s:   %s\n%s:      \t%s" % (
                            _('Title'), info[0],
                            _('Album'), info[1],
                            _('Artist'), info[2],
                            _('Year'), t['year'],
                            _('Genre'), t['genre'],
                            '#', t['num'])
            
            self.view.label.set_tooltip_text(tooltip)
            self.view.tray.set_tooltip_text("%s\n%s\n%s" % info)
            if notify:
                self.notification.update(t['title'], "%s\n%s" % (t['album'], t['artist']))
                self.notification.show()
        else:
            winTitle = t['filename']
            label = "File:\t<b>" + winTitle[:50] + "</b>\n\n"
            self.view.label.set_markup(label)
            self.view.set_title(winTitle)    
    
    def readPlaylists(self):
        try:
            dir = os.path.join(self.cacheDir, 'playlists')
            fileList = os.listdir(dir)
            return fileList
        except:
            return []
    
    def loadPlaylist(self, widget, data=None):
        file = widget.get_label()
        dir = os.path.join(self.cacheDir, 'playlists')
        playlistFile = os.path.join(dir, file)
        FILE = open(playlistFile,'r')
        files = []
        for line in FILE:
            files.append(line[:-1]) 
        self.playerThread.setPlaylist(files)
        FILE.close()
        self.updatePlaylist()
    
    def savePlaylist(self, playlist, dir = 'playlists'):
        dir = os.path.join(self.cacheDir, dir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        playlistFile = os.path.join(dir, playlist)
        FILE = open(playlistFile,'w')
        for track in self.playlist:
            FILE.write(track + '\n')
        FILE.close()
        if dir == 'playlists':
            self.view.updatePlaylistsMenu(playlist)

    def updatePlaylist(self):
        """Refreshes playlist view"""
        lstore = self.view.playlistFrame.listStore     
        pt = self.playerThread        
        playing = str(pt.playing)
        i = 0
        for track in self.playlist:
            if i == pt.getNum():
                iter = lstore.get_iter(str(i))
                lstore.set_value(iter, 0, icons[playing])
            iter = lstore.get_iter(str(i))
            val = lstore.get_value(iter, 0)
            if (i != pt.getNum() 
                and (val in [icons[playing], icons[str(not playing)]])):
                lstore.set_value(iter, 0, None)
            i+=1
            
    def createPlaylist(self):
        """Refreshes playlist view"""
        self.view.playlistFrame.listStore.clear()  
        append = self.view.playlistFrame.listStore.append              
        playing = str(self.playerThread.playing)
        i = 0
        for track in self.playlist:
            tags = self.extractTags(track)
            if i == self.playerThread.trackNum:
                icon = icons[playing]
            else:
                icon = None        
            info = (tags['title'], 
                    tags['album'],
                    tags['artist'])
            text = '<b>%s</b>\n%s <i>%s</i> %s <i>%s</i>' % (info[0], _('from'), info[1], _('by'), info[2])
            text = text.replace('&', '&amp;')
            if info[0] != '' and info[0] != ' ':
                append([icon, text])             
            else:
                f = '<b>%s</b>\n' % tags['filename']
                append([icon, f]) 
            i+=1

    def clearPlaylist(self, widget, data=None):
        """Removes all the files from the playlist"""
        self.playerThread.clearPlaylist()
        self.createPlaylist()
    
    def removeSelected(self, widget, data = None):
        """Removes only the selected files from the playlist"""
        rowList = self.view.playlistFrame.treeview.get_selection().get_selected_rows()[1]
        i = 0
        for row in rowList:
            num = row[0]-i
            self.__removeTrack(num) 
            i+=1    
        self.updatePlaylist()    

    def __removeTrack(self, num): 
        """Handles the removal of the files in the playlist"""
        pt = self.playerThread   
        lstore = self.view.playlistFrame.listStore
        row = lstore.get_iter(str(num))
        remove = lstore.remove
        try:
            if pt.started:
                if pt.trackNum == num:
                    if pt.playing:
                        pt.next()
                        if len(self.playlist) == 1:
                            pt.stop()
                    else:
                        pt.next()
                        pt.pause()
                    if len(self.playlist)-1 == num:
                        pt.trackNum = -1
                        pt.next() 
                        pt.stop()
            if pt.trackNum > num:
                pt.trackNum -= 1    
            del self.playlist[num]
            remove(row)
            self.__updateShuffleList(pt, num)                               
        except:
            pass
            #print sys.exc_info()
    
    def __updateShuffleList(self, pt, num):
        pt.shuffleList.remove(num)
        for n in pt.shuffleList:
            if n > num:
                pt.shuffleList[pt.shuffleList.index(n)] = n-1
            
    def shufflePlaylist(self, widget, data=None):
        """Randomizes the playback"""
        pt = self.playerThread
        if widget.get_active():
            pt.shuffle = True
            pt.setRand()
        else:
            pt.trackNum = pt.getNum()
            pt.shuffle = False
            
    def setRepeat(self, widget, data=None): 
        pt = self.playerThread
        if widget.get_active():
            pt.repeat = True
        else:
            pt.repeat = False
    
    def extractTags(self, completefilename):
        """Extracts tags from a given filename.
           Returns a dictionary with the following keys:
           filename, title, artist, album, genre, year, num"""
        index = completefilename.rfind("/")    
        directory = completefilename[:index]
        filename = completefilename[index+1:]
        af = AudioFile(directory, filename)
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
                                