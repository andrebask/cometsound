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

import gtk, string, gobject, SortFunctions as SF, CometSound
from TagsEditorDialog import TagsEditor

_ = CometSound.t.getTranslationFunc()

class FilesFrame(gtk.Frame):
    """Gtk Frame modified to store a treeview that shows all the audio files inside the selected folder"""
            
    def __init__(self, model, control, formatDict, columns):
                
        gtk.Frame.__init__(self)
        self.listOfFiles = model.getAudioFileList()
        self.formatDict = formatDict
        self.control = control
        self.columns = columns
        #self.set_label("Files selection:")
        
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_border_width(0)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create a treeStore with one string column to use as the model
        s = gobject.TYPE_STRING
        g = gobject.TYPE_BOOLEAN
        self.treeStore = gtk.TreeStore(s, s, s, s, s, s, s, g, s)
        self.listStore = gtk.ListStore(s, s, s, s, s, s, s, g, s)

        self.createTree(None, self.listOfFiles)
        # create and sort the TreeView using treeStore
        self.treeStore.set_sort_func(10, SF.sortNameFunc, self.columns.index(_('Name')))
        self.treeStore.set_sort_func(11, SF.sortNumFunc, self.columns.index('#'))
        self.treeStore.set_sort_func(12, SF.sortNumFunc, self.columns.index(_('Year')))
        self.treeStore.set_sort_column_id(10, gtk.SORT_ASCENDING)
        self.treeview = gtk.TreeView(self.treeStore)
        self.treeview.set_rules_hint(True)
        self.treeview.connect("button-press-event", self.control.doubleClickSelect)
        self.treeview.connect("button-press-event", self.control.rightClick, self.openMenu)
        # create the TreeViewColumns to display the data
        self.__createColumns()    
        
        
        self.scroll.add(self.treeview)
        self.add(self.scroll)

        self.show_all()
        
    def createTree(self, parent, filelist):
        """Adds the files informations to the treeview"""
        for f in filelist:
            if type(f).__name__ == 'instance':
                if self.formatDict[string.lower(f.getTagValues()[0][-4:])] == True:
                    data = f.getTagValues() + [None] + [f.getDir() + f.getTagValues()[0]]
                    self.treeStore.append(parent, data)
                    data[2] = data[2] + '\t(' + data[4] + ')'
                    data[4] = data[4] + '\t(' + data[3] + ')'
                    self.listStore.append(data)
            elif type(f).__name__ == 'list':
                if not self.__isEmpty(f):
                    parent2 = self.treeStore.append(parent, [f[0], '', '', '', '', '', '', '', ''])
                    self.createTree(parent2, f[1:])
    
    def __isEmpty(self, filelist):
        """Recursively checks if in the folder is there any audio file"""
        for f in filelist:
            if type(f).__name__ == 'instance':
                if self.formatDict[string.lower(f.getTagValues()[0][-4:])] == True: 
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
                cell = gtk.CellRendererToggle()
                tvcolumn = gtk.TreeViewColumn(column)
                self.treeview.append_column(tvcolumn)
                tvcolumn.pack_start(cell, False)
                tvcolumn.add_attribute(cell, 'active', i)
                tvcolumn.set_resizable(False)
                tvcolumn.set_fixed_width(gtk.TREE_VIEW_COLUMN_FIXED)
                cell.set_property('active', False)
                cell.connect('toggled', self.control.toggle, self.treeStore)          
            else:
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
                    tvcolumn.set_sort_column_id(11)        
                if column == _('Name'):
                    tvcolumn.set_sort_column_id(10) 
                if column == _('Year'):
                    tvcolumn.set_sort_column_id(12) 
                if column == _('Title'):
                    tvcolumn.set_sort_column_id(2)
                if column == _('Artist'):
                    tvcolumn.set_sort_column_id(3)    
                if column == _('Album'):
                    tvcolumn.set_sort_column_id(6)
                if column == _('Genre'):
                    tvcolumn.set_sort_column_id(5)                              
                if column == '' :
                    tvcolumn.set_expand(False)
                    tvcolumn.set_max_width(0)
                    tvcolumn.set_visible(False)
            i = i + 1
        self.setColumnsVisibility()
        
    def setColumnsVisibility(self):
        columns = self.treeview.get_columns()
        for c in columns:
            try:
                c.set_visible(self.control.settings[c.get_title()])
            except: 
                if c != '' : 
                    c.set_visible(True)
        
    def setModel(self, model):
        """Sets a new model to show"""
        self.listOfFiles = model.getAudioFileList()
        self.treeStore.clear()
        self.listStore.clear()
        self.createTree(None, self.listOfFiles)
    
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
        td = TagsEditor(cfname, self.treeview.get_model(), path)    
    
    def addToPlaylist(self, obj, path):
        self.control.toggle(None, path, self.treeview.get_model())    