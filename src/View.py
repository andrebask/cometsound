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

import Model, Controller, gtk, gobject, string, pygtk, SortFunctions as SF
pygtk.require('2.0')

class View(gtk.Window):
    
    version = '0.1'
    formatDict = {'.mp3': True, '.wma': True, '.ogg': True}
        
    def __init__(self, model, control):
        
        gtk.Window.__init__(self)
        self.model = model
        self.control = control
        self.set_title('CometSound')
        self.control.registerView(self)
        
        # Create the toplevel window
        self.maximized = True
        self.connect('destroy', lambda w: self.destroy())
        self.set_size_request(self.get_screen().get_width() / 2, self.get_screen().get_height() / 2) 
        self.set_position(gtk.WIN_POS_CENTER)
        self.icon = gtk.Image()
        self.icon.set_from_file("icon.svg")
        pix = self.icon.get_pixbuf().scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
        self.set_icon(pix)

        self.vbox = gtk.VBox()
        self.add(self.vbox)       
        
        self.hbox = gtk.HBox()
        self.framebox = gtk.HPaned()
        #self.framebox.set_position(int(self.get_size()[1]*1.2))
        self.connect('window-state-event', self.fixFrameboxPos)
        # Create a UIManager instance
        uimanager = gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup

        
        # Create actions
        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, '_Quit', None, 'Quit the Program', self.quit),
                                 ('Open', gtk.STOCK_OPEN, '_Open Folder...', None, 'Open Media Folder', self.control.openFolder),
                                 ('File', None, '_File'),
                                 ('RadioBand', None, 'Fil_ters'),
                                 ('Play/Stop', gtk.STOCK_MEDIA_PLAY, None, None, 'Play Selection', self.control.playStopSelected),
                                 ('Previous', gtk.STOCK_MEDIA_PREVIOUS, None, None, 'Previous', self.control.previousTrack),
                                 ('Next', gtk.STOCK_MEDIA_NEXT, None, None, 'Next', self.control.nextTrack),
                                 ('Help', None, '_Help'),
                                 ('About', gtk.STOCK_ABOUT, 'About CometSound', None, 'About CometSound', self.showAboutDialog)
                                 ])

        # Create ToggleActions
        actiongroup.add_toggle_actions([('Mp3', None, '_Mp3', '<Control>m',
                                        'MPEG-1 Audio Layer 3', self.control.toggleMp3, self.formatDict[".mp3"]),
                                       ('Wma', None, '_Wma', '<Control>w',
                                        'Windows Media Audio', self.control.toggleWma, self.formatDict[".wma"]),
                                       ('Ogg', None, 'O_gg', '<Control>g',
                                        'Ogg Vorbis', self.control.toggleOgg, self.formatDict[".ogg"]),
                                       ], None)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string('''<ui>
                                        <menubar name="MenuBar">
                                          <menu action="File">
                                            <menuitem action="Open"/>
                                            <menuitem action="Quit"/>
                                          </menu>
                                          <menu action="RadioBand">
                                            <menuitem action="Mp3"/>
                                            <menuitem action="Wma"/>
                                            <menuitem action="Ogg"/>
                                          </menu>
                                          <menu action="Help">
                                            <menuitem action="About"/>
                                          </menu>
                                        </menubar>
                                        <toolbar name="ToolBar">
                                            <toolitem action="Play/Stop"/>
                                            <toolitem action="Previous"/>
                                            <toolitem action="Next"/>
                                            <separator/>
                                            <toolitem action="Open"/>
                                            <separator name="sep1"/>
                                        </toolbar>
                                        </ui>''')

        # Create a MenuBar
        menubar = uimanager.get_widget('/MenuBar')
        toolbar = uimanager.get_widget('/ToolBar')
        #toolbar.set_size_request(170, 50)
        
        # Create a Label to show track info
        self.label = gtk.Label('\n\n')
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.label.set_padding(0, 5)
        tl = gtk.ToolItem()
        tl.add(self.label)
        tl.set_expand(True)
        toolbar.insert(tl, -1)
                
        # Create a button to control player volume
        self.volume = gtk.VolumeButton()
        self.volume.set_value(10)
        self.volume.connect('value-changed', self.control.playerThread.onVolumeChanged)
        tv = gtk.ToolItem()
        tv.add(self.volume)
        toolbar.insert(tv, -1)
        
        
        #self.hbox.pack_end(self.volume, False)
        #self.hbox.pack_end(self.label, True)
        self.hbox.pack_start(toolbar, True)
        
        # Create a slider to show player progress
        self.adjustment = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
        hscale = gtk.HScale(self.adjustment)
        hscale.set_digits(2)
        hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        hscale.set_value_pos(gtk.POS_RIGHT)
        hscale.connect('value-changed', self.control.playerThread.onSliderChange)
        hscale.connect('button-press-event', self.control.playerThread.pause)
        hscale.connect('button-release-event', self.control.playerThread.play)
        hscale.connect('format-value', self.control.sliderFormat)
        self.slider = hscale
        self.slider.set_sensitive(False)
        
        self.buttons = gtk.HBox()
        cIcon = gtk.Image()
        cIcon.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_SMALL_TOOLBAR) 
        clearB = gtk.Button()
        clearB.add(cIcon)
        clearB.set_tooltip_text('Clear Playlist')
        clearB.connect("clicked", self.control.clearPlaylist)
        aIcon = gtk.Image()
        aIcon.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR)
        addAllB = gtk.Button()
        addAllB.add(aIcon)
        addAllB.set_tooltip_text('Select All')
        addAllB.connect("clicked", self.control.addAll, True)
        rIcon = gtk.Image()
        rIcon.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_SMALL_TOOLBAR)
        removeAllB = gtk.Button()
        removeAllB.add(rIcon)
        removeAllB.set_tooltip_text('Deselect All')
        removeAllB.connect("clicked", self.control.addAll, False)
        refIcon = gtk.Image()
        refIcon.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_SMALL_TOOLBAR)
        refreshB = gtk.Button()
        refreshB.add(refIcon)
        refreshB.set_tooltip_text('Refresh')
        refreshB.connect("clicked", self.control.refreshTree)
        rsIcon = gtk.Image()
        rsIcon.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        removeSelectedB = gtk.Button()
        removeSelectedB.add(rsIcon)
        removeSelectedB.set_tooltip_text('Remove Selection')
        removeSelectedB.connect("clicked", self.control.removeSelected)
        sIcon = gtk.Image()
        theme = gtk.icon_theme_get_for_screen(self.get_screen())
        pixbuf = theme.choose_icon(['stock_shuffle'], 18, 0).load_icon()
        sIcon.set_from_pixbuf(pixbuf)
        shuffleB = gtk.Button()
        shuffleB.add(sIcon)
        shuffleB.set_tooltip_text('Shuffle')
        shuffleB.connect("clicked", self.control.shufflePlaylist)
        self.buttons.pack_start(addAllB, False)
        self.buttons.pack_start(removeAllB, False)
        self.buttons.pack_start(refreshB, False)
        self.buttons.pack_start(gtk.Label(), True)
        self.buttons.pack_start(shuffleB, False)
        self.buttons.pack_start(clearB, False)
        self.buttons.pack_start(removeSelectedB, False)
        
        self.filesTree = FilesFrame(self.model, self.control, self.formatDict)
        self.playlistFrame = PlaylistFrame(self.control, [])
        
        self.framebox.add(self.filesTree)
        self.framebox.add(self.playlistFrame)
        
        # Create a progress bar to show during the model creation
        self.progressBar = gtk.ProgressBar()
        self.progressBar.set_properties('min-horizontal-bar-height', 10)
                                     
        self.vbox.pack_start(menubar, False)
        self.vbox.pack_start(self.hbox, False)
        self.vbox.pack_start(self.slider, False)
        self.vbox.pack_start(self.buttons, False)
        self.vbox.pack_start(self.framebox, True)
        self.show_all()
        self.filesTree.setModel(self.model)
        
    def getFormatDict(self):
        return self.formatDict     
    
    def setButtonPlay(self):
        """Sets the button to "play" during playing"""
        self.actiongroup.get_action('Play/Stop').set_stock_id(gtk.STOCK_MEDIA_PLAY)
        self.actiongroup.get_action('Play/Stop').set_tooltip('Play')
    
    def setButtonPause(self):
        """Sets the button to "pause" """
        self.actiongroup.get_action('Play/Stop').set_stock_id(gtk.STOCK_MEDIA_PAUSE)
        self.actiongroup.get_action('Play/Stop').set_tooltip('Pause')
    
    def fixFrameboxPos(self, widget, event):
        """Fixes the position of the HPaned separator when window's size changes"""
        self.maximized = not self.maximized
        size = self.get_size_request()
        if self.maximized:
            self.framebox.set_position(int(size[1] * 2.5))
        else:
            self.framebox.set_position(int(size[1] * 1.2))
    
    def showAboutDialog(self, o):
        about = gtk.AboutDialog()
        about.set_name('CometSound')    
        about.set_version(self.version)
        about.set_copyright(u'Copyright \u00A9 2010 Andrea Bernardini')
        about.set_website('https://launchpad.net/cometsound')
        pix = self.icon.get_pixbuf().scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
        about.set_logo(pix)
        response = about.run()
        if response == -6:
            about.hide()
            
    def quit(self, o):
        self.destroy()
        
    def destroy(self):
        self.control.playerThread.stop()
        if self.control.playerThread.isAlive():
            self.control.playerThread.terminate()    
        gtk.main_quit()
        
