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

import gtk, gobject, SortFunctions as SF, time

class SearchBox(gtk.Entry):
    
    def __init__(self, listStore, control):
        
        gtk.Entry.__init__(self)
        self.control = control
        self.artistStore = gtk.ListStore(gobject.TYPE_STRING)
        self.albumStore = gtk.ListStore(gobject.TYPE_STRING)
        self.setListStore(listStore)
        self.set_size_request(350, 28)
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(self.listStore)
        self.completion.set_text_column(0)
        self.completion.set_match_func(self.matchFunc)
        self.completion.connect('match-selected', self.matchAction, 0)
        self.set_completion(self.completion)
    
    def clear(self, editable, data = None):
        self.set_text('')
        self.disconnect_by_func(self.clear)
        
    def copyValues(self, model, path, iter, user_data = None):
        value = model.get_value(iter, 4)
        if value not in self.albumList:
            self.albumList.append(value)
            self.albumStore.append([value])
        value = model.get_value(iter, 3)
        if value not in self.artistList:
            self.artistList.append(value)
            self.artistStore.append([value])
    
    def setListStore(self, listStore):
        self.listStore = listStore
        self.albumList = []
        self.artistList = []
        self.artistStore.clear()
        self.albumStore.clear()
        self.listStore.foreach(self.copyValues)
            
    def changeSearchColumn(self, widget, data=None): 
        
        if widget.get_active():  
            self.completion = gtk.EntryCompletion()
            if data == 3:
                self.completion.set_model(self.artistStore)
                self.completion.set_text_column(0)
            elif data == 4:
                self.completion.set_model(self.albumStore)
                self.completion.set_text_column(0)    
            else:    
                self.completion.set_model(self.listStore)    
                self.completion.set_text_column(data)
            self.completion.set_match_func(self.matchFunc)
            self.completion.connect('match-selected', self.matchAction, data)
            self.set_completion(self.completion)
            
    def matchFunc(self, completion, key_string, iter, func_data = None):
        model = completion.get_model()
        searchColumn = completion.get_text_column()
        try:
            row = model.get_value(iter, searchColumn).lower()
            row = row.split('(')[0]
        except:
            return False    
        key = key_string.lower()               
        if row.find(key) != -1:
            return True
        else:
            return False
    
    def matchAction(self, completion, model, iter, column):
        self.connect('changed', self.clear)
        if column == 0 or column == 2:
            fileName = model.get_value(iter, 8)
            self.control.playlist.append(fileName)
        else:
            if column == 3:
                self.listStore.set_sort_func(13, SF.sortArtistFunc, 4)
                self.listStore.set_sort_column_id(13, gtk.SORT_ASCENDING)
            elif column == 4:
                self.listStore.set_sort_func(13, SF.sortNumFunc, 1)
                self.listStore.set_sort_column_id(13, gtk.SORT_ASCENDING)    
            value = model.get_value(iter, 0)  
            self.listStore.foreach(self.add, (value, column))  
        self.control.updatePlaylist()

    def add(self, model, path, iter, (value, column)):
        v = model.get_value(iter, column)
        if v == value:
            fileName = model.get_value(iter, 8)
            self.control.playlist.append(fileName)