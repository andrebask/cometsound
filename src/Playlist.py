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

import gtk, gobject, CometSound

_ = CometSound.t.getTranslationFunc()

class PlaylistFrame(gtk.Frame):
    """Gtk Frame modified to store a treeview that shows the playlist"""
    def __init__(self, control, playlist):
        
        gtk.Frame.__init__(self)
        self.control = control
        
        #self.set_label("")
        
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_border_width(0)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create a treeStore with one string column to use as the model
        s = gobject.TYPE_STRING
        g = gobject.TYPE_STRING
        self.listStore = gtk.ListStore(g, s)
        
        # create and sort the TreeView using treeStore
        self.treeview = gtk.TreeView(self.listStore)
        self.treeview.set_rules_hint(True) 
        self.treeview.connect("button-press-event", self.control.doubleClickPlay)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.setupDnD()
        
        playCell = gtk.CellRendererPixbuf()
        tvcolumn = gtk.TreeViewColumn()
        self.treeview.append_column(tvcolumn)
        tvcolumn.pack_start(playCell, False)    
        tvcolumn.add_attribute(playCell, 'stock-id', 0)
        tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        tvcolumn.set_resizable(True)   
        
        titleCell = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn(_('Playlist'))
        self.treeview.append_column(tvcolumn)
        tvcolumn.pack_start(titleCell, False)    
        tvcolumn.add_attribute(titleCell, 'markup', 1)
        tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        tvcolumn.set_resizable(True)
        
        self.scroll.add(self.treeview)
        self.add(self.scroll)
        self.show_all()
    
    def setupDnD(self):
        """Drag and drop inizialization"""
        self.TARGETS = [('TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0)]  
        self.treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, self.TARGETS, gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.treeview.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_DEFAULT)     
        self.treeview.connect("drag_data_get", self.control.drag)
        self.treeview.connect("drag_data_received", self.control.drop)
        