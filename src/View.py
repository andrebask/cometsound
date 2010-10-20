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

import gtk, pygtk
pygtk.require('2.0')
from FileBrowser import FilesFrame
from Dialogs import AboutDialog, PreferencesDialog
from Playlist import PlaylistFrame
import CometSound

version = '0.1.1'
_ = CometSound.t.getTranslationFunc()

class View(gtk.Window):
    
    
    formatDict = {'.mp3': True, '.wma': True, '.ogg': True, 'flac': True}
        
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
        self.pix = self.icon.get_pixbuf().scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
        self.set_icon(self.pix)
        self.tray = None
        if self.control.settings['statusicon'] == (0 or 1):
            self.setStatusIcon()
        
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
        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, _('_Quit'), None, _('Quit the program'), self.quit),
                                 ('Open', gtk.STOCK_OPEN, _('_Open folder...'), None, _('Open media folder'), self.control.openFolder),
                                 ('Preferences', gtk.STOCK_PREFERENCES, _('Preferences'), None, _('Change settings'), self.openPreferences),
                                 ('File', None, _('_File')),
                                 ('RadioBand', None, _('Fil_ters')),
                                 ('Play/Stop', gtk.STOCK_MEDIA_PLAY, None, None, _('Play selection'), self.control.playStopSelected),
                                 ('Previous', gtk.STOCK_MEDIA_PREVIOUS, None, None, _('Previous'), self.control.previousTrack),
                                 ('Next', gtk.STOCK_MEDIA_NEXT, None, None, _('Next'), self.control.nextTrack),
                                 ('Help', None, _('_Help')),
                                 ('About', gtk.STOCK_ABOUT, _('About CometSound'), None, _('About CometSound'), self.showAboutDialog)
                                 ])

        # Create ToggleActions
        actiongroup.add_toggle_actions([('Mp3', None, '_Mp3', '<Control>m',
                                        'MPEG-1 Audio Layer 3', self.control.toggleMp3, self.formatDict[".mp3"]),
                                       ('Wma', None, '_Wma', '<Control>w',
                                        'Windows Media Audio', self.control.toggleWma, self.formatDict[".wma"]),
                                       ('Ogg', None, 'O_gg', '<Control>g',
                                        'Ogg Vorbis', self.control.toggleOgg, self.formatDict[".ogg"]),
                                       ('Flac', None, '_Flac', '<Control>f',
                                        'Ogg Vorbis', self.control.toggleFlac, self.formatDict["flac"])
                                       ], None)

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
                                          <menu action="RadioBand">
                                            <menuitem action="Mp3"/>
                                            <menuitem action="Wma"/>
                                            <menuitem action="Ogg"/>
                                            <menuitem action="Flac"/>
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
        self.label.set_line_wrap(True)
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
        clearB.set_tooltip_text(_('Clear Playlist'))
        clearB.connect("clicked", self.control.clearPlaylist)
        aIcon = gtk.Image()
        aIcon.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR)
        addAllB = gtk.Button()
        addAllB.add(aIcon)
        addAllB.set_tooltip_text(_('Select All'))
        addAllB.connect("clicked", self.control.addAll, True)
        rIcon = gtk.Image()
        rIcon.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_SMALL_TOOLBAR)
        removeAllB = gtk.Button()
        removeAllB.add(rIcon)
        removeAllB.set_tooltip_text(_('Deselect All'))
        removeAllB.connect("clicked", self.control.addAll, False)
        refIcon = gtk.Image()
        refIcon.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_SMALL_TOOLBAR)
        refreshB = gtk.Button()
        refreshB.add(refIcon)
        refreshB.set_tooltip_text(_('Refresh'))
        refreshB.connect("clicked", self.control.refreshTree)
        rsIcon = gtk.Image()
        rsIcon.set_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        removeSelectedB = gtk.Button()
        removeSelectedB.add(rsIcon)
        removeSelectedB.set_tooltip_text(_('Remove Selection'))
        removeSelectedB.connect("clicked", self.control.removeSelected)
        sIcon = gtk.Image()
        theme = gtk.icon_theme_get_for_screen(self.get_screen())
        pixbuf = theme.choose_icon(['stock_shuffle'], 18, 0).load_icon()
        sIcon.set_from_pixbuf(pixbuf)
        shuffleB = gtk.Button()
        shuffleB.add(sIcon)
        shuffleB.set_tooltip_text(_('Shuffle'))
        shuffleB.connect("clicked", self.control.shufflePlaylist)
        self.buttons.pack_start(addAllB, False)
        self.buttons.pack_start(removeAllB, False)
        self.buttons.pack_start(refreshB, False)
        self.buttons.pack_start(gtk.Label(), True)
        self.buttons.pack_start(shuffleB, False)
        self.buttons.pack_start(clearB, False)
        self.buttons.pack_start(removeSelectedB, False)
        
        self.columns = [_('Name'), '#', _('Title'), _('Artist'), _('Album'), _('Genre'), _('Year'), _('Add'), '']
        self.filesTree = FilesFrame(self.model, self.control, self.formatDict, self.columns)
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
    
    def setStatusIcon(self):
        pix = self.pix
        if self.tray != None:
            self.tray.set_visible(False)
        if self.control.settings['statusicon'] != 2:    
            self.tray = gtk.StatusIcon()
            pix = pix.scale_simple(20, 20, gtk.gdk.INTERP_BILINEAR)
            self.tray.set_from_pixbuf(pix)
            self.tray.connect('popup-menu', self.openMenu) 
            self.tray.connect('activate', self.minimize) 
    
    def minimize(self, obj = None):
        if self.get_visible():
            self.hide()
        else:
            self.show()
        
    def openMenu(self, icon, event_button, event_time):    
        statusMenu = gtk.Menu()
        
        if self.label.get_text() != '\n\n' and self.control.settings['statusicon'] == 0:
            label = gtk.MenuItem(self.label.get_text())
            label.show()
            statusMenu.append(label)
            
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
        
        statusMenu.popup(None, None, gtk.status_icon_position_menu,
                   event_button, event_time, self.tray)
        
    def openPreferences(self, obj = None):
        p = PreferencesDialog(self.columns, self.control)
        
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
        
    def fixFrameboxPos(self, widget, event):
        """Fixes the position of the HPaned separator when window's size changes"""
        self.maximized = not self.maximized
        size = self.get_size_request()
        if self.maximized:
            self.framebox.set_position(int(size[1] * 2.5))
        else:
            self.framebox.set_position(int(size[1] * 1.2))
    
    def showAboutDialog(self, o):
        ad = AboutDialog(self.icon, version)
        
            
    def quit(self, obj = None):
        self.destroy()
        
    def destroy(self):
        self.control.playerThread.stop()
        if self.control.playerThread.isAlive():
            self.control.playerThread.terminate()    
        gtk.main_quit()
        