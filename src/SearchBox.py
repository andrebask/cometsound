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

import gtk, gobject, SortFunctions as SF
from Translator import t
_ = t.getTranslationFunc()

class SearchBox(gtk.Entry):
    
    def __init__(self, listStore, control):
        
        gtk.Entry.__init__(self)
        self.control = control
        self.modify_text(gtk.STATE_NORMAL,  gtk.gdk.Color('#AAAAAA'))
        self.set_text(_('Search'))
        s = gobject.TYPE_STRING
        g = gobject.TYPE_OBJECT
        self.matchStore = gtk.ListStore(s, s, s, s, s, s, s, g, s)
        self.set_property("primary-icon-stock", gtk.STOCK_FIND)
        self.set_property("secondary-icon-stock", gtk.STOCK_CLEAR)
        self.connect("icon-press", self.simpleClear)
        self.connect("focus-in-event", self.clear)
        self.connect('changed', self.matchClear)
        self.listStore = listStore
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(self.listStore)
        self.completion.set_text_column(2)
        self.completion.set_match_func(self.matchFunc)
        self.set_completion(self.completion)
        self.previousList = []
    
    def matchClear(self, editable):
        if self.get_text() == '':
            self.control.view.filesTree.setStore()
        else:
            self.matchStore.clear()
        self.previousList = []
    
    def simpleClear(self, entry, icon, event):
        if icon == gtk.ENTRY_ICON_SECONDARY:
            self.set_text('')
            
    def clear(self, editable, data = None):
        self.set_text('')
        self.modify_text(gtk.STATE_NORMAL,  gtk.gdk.Color(0,0,0))
        self.disconnect_by_func(self.clear)
            
    def setListStore(self, listStore):
        self.listStore = listStore
        self.set_text('')
        self.control.view.filesTree.setStore()
            
    def changeSearchColumn(self, widget, data=None): 
        if widget.get_active():  
            self.completion.set_text_column(data)
            
    def matchFunc(self, completion, key_string, iter, func_data = None):
        model = completion.get_model()
        searchColumn = completion.get_text_column()
        try:
            row = model.get_value(iter, searchColumn).lower()
        except:
            return False    
        key = key_string.lower()               
        if row.find(key) != -1:
            list = []
            for c in range(9):
                list.append(model.get_value(iter, c))
            if list not in self.previousList:
                self.previousList.append(list)
                self.matchStore.append(list) 
            self.control.view.filesTree.setStore(self.matchStore) 
            return False
        else:
            return False

