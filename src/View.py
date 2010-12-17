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

import gtk, pygtk, os
pygtk.require('2.0')
from Translator import t
from Dialogs import AboutDialog, PreferencesDialog, SavePlaylistDialog
from Playlist import PlaylistFrame
from FileBrowser import FilesFrame
from Model import audioTypes
from AlbumCover import AlbumImage, Global

version = '0.3.2'
_ = t.getTranslationFunc()

columns = [_('Name'), '#', _('Title'), _('Artist'),
            _('Album'), _('Genre'), _('Year'), _('Add')]

defaultSettings = {'audiosink': 'autoaudiosink',
                    'statusicon': 0,    
                    '#': True,
                     _('Title'): True,
                     _('Artist'): True,
                      _('Album'): True,
                       _('Genre'): True,
                        _('Year'): True,
                        'lastplaylist': True,
                        'foldercache': True 
                         }

class View(gtk.Window):
    
    
    formatDict = {'mp3': True, 'wma': True, 'ogg': True, 'flac': True, 
                  'm4a': True, 'mp4': True, 'aac': True, 'wav': True,
                  'ape': True, 'mpc': True, 'wv': True}
        
    def __init__(self, model, control):
        
        gtk.Window.__init__(self)
        self.model = model
        self.control = control
        self.set_title('CometSound')
        self.control.registerView(self)
        
        
        # Create the toplevel window
        self.connect('destroy', lambda w: self.destroy())
        minwidth = 733 #int(self.get_screen().get_width() / 2.5)
        minheight = 420 #int(self.get_screen().get_height() / 2.5)
        try:
            self.width, self.height, framepos, self.volume = self.control.readWinSize()
        except:
            self.width = minwidth
            self.height = minheight
            framepos = int(minwidth * 0.7)
            self.volume = 10
        self.set_size_request(minwidth, minheight)
        self.resize(self.width, self.height) 
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('expose-event', self.storeSize)
        self.icon = gtk.Image()
        self.icon.set_from_file("icon.png")
        self.pix = self.icon.get_pixbuf().scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
        self.set_icon(self.pix)
        self.tray = None
        
        self.createSlider()
        
        self.createPrimaryToolbar()
        
        self.setStatusIcon()
        
        self.columns = columns
        self.filesTree = FilesFrame(self.model, self.control, self.formatDict, self.columns)
        self.playlistFrame = PlaylistFrame(self.control, [])
        
        self.framebox.pack1(self.filesTree)
        self.framebox.pack2(self.playlistFrame, False, False)
        self.framebox.set_position(framepos)
        self.control.createPlaylist()
        # Create a progress bar to show during the model creation
        self.progressBar = gtk.ProgressBar()
        self.progressBar.set_properties('min-horizontal-bar-height', 10)
        sbar = gtk.Statusbar()
        sbar.set_size_request(0,14)
        
        self.vbox.set_spacing(0)                             
        self.vbox.pack_start(self.menubar, False)
        self.vbox.pack_start(self.imageToolbar, False)
        self.vbox.pack_start(self.hbox, False)
        #self.vbox.pack_start(self.slider, False)
        self.vbox.pack_start(self.framebox, True)
        self.vbox.pack_start(sbar, False)
        self.show_all()
        self.filesTree.setModel(self.model)
        self.filesTree.treeview.grab_focus()
        self.control.refreshTree()
        if self.model.playlist != None:
            self.control.playStopSelected()
        
    def createPrimaryToolbar(self):
        self.vbox = gtk.VBox()
        self.add(self.vbox)       
        
        self.hbox = gtk.HBox()
        self.framebox = gtk.HPaned()
        # Create a UIManager instance
        uimanager = gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup

        
        # Create actions
        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, _('_Quit'), None, _('Quit the program'), self.quit),
                                 ('Open', gtk.STOCK_OPEN, _('_Open folder...'), None, _('Open media folder'), self.control.openFolder),
                                 ('Preferences', gtk.STOCK_PREFERENCES, _('Preferences'), '<Control>P', _('Change settings'), self.openPreferences),
                                 ('File', None, _('_File')),
                                 ('RadioBand', None, _('Fil_ters')),
                                 ('Play/Stop', gtk.STOCK_MEDIA_PLAY, None, None, _('Play selection'), self.control.playStopSelected),
                                 ('Previous', gtk.STOCK_MEDIA_PREVIOUS, None, None, _('Previous'), self.control.previousTrack),
                                 ('Next', gtk.STOCK_MEDIA_NEXT, None, None, _('Next'), self.control.nextTrack),
                                 ('Playlists', None, _('Playlists')),
                                 ('PlaylistsFolder', None, _('Open folder...'), None, None, self.openPlaylistFolder),
                                 ('Help', None, _('_Help')),
                                 ('About', gtk.STOCK_ABOUT, _('About CometSound'), None, _('About CometSound'), self.showAboutDialog)
                                 ])
        
        actions = self.control.readPlaylists()
        uilist = ''
        for act in actions:
            actiongroup.add_actions([(act, None, act, None, None, self.control.loadPlaylist)])
            uilist = uilist + '<menuitem action="%s"/>' % (act)

        # Create ToggleActions
        list = []
        for type in audioTypes:
            label = type[1:].capitalize()
            actiongroup.add_toggle_actions([(label, None, label, None, None,self.control.toggleFilter, True)], None)
            list.append(label)
        list.sort()
        uitogglelist = ''
        for label in list:
            uitogglelist = uitogglelist + '<menuitem action="%s"/>' % (label)    

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string('''<ui>
                                        <menubar name="MenuBar">
                                          <menu action="File">
                                            <menuitem action="Open"/>
                                            <menuitem action="Preferences"/>
                                            <menuitem action="Quit"/>
                                          </menu>
                                          <menu action="RadioBand">'''
                                            + uitogglelist +
                                       '''</menu>
                                          <menu action="Playlists">
                                            <menuitem action="PlaylistsFolder"/>'''
                                            + uilist +
                                      ''' </menu>
                                          <menu action="Help">
                                            <menuitem action="About"/>
                                          </menu>
                                        </menubar>
                                        <toolbar name="ImageToolBar">
                                            <toolitem action="Open"/>
                                        </toolbar>
                                        <toolbar name="ToolBar">
                                            <toolitem action="Previous"/>
                                            <toolitem action="Play/Stop"/>
                                            <toolitem action="Next"/>
                                            <separator/>
                                            <separator name="sep1"/>
                                        </toolbar>
                                        </ui>''')
        self.actiongroup = actiongroup
        self.uimanager = uimanager
        
        # Create a MenuBar
        self.menubar = uimanager.get_widget('/MenuBar')
        toolbar = uimanager.get_widget('/ToolBar')
        imageToolbar = uimanager.get_widget('/ImageToolBar')
        #toolbar.set_size_request(170, 50)
        
        # Create an Image to show the album's cover
        self.image = AlbumImage()
        box = gtk.HBox()
        box.pack_start(self.image, True)
        box.set_border_width(6)
        tv = gtk.ToolItem()
        tv.add(box)
        imageToolbar.insert(tv, 0)
        
        # Create a Label to show track info
        self.label = gtk.Label()
        self.label.set_justify(gtk.JUSTIFY_LEFT)
        self.label.set_alignment(0, 0)
        self.label.set_padding(9, 10)
        #self.label.set_line_wrap(True)
        self.slider.connect('expose-event', self.image.updateImage)
        box = gtk.HBox()
        box.pack_start(self.label, True)
        #box.pack_start(gtk.Label(), False)
        tl = gtk.ToolItem()
        tl.add(box)
        tl.set_expand(True)
        imageToolbar.insert(tl, 1)
                
        # Create a button to control player volume
        self.volumeButton = gtk.VolumeButton()
        self.volumeButton.set_value(self.volume)
        self.volumeButton.connect('value-changed', self.control.playerThread.onVolumeChanged)
        tv = gtk.ToolItem()
        tv.add(self.volumeButton)
        imageToolbar.insert(tv, 3)
        
        tl = gtk.ToolItem()
        tl.add(self.slider)
        tl.set_expand(True)
        toolbar.insert(tl, -1)
        
        tl = gtk.ToolItem()
        l = gtk.Label()
        l.set_size_request(19,0)
        tl.add(l)
        toolbar.insert(tl, 3)
        
        tl = gtk.ToolItem()
        l = gtk.Label()
        l.set_size_request(9,0)
        tl.add(l)
        toolbar.insert(tl, 0)
        
        tl = gtk.ToolItem()
        l = gtk.Label()
        l.set_size_request(12,0)
        tl.add(l)
        toolbar.insert(tl, -1)
        
        tl = gtk.ToolItem()
        l = gtk.Label()
        l.set_size_request(7,0)
        tl.add(l)
        imageToolbar.insert(tl, -1)
        
        self.imageToolbar = imageToolbar
        self.hbox.pack_start(toolbar, True)
    
    def updatePlaylistsMenu(self, newPlaylist):
        self.actiongroup.add_actions([(newPlaylist, None, newPlaylist, None, None, self.control.loadPlaylist)])
        merge_id = self.uimanager.new_merge_id()
        self.uimanager.add_ui(merge_id, 'ui/MenuBar/Playlists', newPlaylist, newPlaylist, gtk.UI_MANAGER_MENUITEM, False)
        
    def createSlider(self):
        # Create a slider to show player progress
        self.adjustment = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
        hscale = gtk.HScale(self.adjustment)
        hscale.set_digits(2)
        hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        hscale.set_value_pos(gtk.POS_RIGHT)
        hscale.connect('value-changed', self.control.playerThread.onSliderChange)
        hscale.connect('button-press-event', self.control.sliderClickPress)
        hscale.connect('button-release-event', self.control.sliderClickRelease)
        hscale.connect('format-value', self.control.sliderFormat)
        self.slider = hscale
        self.slider.set_sensitive(False)
    
    def createButton(self, imageStock, tooltip, func, data = None):
        Icon = gtk.Image()
        Icon.set_from_stock(imageStock, gtk.ICON_SIZE_SMALL_TOOLBAR) 
        B = gtk.Button()
        B.add(Icon)
        B.set_tooltip_text(tooltip)
        B.connect("clicked", func, data)        
        return B
    
    def setStatusIcon(self):
        pix = self.pix
        try:
            mode = self.control.settings['statusicon']
        except:
            mode = 0    
        if self.tray != None:
            self.tray.set_visible(False)
        if mode != 2:    
            self.tray = gtk.StatusIcon()
            pix = pix.scale_simple(20, 20, gtk.gdk.INTERP_BILINEAR)
            self.tray.set_from_pixbuf(pix)
            self.tray.connect('popup-menu', self.openMenu) 
            self.tray.connect('activate', self.minimize) 
            
        statusMenu = gtk.Menu()
        if self.control.settings['statusicon'] == 0:
            self.menulabel = gtk.MenuItem(self.label.get_text())
            statusMenu.append(self.menulabel)
            
            sep = gtk.SeparatorMenuItem()
            sep.show()
            statusMenu.append(sep)
        
        statusPlay = gtk.CheckMenuItem(_('Play'))
        statusPlay.set_active(self.control.playerThread.playing)
        statusPlay.show()
        statusMenu.append(statusPlay)
        statusPlay.connect('toggled', self.control.playStopSelected)
        
        next = gtk.MenuItem(_('Next'))
        next.show()
        statusMenu.append(next)
        next.connect('activate', self.control.nextTrack)
        
        previous = gtk.MenuItem(_('Previous'))
        previous.show()
        statusMenu.append(previous)
        previous.connect('activate', self.control.previousTrack)
        
        quit = gtk.MenuItem(_('Quit'))
        quit.show()
        statusMenu.append(quit)
        quit.connect('activate', self.quit)    
        self.statusMenu = statusMenu    
    
    def openMenu(self, icon, event_button, event_time):    
        if self.label.get_text() != '\n\n' and self.control.settings['statusicon'] == 0:
            self.statusMenu.remove(self.menulabel)
            self.menulabel = gtk.MenuItem(self.label.get_text())
            self.menulabel.show()
            self.statusMenu.prepend(self.menulabel)
        self.statusMenu.popup(None, None, gtk.status_icon_position_menu,
                   event_button, event_time, self.tray)
            
    def minimize(self, obj = None):
        if self.get_visible():
            self.hide()
        else:
            self.show()
        
    def openPreferences(self, obj = None):
        try:
            p = PreferencesDialog(self.columns, self.control, self.control.settings)
        except:
            self.control.settings = defaultSettings
            p = PreferencesDialog(self.columns, self.control, defaultSettings)
            
    def openPlaylistFolder(self, widget, data=None):
        cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")
        dir = os.path.join(cacheDir, 'playlists')
        if not os.path.exists(dir):
            os.makedirs(dir)
        os.system('xdg-open %s' % dir)
    
    def savePlaylistDialog(self, widget, data=None):
        d = SavePlaylistDialog(self.control)
        
    def getFormatDict(self):
        return self.formatDict     
    
    def setButtonPlay(self):
        """Sets the button to "play" during playing"""
        self.actiongroup.get_action('Play/Stop').set_stock_id(gtk.STOCK_MEDIA_PLAY)
        self.actiongroup.get_action('Play/Stop').set_tooltip(_('Play'))    
        
    def setButtonPause(self):
        """Sets the button to "pause" """
        self.actiongroup.get_action('Play/Stop').set_stock_id(gtk.STOCK_MEDIA_PAUSE)
        self.actiongroup.get_action('Play/Stop').set_tooltip(_('Pause'))
    
    def storeSize(self, widget, event):
        all = widget.get_allocation()
        self.width, self.height = all.width, all.height
    
    def showAboutDialog(self, o):
        ad = AboutDialog(self.icon, version)
        
            
    def quit(self, obj = None):
        self.destroy()
        
    def destroy(self):
        Global.stop = True
        self.control.saveCache()
        pos = self.framebox.get_position()
        volume = self.control.playerThread.getVolume()
        self.control.saveWinSize(self.width, self.height, pos, volume)
        self.control.playerThread.stop()
        #self.control.modelUpdater.terminate()
        if self.control.playerThread.isAlive():
            self.control.playerThread.terminate()
        gtk.main_quit()
        