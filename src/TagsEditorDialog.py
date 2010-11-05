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

import gtk, os, CometSound
from AF import AudioFile

_ = CometSound.t.getTranslationFunc()

class TagsEditor(gtk.Dialog):
    
    def __init__(self, cfname, treeModel, path, columns, colToKey):
        gtk.Dialog.__init__(self)
        i = cfname.rfind('/')
        self.set_title(_('Edit Tags'))       
        file = AudioFile(cfname[:i], cfname[i+1:])
        self.set_size_request(300, 300)
        vbox = self.get_child()
        hbox = gtk.HBox()
        l1 = gtk.Label('File:')
        l1.set_size_request(5,5)
        l1.set_alignment(0.1,0.5)
        e = gtk.Entry()
        e.set_text(cfname[i+1:])
        entries = {}
        entries['file'] = e
        hbox.pack_start(l1)
        hbox.pack_start(e)
        vbox.pack_start(hbox)
        for key in columns[1:7]:
            hbox = gtk.HBox()
            l = gtk.Label(key + ':')
            l.set_size_request(5,5)
            l.set_alignment(0.1,0.5)
            e = gtk.Entry()
            e.set_text(file.getTagValue(colToKey[key]))
            entries[key] = e
            hbox.pack_start(l)
            hbox.pack_start(e)
            vbox.pack_start(hbox)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_APPLY)    
        self.show_all()    
        
        row = treeModel.get_iter(path)
        response = self.run()
        if response == gtk.RESPONSE_CANCEL or response == gtk.RESPONSE_DELETE_EVENT:
            self.destroy()
        elif response == gtk.RESPONSE_APPLY:
            for key in columns[1:7]:
                val = entries[key].get_text()
                file.writeTagValue(colToKey[key], val)  
                n = columns.index(key)
                treeModel.set_value(row, n, val)
            newname = os.path.join(cfname[:i], entries['file'].get_text())
            os.rename(cfname, newname)
            treeModel.set_value(row, len(columns)-1, newname)
            treeModel.set_value(row, 0, entries['file'].get_text())    
            self.destroy()
            
        
        
        