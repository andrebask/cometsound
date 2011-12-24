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

import gtk, gobject, SortFunctions as SF
from Translator import t
_ = t.getTranslationFunc()

class SearchBox(gtk.Entry):
    """Search bar to search tracks
        (Implemented with gtk.EntryCompletion)"""
    
    def __init__(self, listStore, fileBrowser):
        
        gtk.Entry.__init__(self)
        self.fileBrowser = fileBrowser
        s = gobject.TYPE_STRING
        g = gobject.TYPE_OBJECT
        self.matchStore = gtk.ListStore(s, s, s, s, s, s, s, g, s)
        self.setSortFunctions()
        self.set_property("primary-icon-stock", gtk.STOCK_FIND)
        self.set_property("secondary-icon-stock", gtk.STOCK_CLEAR)
        self.connect("icon-press", self.simpleClear)
        self.connect('changed', self.matchClear)
        self.setListStore(listStore)
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(self.listStore)
        self.completion.set_text_column(2)
        self.searchColumn = self.completion.get_text_column()
        self.completion.set_match_func(self.matchFunc)
        self.set_completion(self.completion)
        self.previousDict = {}
        self.stop = False
    
    def matchClear(self, editable):
        if len(self.get_text()) < 2:
            self.fileBrowser.setCurrentStore()
        else:
            self.matchStore.clear()
            self.fileBrowser.setStore(self.matchStore)
        self.previousDict = {}
        self.stop = False
    
    def simpleClear(self, entry, icon, event):
        if icon == gtk.ENTRY_ICON_SECONDARY:
            self.set_text('')
            
    def clear(self, editable, data = None):
        self.set_text('')
        self.modify_text(gtk.STATE_NORMAL,  gtk.gdk.Color(0,0,0))
        self.disconnect_by_func(self.clear)
            
    def setListStore(self, listStore):
        self.listStore = listStore
        self.set_text(_('Search'))
        self.modify_text(gtk.STATE_NORMAL,  gtk.gdk.Color('#AAAAAA'))
        self.connect("focus-in-event", self.clear)
        self.fileBrowser.setStore()
            
    def changeSearchColumn(self, widget, data=None): 
        if widget.get_active():  
            self.completion.set_text_column(data)
            self.searchColumn = self.completion.get_text_column()
            
    def matchFunc(self, completion, key_string, iter, func_data = None):
        if not self.stop and len(key_string) > 1:
            try:
                row = self.listStore.get_value(iter, self.searchColumn).lower()
            except:
                return False    
            key = key_string.lower()               
            if row.find(key) != -1:
                list = []
                for c in range(9):
                    list.append(self.listStore.get_value(iter, c))
                try:
                    x = self.previousDict[list[8]]
                    for key in self.previousDict.keys():
                        self.matchStore.append(self.previousDict[key])
                    self.fileBrowser.setStore(self.matchStore)
                    self.stop = True
                except:
                    self.previousDict[list[8]] = list
                return False
            else:
                return False
        return False

    def setSortFunctions(self):
        self.matchStore.set_sort_func(0, SF.sortNameFunc)
        self.matchStore.set_sort_func(1, SF.sortNumFunc, 1)
        self.matchStore.set_sort_func(4, SF.sortNameFunc, 4)
        self.matchStore.set_sort_func(6, SF.sortNumFunc, 6)
        self.matchStore.set_sort_column_id(0, gtk.SORT_ASCENDING)