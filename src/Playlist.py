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

import gtk, gobject
from Translator import t

_ = t.getTranslationFunc()

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
        tvcolumn.set_min_width(20)
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
        
        self.createButtons()
        
        self.treeview.set_headers_visible(False)
        self.scroll.add(self.treeview)
        vbox = gtk.VBox()
        vbox.pack_start(self.buttons, False)
        vbox.pack_start(self.scroll)
        self.add(vbox)
        self.show_all()
    
    def createButtons(self):
        
        self.buttons = gtk.HBox()

        clearB = self.control.view.createButton(gtk.STOCK_CLEAR, _('Clear Playlist'), self.control.clearPlaylist)
        removeSelectedB = self.control.view.createButton(gtk.STOCK_REMOVE, _('Remove Selection'), self.control.removeSelected)
        saveB = self.control.view.createButton(gtk.STOCK_SAVE, _('Save Playlist'), self.control.view.savePlaylistDialog)
        
        sIcon = gtk.Image()
        icontheme = gtk.icon_theme_get_for_screen(self.get_screen())
        pixbuf = icontheme.choose_icon(['stock_shuffle'], 18, 0).load_icon()
        sIcon.set_from_pixbuf(pixbuf)
        shuffleB = gtk.ToggleButton()
        shuffleB.add(sIcon)
        shuffleB.set_tooltip_text(_('Shuffle'))
        shuffleB.connect("toggled", self.control.shufflePlaylist)
        
        sIcon = gtk.Image()
        icontheme = gtk.icon_theme_get_for_screen(self.get_screen())
        pixbuf = icontheme.choose_icon(['stock_repeat'], 18, 0).load_icon()
        sIcon.set_from_pixbuf(pixbuf)
        repeatB = gtk.ToggleButton()
        repeatB.add(sIcon)
        repeatB.set_tooltip_text(_('Repeat'))
        repeatB.connect("toggled", self.control.setRepeat)
        
        self.buttons.set_border_width(3)
        self.buttons.pack_start(gtk.Label(_('Playlist')), True)
        self.buttons.pack_start(repeatB, False)
        self.buttons.pack_start(shuffleB, False)
        self.buttons.pack_start(saveB, False)
        self.buttons.pack_start(clearB, False)
        self.buttons.pack_start(removeSelectedB, False)          
    
    def setupDnD(self):
        """Drag and drop inizialization"""
        self.TARGETS = [('TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0)]  
        self.treeview.drag_source_set(gtk.gdk.BUTTON1_MASK, self.TARGETS, gtk.gdk.ACTION_MOVE)
        self.treeview.enable_model_drag_dest(self.TARGETS, gtk.gdk.ACTION_MOVE)
        self.treeview.connect("drag_begin", self.control.dragBegin, self.treeview.get_selection())     
        self.treeview.connect("drag_data_get", self.control.drag)
        self.treeview.connect("drag_data_received", self.control.drop)
        self.treeview.connect("drag_end", self.control.dragEnd) 
        