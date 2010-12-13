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

import gtk, string, gobject, SortFunctions as SF
from Translator import t
from TagsEditorDialog import TagsEditor
from SearchBox import SearchBox

_ = t.getTranslationFunc()

colToKey  = {'#': 'num', _('Title'): 'title', _('Artist'): 'artist',
                _('Album'): 'album', _('Genre'): 'genre', _('Year'): 'year'}

class FilesFrame(gtk.Frame):
    """Gtk Frame modified to store a treeview that shows all the audio files inside the selected folder"""
            
    def __init__(self, model, control, formatDict, columns):
                
        gtk.Frame.__init__(self)
        self.listOfFiles = model.getAudioFileList()
        self.formatDict = formatDict
        self.control = control
        self.columns = columns
        #setting icons
        try:
            self.iconType = 'pixbuf'
            icontheme = gtk.icon_theme_get_for_screen(self.get_screen())
            self.rightPixbuf = icontheme.choose_icon(['stock_right'], 18, 0).load_icon()
            self.dirPixbuf = icontheme.choose_icon(['stock_new-dir'], 18, 0).load_icon()
            g = gobject.TYPE_OBJECT
        except:
            self.iconType = 'stock-id'
            self.rightPixbuf = gtk.STOCK_GO_FORWARD
            self.dirPixbuf = gtk.STOCK_DIRECTORY
            g = gobject.TYPE_STRING
            
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_border_width(0)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create a treeStore with one string column to use as the model
        s = gobject.TYPE_STRING
        self.treeStore = gtk.TreeStore(s, s, s, s, s, s, s, g, s)
        self.listStore = gtk.ListStore(s, s, s, s, s, s, s, g, s)

        self.createTree(None, self.listOfFiles)
        # create and sort the TreeView using treeStore
        self.treeStore.set_sort_func(0, SF.sortNameFunc)
        self.treeStore.set_sort_func(1, SF.sortNumFunc, self.columns.index('#'))
        self.treeStore.set_sort_func(6, SF.sortNumFunc, self.columns.index(_('Year')))
        self.treeStore.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.treeview = gtk.TreeView(self.treeStore)
        self.treeview.set_rules_hint(True)
        self.treeview.connect("button-press-event", self.control.doubleClickSelect)
        self.treeview.connect("button-press-event", self.control.rightClick, self.openMenu)
        # create the TreeViewColumns to display the data
        self.__createColumns()    
        
        self.createSearchToolbar()
        self.scroll.add(self.treeview)
        vbox = gtk.VBox()
        vbox.pack_start(self.buttons, False)
        vbox.pack_start(self.scroll)
        self.add(vbox)

        self.show_all()
    
    def createSearchToolbar(self):
        
        self.buttons = gtk.HBox()

        addAllB = self.control.view.createButton(gtk.STOCK_APPLY, _('Select All'), self.control.addAll, True)
        refreshB = self.control.view.createButton(gtk.STOCK_REFRESH, _('Refresh'), self.control.refreshTree)
        
        searchBox = SearchBox(self.listStore, self.control)
                        
        title = gtk.RadioButton(None, _('Title'))
        title.connect('toggled', searchBox.changeSearchColumn, 2)
        file = gtk.RadioButton(title, 'File')
        file.connect('toggled', searchBox.changeSearchColumn, 0)
        artist = gtk.RadioButton(file, _('Artist'))
        artist.connect('toggled', searchBox.changeSearchColumn, 3)
        album = gtk.RadioButton(artist, _('Album'))
        album.connect('toggled', searchBox.changeSearchColumn, 4)

        self.searchButtons = [file, title, artist, album]
        
        for b in self.searchButtons:
            b.set_relief(gtk.RELIEF_NONE)
            b.set_mode(False)
            
        self.searchBox = searchBox
        self.searchBox.set_size_request(self.get_screen().get_width() / 6, 28) 
        
        #self.buttons.pack_start(gtk.Label('  %s: ' % _('Search')), False)
        self.buttons.set_border_width(3)
        self.buttons.pack_start(searchBox, True)
        self.buttons.pack_start(file, False)
        self.buttons.pack_start(title, False)
        self.buttons.pack_start(artist, False)
        self.buttons.pack_start(album, False)
        self.buttons.pack_start(addAllB, False)
        self.buttons.pack_start(refreshB, False)
        
    def createTree(self, parent, filelist):
        """Adds the files informations to the treeview"""
        for f in filelist:
            if type(f).__name__ == 'instance':
                ext = f.getTagValues()[0].split('.')[-1]
                if self.formatDict[string.lower(ext)] == True:
                    data = f.getTagValues() + [self.rightPixbuf] + [f.getDir() + f.getTagValues()[0]]
                    self.treeStore.append(parent, data)
                    self.listStore.append(data)
            elif type(f).__name__ == 'list':
                if not self.__isEmpty(f):
                    parent2 = self.treeStore.append(parent, [f[0], '', '', '', '', '', '', self.dirPixbuf, ''])
                    self.createTree(parent2, f[1:])
    
    def __isEmpty(self, filelist):
        """Recursively checks if in the folder is there any audio file"""
        for f in filelist:
            if type(f).__name__ == 'instance':
                ext = f.getTagValues()[0].split('.')[-1]
                if self.formatDict[string.lower(ext)] == True: 
                    return False
            elif type(f).__name__ == 'list':   
                if not self.__isEmpty(f):
                    return False           
        return True
    
    def __createColumns(self):
        """Builds and sets the treeview's columns"""
        i = 0
        for column in self.columns:
            if column == _('Add'):
                cell = gtk.CellRendererPixbuf()
                tvcolumn = gtk.TreeViewColumn(column)
                self.treeview.append_column(tvcolumn)
                tvcolumn.pack_start(cell, True)
                tvcolumn.add_attribute(cell, self.iconType, 7)
                cell.set_property('stock-size', gtk.ICON_SIZE_SMALL_TOOLBAR)
                cell.set_fixed_size(5,22)
                tvcolumn.set_resizable(False)
                tvcolumn.set_fixed_width(gtk.TREE_VIEW_COLUMN_FIXED)      
            else:
                if column != '' : 
                    cell = gtk.CellRendererText()
                    cell.set_padding(2, 0)
                    tvcolumn = gtk.TreeViewColumn(column)
                    self.treeview.append_column(tvcolumn)  
                    if column != '#':
                        tvcolumn.pack_start(cell, True)    
                        tvcolumn.add_attribute(cell, 'text', i)
                        tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                        tvcolumn.set_min_width(5)
                        tvcolumn.set_resizable(True)
                        tvcolumn.set_expand(True)
                    else:
                        tvcolumn.pack_start(cell, False) 
                        tvcolumn.add_attribute(cell, 'text', i) 
                        tvcolumn.set_resizable(False)
                        tvcolumn.set_fixed_width(gtk.TREE_VIEW_COLUMN_FIXED)  
                        tvcolumn.set_sort_column_id(1)        
                    if column == _('Name'):
                        tvcolumn.set_sort_column_id(0) 
                    if column == _('Year'):
                        tvcolumn.set_sort_column_id(6) 
                    if column == _('Title'):
                        tvcolumn.set_sort_column_id(2)
                    if column == _('Artist'):
                        tvcolumn.set_sort_column_id(3)    
                    if column == _('Album'):
                        tvcolumn.set_sort_column_id(4)
                    if column == _('Genre'):
                        tvcolumn.set_sort_column_id(5)                              
            i = i + 1
        self.setColumnsVisibility()
        
    def setColumnsVisibility(self):
        columns = self.treeview.get_columns()
        for c in columns:
            try:
                c.set_visible(self.control.settings[c.get_title()])
            except: 
                c.set_visible(True)
        
    def setModel(self, model):
        """Sets a new model to show"""
        self.listOfFiles = model.getAudioFileList()
        self.treeStore.clear()
        self.listStore.clear()
        self.createTree(None, self.listOfFiles)
    
    def setStore(self, store = None):
        if store == None:
            self.treeview.set_model(self.treeStore)
        else:
            self.treeview.set_model(store)
    
    def openMenu(self, time, path):
        cfname = self.treeview.get_model()[path][8]
        trackMenu = gtk.Menu()
        add = gtk.MenuItem(_('Add to playlist'))
        add.show()
        trackMenu.append(add)
        add.connect('activate', self.addToPlaylist, path)
        if cfname != '':
            edit = gtk.MenuItem(_('Edit tags'))
            edit.show()
            trackMenu.append(edit)
            edit.connect('activate', self.openTagsEditor, cfname, path)
        trackMenu.popup(None, None, None, 3, time)
        
    def openTagsEditor(self, obj, cfname, path):
        td = TagsEditor(cfname, self.treeview.get_model(), path, self.columns, colToKey)    
    
    def addToPlaylist(self, obj, path):
        self.control.toggle(None, path, self.treeview.get_model())    
