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

import gtk

class SearchBox(gtk.Entry):
    
    def __init__(self, listStore, control):
        
        gtk.Entry.__init__(self)
        self.control = control
        self.playlist = control.playlist
        self.listStore = listStore
        self.lastMatch = None
        self.count = 0
        self.set_size_request(350, 28)
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(listStore)
        self.completion.set_text_column(0)
        self.completion.set_match_func(self.matchFunc)
        self.completion.connect('match-selected', self.matchAction)
        self.set_completion(self.completion)
    
    def changeSearchColumn(self, widget, data=None): 
        if widget.get_active():  
            self.completion = gtk.EntryCompletion()
            self.completion.set_model(self.listStore)
            self.completion.set_text_column(data)
            self.completion.set_match_func(self.matchFunc)
            self.completion.connect('match-selected', self.matchAction)
            self.set_completion(self.completion)
            
    def matchFunc(self, completion, key_string, iter, func_data = None):
        model = completion.get_model()
        searchColumn = completion.get_text_column()
        row = model.get_value(iter, searchColumn).lower()
        key = key_string.lower()               
        if row.find(key) != -1:
            return True
        else:
            return False
    
    def matchAction(self, completion, model, iter):
        fileName = model.get_value(iter, 8)
        self.playlist.append(fileName)
        self.control.updatePlaylist()