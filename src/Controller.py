##
#    Project: CometSound - A music player written in Python
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

from Commons import gtk
from Commons import gobject
from Commons import gst
from Commons import os
from Commons import sys
from Commons import pynotify
from Commons import cerealizer
from Commons import random
from Commons import time
from Commons import t, _
from Commons import settings, defaultSettings
from Commons import gtkTrick
from Commons import cacheDir
from Commons import audioTypes
from Commons import Global

from Player import PlayerThread
from AF import AudioFile
from Model import Model

icons = {'True': gtk.STOCK_MEDIA_PLAY, 'False': gtk.STOCK_MEDIA_PAUSE}

class Controller:
    """This Class Handles the interactions between the GUI(View) and the Model"""
    folder = ''
    folders = []
    cacheDir = cacheDir

    def __init__(self, model):
        self.model = model
        self.settings = settings
        self.playlist = self.lastPlaylist()
        self.playerThread = PlayerThread(self.playlist, self)
        self.position = 0
        self.duration = 0
        pynotify.init('label')
        self.notification = pynotify.Notification(' ',' ')
        self.folder = self.model.directory
        if self.folder == '':
            self.folder = os.environ.get('HOME', None)
        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)
        try:
            from MediaKeysHandler import MediaKeys
            MediaKeys(self)
        except:
            pass

    def registerView(self,view):
        """Connects the View to the Controller"""
        self.view = view

    def refreshColumnsVisibility(self):
        """Sets the visibility property of the file browser
            columns according to the settings"""
        self.view.filesTree.setColumnsVisibility()

    def refreshStatusIcon(self):
        """Refresh the status icon according to the settings"""
        self.view.setStatusIcon()

    def openFolder(self, o):
        """Creates the dialog window that permits to choose the folder(s) to scan"""
        old = self.folders
        folderChooser = gtk.FileChooserDialog(_('Select Folder...'), None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                               (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        folderChooser.set_current_folder(self.folder)
        folderChooser.set_default_response(gtk.RESPONSE_OK)
        folderChooser.set_select_multiple(True)
        response = folderChooser.run()
        if response == gtk.RESPONSE_OK:
            folderChooser.hide()
            gtkTrick()
            Global.PBcount = 0
            self.view.vbox.pack_start(self.view.progressBar, False)
            self.view.progressBar.set_fraction(0.0)
            if self.settings['view'] != 3:
                self.view.progressBar.show()
            gtkTrick()
            self.folders = folderChooser.get_filenames()
            self.folder = folderChooser.get_current_folder()
            if old != self.folders:
                #if False not in [True for f in self.folders if os.stat(f).st_uid == os.getuid()]:
                self.__reBuildViewTree()
            else:
                self.view.vbox.remove(self.view.progressBar)
                self.refreshTree(update = False)
            folderChooser.hide()
        else:
            folderChooser.destroy()
        gtkTrick()

    def __reBuildViewTree(self):
        """Creates a new Model using the current folder"""
        self.view.filesTree.buttons.set_sensitive(False)
        if len(self.folders) == 1:
            self.model = Model([self.folders[0]], self.view.progressBar)
        else:
            self.model = Model(self.folders, self.view.progressBar, group=True)
        self.saveCache()
        self.__refreshViewTree()
        self.view.vbox.remove(self.view.progressBar)
        self.model.lastUpdate = time.time()
        self.view.filesTree.buttons.set_sensitive(True)

    def loadLibrary(self):
        Global.PBcount = 0
        self.folder = self.settings['libraryFolder']
        self.folders = [self.settings['libraryFolder']]
        self.view.vbox.pack_start(self.view.progressBar, False)
        self.view.progressBar.set_fraction(0.0)
        self.view.progressBar.show()
        gtkTrick()
        self.__reBuildViewTree()

    def saveLibrary(self):
        """Saves the library in a cache file, using serialization"""
        fname = 'library'
        dir = self.cacheDir
        cachefile = os.path.join(dir, fname)
        FILE = open(cachefile,'w')
        cerealizer.dump(self.model.getAudioFileList(), FILE)
        FILE.close()

    def saveCache(self):
        """Saves the model in a cache file, using serialization"""
        if self.settings['libraryMode']:
            return
        else:
            fname = 'cache'
        dir = self.cacheDir
        cachefile = os.path.join(dir, fname)
        FILE = open(cachefile,'w')
        if self.settings['foldercache']:
            cerealizer.dump(self.model.getAudioFileList(), FILE)
        else:
            cerealizer.dump([], FILE)
        FILE.close()

    def saveWinSize(self, width, height, pos, volume):
        """Stores in the settings dictionary the dimensions of the main window"""
        self.settings['width'] = width
        self.settings['height'] = height
        self.settings['pos'] = pos
        self.settings['volume'] = volume

    def readWinSize(self):
        """Returns the dimensions of the main window"""
        s = self.settings
        return s['width'], s['height'], s['pos'], s['volume']

    def saveLastPlaylist(self):
        """Saves the current playlists"""
        dir = self.cacheDir
        if not os.path.exists(dir):
            os.makedirs(dir)
        playlistFile = os.path.join(dir, 'lastplaylist')
        FILE = open(playlistFile,'w')
        cerealizer.dump(self.playlist, FILE)
        FILE.close()

    def lastPlaylist(self):
        """Loads the playlist saved at last shutdown"""
        if self.model.playlist != None:
            return self.model.playlist
        try:
            if self.settings['lastplaylist']:
                dir = self.cacheDir
                playlistFile = os.path.join(dir, 'lastplaylist')
                FILE = open(playlistFile,'r')
                files = cerealizer.load(FILE)
                FILE.close()
                return files
            else:
                return []
        except:
            return []

    def __expFunc(self, tree, path):
        """Stores the currently expanded rows"""
        model = tree.get_model()
        iter = model.get_iter(path)
        folderName = model.get_value(iter, 0)
        self.expandedList.append(folderName)

    def __restoreExpanded(self, model, path, iter):
        """Re-expands the previously expanded rows (to use after a treeView refresh)"""
        iter = model.get_iter(path)
        folderName = model.get_value(iter, 0)
        if folderName in self.expandedList:
            self.view.filesTree.treeview.expand_row(path, False)

    def __refreshViewTree(self):
        """Refreshes the treeview"""
        self.expandedList = []
        self.view.filesTree.treeview.map_expanded_rows(self.__expFunc)
        self.view.filesTree.setModel(self.model)
        self.view.filesTree.searchBox.setListStore(self.view.filesTree.listStore)
        self.view.filesTree.treeStore.foreach(self.__restoreExpanded)

    def refreshTree(self, widget = None, data = None, update = True):
        """Refreshes the Model and the file browser treeView"""
        self.view.vbox.pack_start(self.view.progressBar, False)
        #self.view.progressBar.pulse()
        self.view.statusbar.push(0, 'Updating library...')
        gtkTrick()
        if update: self.model.updateModel()
        if self.model.changed:
            self.__refreshViewTree()
            if self.settings['libraryMode']:
                self.saveLibrary()
            else:
                self.saveCache()
        self.view.statusbar.pop(0)
        self.view.vbox.remove(self.view.progressBar)

    def toggle(self, cell, path, rowModel):
        """Adds the selected files to the playlist and updates the treeview"""
        print
        row = rowModel[path]
        self.__addTrack(row)
        if type(rowModel).__name__ == 'TreeStore':
            self.__recursiveToggle(path, rowModel)
        self.updatePlaylist()

    def __recursiveToggle(self, path, rowModel):
        """Recursively adds the selected files to the playlist and updates the treeview"""
        i=0
        rowexists = True
        while True:
            try:
                row = rowModel[path + (":%d" % (i))]
                self.__addTrack(row)
                self.__recursiveToggle((path + (":%d" % (i))), rowModel)
                i+=1
            except:
                rowexists = False
                #print sys.exc_info()
            if not rowexists:
                break

    def addAll(self, widget, add):
        """Adds to the playlist all the files of the current folder"""
        rowModel = self.view.filesTree.treeview.get_model()
        rowModel.foreach(self.__add)
        self.updatePlaylist()

    def __add(self, model, path, iter, add = None):
        row = model[path]
        self.__addTrack(row)

    def __addTrack(self, row):
        """Handles the addition of the files in the playlist"""
        pt = self.playerThread
        lstore = self.view.playlistFrame.listStore
        append = lstore.append
        cfname = row[8]
        fname = row[0]
        title = row[2]
        album = row[4]
        artist = row[3]
        if cfname != '':
            self.playlist.append((cfname, title, album, artist))
            icon = None
            info = [title,
                    album,
                    artist]
            for tag in info:
                new = tag.replace('<', '')
                new = new.replace('>', '')
                info[info.index(tag)] = new
            text = '<b>%s</b>\n%s <i>%s</i> %s <i>%s</i>' % (info[0], _('from'), info[1], _('by'), info[2])
            text = text.replace('&', '&amp;')
            if info[0] != '' and info[0] != ' ':
                append([icon, text])
            else:
                f = '<b>%s</b>\n' % fname
                append([icon, f])
            if len(self.playlist) == 1 and pt.trackNum != -1:
                pt.trackNum = -1
                self.nextTrack()
                pt.pause()
            self.__extendShuffleList(len(self.playlist)-1)

    def addTrack(self, cfname):
        """Handles the addition of the files in the playlist"""
        pt = self.playerThread
        lstore = self.view.playlistFrame.listStore
        append = lstore.append
        if cfname != '':
            tags = self.extractTags(cfname)
            self.playlist.append((cfname, tags['title'], tags['album'], tags['artist']))
            icon = None
            info = [tags['title'],
                    tags['album'],
                    tags['artist']]
            for tag in info:
                new = tag.replace('<', '')
                new = new.replace('>', '')
                info[info.index(tag)] = new
            text = '<b>%s</b>\n%s <i>%s</i> %s <i>%s</i>' % (info[0], _('from'), info[1], _('by'), info[2])
            text = text.replace('&', '&amp;')
            if info[0] != '' and info[0] != ' ':
                append([icon, text])
            else:
                f = '<b>%s</b>\n' % tags['filename']
                append([icon, f])
            if len(self.playlist) == 1 and pt.trackNum != -1:
                pt.trackNum = -1
                self.nextTrack()
                pt.pause()
            self.__extendShuffleList(len(self.playlist)-1)

    def __extendShuffleList(self, num):
        """Extends the shuffleList to handle the insertion in the playlist of a new track"""
        r = range(self.playerThread.trackNum+1,num)
        if len(r) > 0:
            i = random.choice(r)
            self.playerThread.shuffleList.insert(i, num)
        else:
            self.playerThread.shuffleList.append(num)

    def doubleClickSelect(self, tree, event):
        """Detects double click on the treeview and updates the selection"""
        rowList = tree.get_selection().get_selected_rows()[1]
        model = tree.get_model()
        pt = self.playerThread
        try:
            path, x, y = self.__detectPath(tree, event)
            rectangle = tuple(tree.get_cell_area(path, tree.get_column(7)))
            max, min = rectangle[0] + rectangle[2], rectangle[0]
            if event.type == gtk.gdk._2BUTTON_PRESS and x < min:
                path, x, y = self.__detectPath(tree, event)
                iter = model.get_iter(path)
                if model.get_value(iter, 8) != '':
                    self.toggle(None, path, model)
                    if pt.shuffle:
                        i = pt.shuffleList.index(len(self.playlist)-1)
                        pt.trackNum = i - 1
                    else:
                        pt.trackNum = len(self.playlist) - 2
                    self.nextTrack()
                else:
                    if tree.row_expanded(path):
                        tree.collapse_row(path)
                    else:
                        tree.expand_row(path, False)
                if not self.view.slider.get_sensitive():
                    self.view.slider.set_sensitive(True)
            elif event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
                if max > x > min:
                    if len(rowList) <= 1:
                        self.toggle(None, path, model)
                    elif len(rowList) > 1:
                        for row in rowList:
                            try:
                                path = str(row[0]) + ':' + str(row[1])
                            except:
                                path = str(row[0])
                            self.toggle(None, path, model)
        except:
            #import sys
            #print sys.exc_info()
            return

    def dbusPlay(self):
        """Play command to be called from the dbus service"""
        pt = self.playerThread
        if pt.shuffle:
            i = pt.shuffleList.index(len(self.playlist)-1)
            pt.trackNum = i - 1
        else:
            pt.trackNum = len(self.playlist) - 2
        self.nextTrack()
        if not self.view.slider.get_sensitive():
            self.view.slider.set_sensitive(True)

    def dbusAddTrack(self, cfname):
        """AddTrack command to be called from the dbus service"""
        self.addTrack(cfname)

    def doubleClickPlay(self, tree, event):
        """Detects double click on the playlist and play the selected track"""
        try:
            if event.type == gtk.gdk._2BUTTON_PRESS:
                path, x, y = self.__detectPath(tree, event)
                if not self.view.slider.get_sensitive():
                    self.view.slider.set_sensitive(True)
                i = int(path)
                if self.playerThread.shuffle:
                    num = int(path)
                    i = self.playerThread.shuffleList.index(int(path))
                self.playerThread.trackNum = i - 1
                self.nextTrack()
        except:
            return

    def rightClick(self, tree, event, openMenu):
        """Opens the rx click menu"""
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
        """Starts the D&D process"""
        items = selection.get_selected_rows()
        if len(items[1]) > 1:
            icon = gtk.STOCK_DND_MULTIPLE
        else:
            icon = gtk.STOCK_DND
        context.set_icon_stock(icon, 0, 0)

    def drag(self, treeview, context, selection, target_id, etime):
        """Starts DnD removing the selected file from the playlist"""
        try:
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
        except:
            return


    def drop(self, treeview, context, x, y, selection, info, etime):
        """Starts DnD inserting the selected file in the playlist"""
        try:
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
        except:
            return

    def dragEnd(self, widget, context):
        """Ends the D&D process"""
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
                    self.view.slider.set_sensitive(True)
                    self.playerThread.go()
                    #self.playerThread.join(0.1)
                else:
                    if self.playerThread.trackNum == 0 and self.view.slider.get_value() == 0:
                        self.playerThread.updateGUI()
                    if not self.view.slider.get_sensitive():
                        self.view.slider.set_sensitive(True)
                    self.playerThread.play()
        elif self.view.actiongroup.get_action('Play/Stop').get_stock_id() == gtk.STOCK_MEDIA_PAUSE:
            self.playerThread.pause()
        self.view.image.updateImage()

    def nextTrack(self, obj = None):
        """Handles the click on the Next button"""
        if self.playerThread.started:
            self.playerThread.next()
        else:
            self.playerThread.go()

    def previousTrack(self, obj = None):
        """Handles the click on the Previous button"""
        self.playerThread.previous()

    def updateLabel(self, (cfname, title, album, artist), notify = True):
        """Updates the track label with the tags values"""
        try:
            if title != '' and title != ' ' and title != None:
                info = (title, album, artist)
                label = "<span font_desc='18'><b>%s</b></span>\n<span font_desc='14'>%s\n%s</span>" % info

                winTitle = "%s - %s - %s" % (title, album, artist)
                label = label.replace('&', '&amp;')
                self.view.label.set_markup(label)
                self.view.set_title(winTitle)
                tooltip = "%s:   %s\n%s:   %s\n%s:   %s" % (
                                _('Title'), info[0],
                                _('Album'), info[1],
                                _('Artist'), info[2])

                self.view.label.set_tooltip_text(tooltip)
                self.view.tray.set_tooltip_text("%s\n%s\n%s" % info)
                self.view.label.queue_draw()
            else:
                winTitle = t['filename']
                label = "File:\t<b>" + winTitle + "</b>\n\n"
                self.view.label.set_markup(label)
                self.view.set_title(winTitle)
                print sys.exc_info()
        except:
            label = '\n\n'
            self.view.label.set_text(label)
            self.view.label.set_tooltip_text(label)
            self.view.tray.set_tooltip_text(label)
            self.view.set_title('CometSound')
            self.view.image.setDefaultCover()
            return

    def readPlaylists(self):
        """Reads and returns the list of the playlists stored in the playlists folder"""
        try:
            dir = os.path.join(self.cacheDir, 'playlists')
            fileList = os.listdir(dir)
            return fileList
        except:
            return []

    def loadPlaylist(self, widget, data=None):
        """Loads the selected playlists"""
        file = widget.get_label()
        dir = os.path.join(self.cacheDir, 'playlists')
        playlistFile = os.path.join(dir, file)
        FILE = open(playlistFile,'r')
        files = []
        for line in FILE:
            cfname = line[:-1]
            t = self.extractTags(cfname)
            files.append((cfname, t['title'], t['album'], t['artist']))
        self.playerThread.setPlaylist(files)
        FILE.close()
        self.createPlaylist()

    def savePlaylist(self, playlist, dir = 'playlists'):
        """Saves the current playlists"""
        dir = os.path.join(self.cacheDir, dir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        playlistFile = os.path.join(dir, playlist)
        FILE = open(playlistFile,'w')
        for track in self.playlist:
            FILE.write(track[0] + '\n')
        FILE.close()
        if dir.split('/')[-1] == 'playlists':
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
                lstore.set_value(iter, 0, icons[str(playing)])
            iter = lstore.get_iter(str(i))
            val = lstore.get_value(iter, 0)
            if (i != pt.getNum()
                and (val in [icons[icons.keys()[0]], icons[icons.keys()[1]]])):
                lstore.set_value(iter, 0, None)
            i+=1

    def updatePlaylistSafe(self, playing, num):
        """Refreshes playlist view"""
        lstore = self.view.playlistFrame.listStore
        i = 0
        for track in self.playlist:
            if i == num:
                iter = lstore.get_iter(str(i))
                lstore.set_value(iter, 0, icons[str(playing)])
            iter = lstore.get_iter(str(i))
            val = lstore.get_value(iter, 0)
            if (i != num
                and (val in [icons[icons.keys()[0]], icons[icons.keys()[1]]])):
                lstore.set_value(iter, 0, None)
            i+=1

    def createPlaylist(self):
        """Refreshes playlist view"""
        self.view.playlistFrame.listStore.clear()
        append = self.view.playlistFrame.listStore.append
        playing = str(self.playerThread.playing)
        i = 0
        for (cfname, title, album, artist) in self.playlist:
            if i == self.playerThread.trackNum:
                icon = icons[playing]
            else:
                icon = None
            info = [title,
                    album,
                    artist]
            for tag in info:
                new = tag.replace('<', '')
                new = new.replace('>', '')
                info[info.index(tag)] = new
            text = '<b>%s</b>\n%s <i>%s</i> %s <i>%s</i>' % (info[0], _('from'), info[1], _('by'), info[2])
            text = text.replace('&', '&amp;')
            if info[0] != '' and info[0] != ' ':
                append([icon, text])
            else:
                index = cfname.rfind("/")
                filename = cfname[index+1:]
                f = '<b>%s</b>\n' % filename
                append([icon, f])
            i+=1

    def clearPlaylist(self, widget = None, data=None):
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
        if len(self.playlist) == 0:
            self.view.slider.set_sensitive(False)

    def __removeTrack(self, num):
        """Handles the removal of the files in the playlist"""
        pt = self.playerThread
        lstore = self.view.playlistFrame.listStore
        row = lstore.get_iter(str(num))
        remove = lstore.remove
        try:
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
        """Updates the shuffleList after a removal in the playlist"""
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
        """Sets the repeat state"""
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

        tags = {'filename':filename, 'title':title, 'album':album, 'artist':artist, 'genre':genre, 'year':year, 'num':num }

        return tags

    def sliderClickPress(self, slider, event):
        """Handles the click on the playback slider (stage 1)"""
        self.sliderClickValue = self.__getSliderValue(slider, event)
        if self.sliderClickValue < self.duration:
            gobject.source_remove(self.playerThread.timeoutID)
            slider.handler_block_by_func(self.playerThread.onSliderChange)
            slider.set_value(self.sliderClickValue)

    def sliderClickRelease(self, slider, event):
        """Handles the click on the playback slider (stage 2)"""
        value = self.__getSliderValue(slider, event)
        if self.sliderClickValue < self.duration and value < self.duration:
            self.playerThread.setTimeout()
            slider.handler_unblock_by_func(self.playerThread.onSliderChange)
            slider.set_value(value)

    def __getSliderValue(self, slider, event):
        """Gets the click position from the event"""
        rectangle = tuple(slider.get_allocation())
        width = rectangle[2] - 82
        pos = event.get_coords()[0]
        if pos < 63:
            width += 82
        value = (pos * self.duration) / (width)
        return value

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

            self.view.image.emit('event', gtk.gdk.Event(gtk.gdk.NOTHING))

            if self.playerThread.playing:
                self.playerThread.played += 1

            if self.settings['scrobbler']:
                percentage = int(((self.playerThread.played / 10) / self.duration) * 100)

                if percentage == 50:
                    if self.duration > 30:
                        self.playerThread.scrobble()

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