class FilesFrame(gtk.Frame):
    """Gtk Frame modified to store a treeview that shows all the audio files inside the selected folder"""
    
    columns = ['Name', '#', 'Title', 'Artist', 'Album', 'Genre', 'Year', 'Add', '']
        
    def __init__(self, model, control, formatDict):
        
        gtk.Frame.__init__(self)
        self.listOfFiles = model.getAudioFileList()
        self.formatDict = formatDict
        self.control = control
        
        #self.set_label("Files selection:")
        
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_border_width(0)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # create a treeStore with one string column to use as the model
        s = gobject.TYPE_STRING
        g = gobject.TYPE_BOOLEAN
        self.treeStore = gtk.TreeStore(s, s, s, s, s, s, s, g, s)

        self.createTree(None, self.listOfFiles)
        # create and sort the TreeView using treeStore
        self.treeStore.set_sort_func(10, SF.sortNameFunc, self.columns.index('Name'))
        self.treeStore.set_sort_func(11, SF.sortNumFunc, self.columns.index('#'))
        self.treeStore.set_sort_func(12, SF.sortNumFunc, self.columns.index('Year'))
        self.treeStore.set_sort_column_id(10, gtk.SORT_ASCENDING)
        self.treeview = gtk.TreeView(self.treeStore)
        self.treeview.set_rules_hint(True)
        self.treeview.connect("button-press-event", self.control.doubleClickSelect)
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
                    self.treeStore.append(parent, f.getTagValues() + [None] + [f.getDir() + f.getTagValues()[0]])
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
            if column == 'Add':
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
                if column == 'Name':
                    tvcolumn.set_sort_column_id(10) 
                if column == 'Year':
                    tvcolumn.set_sort_column_id(12) 
                if column == 'Title':
                    tvcolumn.set_sort_column_id(2)
                if column == 'Artist':
                    tvcolumn.set_sort_column_id(3)    
                if column == 'Album':
                    tvcolumn.set_sort_column_id(6)
                if column == 'Genre':
                    tvcolumn.set_sort_column_id(5)                              
                if column == '' :
                    tvcolumn.set_expand(False)
                    tvcolumn.set_max_width(0)
                    tvcolumn.set_visible(False)
            i = i + 1
      
    def setModel(self, model):
        """Sets a new model to show"""
        self.listOfFiles = model.getAudioFileList()
        self.treeStore.clear()
        self.createTree(None, self.listOfFiles)
     
    
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
        self.setupDnD()
        
        playCell = gtk.CellRendererPixbuf()
        tvcolumn = gtk.TreeViewColumn()
        self.treeview.append_column(tvcolumn)
        tvcolumn.pack_start(playCell, False)    
        tvcolumn.add_attribute(playCell, 'stock-id', 0)
        tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        tvcolumn.set_resizable(True)   
        
        titleCell = gtk.CellRendererText()
        tvcolumn = gtk.TreeViewColumn('Playlist')
        self.treeview.append_column(tvcolumn)
        tvcolumn.pack_start(titleCell, False)    
        tvcolumn.add_attribute(titleCell, 'text', 1)
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
    
import AF, cerealizer
import mutagen.asf as mtgasf
    
def registerClasses():
    cerealizer.register(mtgasf.ASFUnicodeAttribute)
    cerealizer.register(mtgasf.ASFDWordAttribute)
    cerealizer.register(AF.AudioFile)            
            
def main():
    gtk.main()
    return 0
if __name__ == "__main__":
    registerClasses()
    m = Model.Model('')
    c = Controller.Controller(m)
    View(m, c)
    main()       
