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

from Common import gtk, gtkTrick
from Common import _

from Scrobbler import Scrobbler
from Scrobbler import md5
from Scrobbler import pylastInstalled

class AboutDialog(gtk.AboutDialog):
    """Shows general informations of CometSound"""
    
    def __init__(self, icon, version):  
        gtk.AboutDialog.__init__(self)
        self.set_name('CometSound')    
        self.set_version(version)
        self.set_copyright(u'Copyright \u00A9 2010-2011 Andrea Bernardini')
        self.set_website('https://launchpad.net/cometsound')
        pix = icon.get_pixbuf().scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
        self.set_logo(pix)
        
        response = self.run()
        if response == gtk.RESPONSE_CANCEL or response == gtk.RESPONSE_DELETE_EVENT:
            self.destroy()
            
class SavePlaylistDialog(gtk.Dialog):
    """Allows to give a name to a playlist and save it"""
    
    def __init__(self, control):
        gtk.Dialog.__init__(self)
        self.set_title(_('Save Playlist'))
        self.set_size_request(250, 100)
        l = gtk.Label(_('Insert playlist name:'))
        e = gtk.Entry()
        vbox = self.get_child()
        vbox.pack_start(l)
        vbox.pack_start(e)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        self.show_all()
        
        response = self.run()
        if response == gtk.RESPONSE_OK:
            control.savePlaylist(e.get_text())
            self.destroy()
        if response == gtk.RESPONSE_CANCEL or response == gtk.RESPONSE_DELETE_EVENT:
            self.destroy()
                
class PreferencesDialog(gtk.Dialog):
    """Allows to set the program options"""
    
    def __init__(self, columns, control, settings):
        gtk.Dialog.__init__(self)
        self.set_size_request(300,400)
        self.control = control
        
        ########################
        ###   General Page   ###
        ########################
        
        self.set_title(_('CometSound preferences'))
        sinks = ['Auto', 'ALSA', 'PulseAudio', 'OSS', 'Jack']
        gstSinks = ['autoaudiosink', 'alsasink', 'pulsesink', 'osssink', 'jackaudiosink']
        dialogBox = self.get_child()
        vbox = gtk.VBox()
        audioLabel = gtk.Label()
        audioLabel.set_alignment(0,0)
        audioLabel.set_padding(5,6)
        audioLabel.set_markup(_('<b>Audio output (Restart required)</b>'))
        audioCombo = gtk.combo_box_new_text()
        acombo = gtk.HBox()
        acombo.pack_start(gtk.Label('     '), False)
        acombo.pack_start(audioCombo)
        acombo.pack_start(gtk.Label('  '), False)
        for s in sinks:
            audioCombo.append_text(s)
        audioCombo.set_active(gstSinks.index(settings['audiosink']))
        
        columnsLabel = gtk.Label()
        columnsLabel.set_alignment(0,0)
        columnsLabel.set_padding(5,6)
        columnsLabel.set_markup(_('<b>Visible columns</b>'))
        labels = dict()
        cbox1 = gtk.VButtonBox() 
        cbox1.set_layout(gtk.BUTTONBOX_START)
        cbox2 = gtk.VButtonBox() 
        cbox2.set_layout(gtk.BUTTONBOX_START)
        hbox = gtk.HBox()
        hbox.pack_start(cbox1)
        hbox.pack_start(cbox2)
        count = 0
        #print settings.keys()
        for c in columns:
            if c != '' and c != _('Name') and c != _('Add'):
                cb = gtk.CheckButton(c)
                labels[c] = cb
                cb.set_active(settings[c])
                if count % 2 == 0:
                    cbox1.pack_start(cb)
                else:
                    cbox2.pack_start(cb)    
                count+=1
                
        statusLabel = gtk.Label()
        statusLabel.set_alignment(0,0)
        statusLabel.set_padding(5,6)
        statusLabel.set_markup(_('<b>Status Icon</b>'))
        statusCombo = gtk.combo_box_new_text()
        statusCombo.append_text(_('Enable status icon with track\'s informations'))
        statusCombo.append_text(_('Enable status icon'))
        statusCombo.append_text(_('Disable status icon'))
        statusCombo.set_active(settings['statusicon'])
        scombo = gtk.HBox()
        scombo.pack_start(gtk.Label('     '), False)
        scombo.pack_start(statusCombo)
        scombo.pack_start(gtk.Label('  '), False)
        
        startupLabel = gtk.Label()
        startupLabel.set_alignment(0,0)
        startupLabel.set_padding(5,6)
        startupLabel.set_markup(_('<b>Startup settings</b>'))
        startbox = gtk.VButtonBox() 
        startbox.set_layout(gtk.BUTTONBOX_START)
        playcb = gtk.CheckButton(_('Reload last play queue'))
        playcb.set_active(settings['lastplaylist'])
        cachecb = gtk.CheckButton(_('Reload last folder'))
        cachecb.set_active(settings['foldercache'])
        startbox.pack_start(playcb)
        startbox.pack_start(cachecb)
                
        vbox.pack_start(audioLabel)
        vbox.pack_start(acombo)
        vbox.pack_start(columnsLabel)
        vbox.pack_start(hbox) 
        vbox.pack_start(statusLabel)
        vbox.pack_start(scombo)
        vbox.pack_start(startupLabel)
        vbox.pack_start(startbox)
        
        ########################
        ###   Library Page   ###
        ########################
        
        lvbox = gtk.VBox()
        lLabel = gtk.Label()
        lLabel.set_alignment(0,0)
        lLabel.set_padding(5,6)
        lLabel.set_markup(_('<b>Music Library location</b>'))
        
        folderChooser = gtk.FileChooserDialog(_('Select Folder...'), None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                               (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        entrybox = gtk.HBox()
        #pathEntry = gtk.Entry()
        browseButton = gtk.FileChooserButton(folderChooser)
        browseButton.set_border_width(5)
        browseButton.set_current_folder(settings['libraryFolder'])
        #entrybox.pack_start(pathEntry)
        entrybox.pack_start(browseButton)
        entrybox.set_border_width(5)
        
        libbox = gtk.VButtonBox() 
        libbox.set_layout(gtk.BUTTONBOX_START)
        librarycb = gtk.CheckButton(_('Enable library mode'))
        librarycb.set_active(settings['libraryMode'])
        libbox.pack_start(librarycb)
                
        lvbox.pack_start(lLabel, False, False)
        lvbox.pack_start(libbox, False, False)
        lvbox.pack_start(entrybox, False, False) 
        lvbox.set_spacing(0)
        
        ##########################
        ###   Scrobbler Page   ###
        ##########################
        
        svbox = gtk.VBox()
        self.pwdChanged = False
        self.userChanged = False
        
        scrobblerLabel = gtk.Label()
        scrobblerLabel.set_alignment(0,0)
        scrobblerLabel.set_padding(5,6)
        scrobblerLabel.set_markup(_('<b>Last.fm login</b>'))
        
        uhbox = gtk.HBox()
        ulabel = gtk.Label(_('Username:'))
        ulabel.set_alignment(0,0.5)
        ulabel.set_padding(10, 0)
        ulabel.set_size_request(45,40)
        uentry = gtk.Entry()
        uentry.set_text(settings['user'])
        uentry.connect('changed', self.setUserChanged)
        
        phbox = gtk.HBox()
        plabel = gtk.Label(_('Password:'))
        plabel.set_alignment(0,0.5)
        plabel.set_padding(10, 0)
        plabel.set_size_request(45,40)
        pentry = gtk.Entry()
        pentry.set_text(settings['fakepwd'])
        pentry.set_visibility(False)
        self.emptyentry = len(pentry.get_text()) == 0
        pentry.connect('changed', self.setPwdChanged)
        
        cbhbox = gtk.HBox()
        loginbox = gtk.HBox()
        scrobblercb = gtk.CheckButton(_('Enable scrobbling'))
        scrobblercb.set_active(settings['scrobbler'])
        scrobblercb.connect('toggled', self.hideLoveIcon)
        cbhbox.pack_start(scrobblercb)
        cbhbox.set_border_width(10)
        loginImage = gtk.Image()
        self.loginImage = loginImage
        loginButton = gtk.Button(_('Login'))
        loginButton.connect('clicked', self.login, uentry, pentry)
        
        self.control.playerThread.scrobbler.thread.join()
        if self.control.playerThread.scrobbler.connected:
            loginImage.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_SMALL_TOOLBAR)
            loginLabel = gtk.Label(_('Logged in'))
        else:
            loginImage.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_SMALL_TOOLBAR)
            loginLabel = gtk.Label(_('Logged off'))
        loginLabel.set_alignment(0.1,0.5)
        self.loginLabel = loginLabel
        
        loginbox.pack_start(loginImage, False)
        loginbox.pack_start(loginLabel)
        loginbox.pack_start(loginButton, False)
        loginbox.set_border_width(10)
        uhbox.pack_start(ulabel)
        uhbox.pack_start(uentry, False)
        uhbox.pack_start(gtk.Label('  '), False)
        phbox.pack_start(plabel)
        phbox.pack_start(pentry, False)
        phbox.pack_start(gtk.Label('  '), False)
        svbox.pack_start(scrobblerLabel, False)
        svbox.pack_start(uhbox, False)
        svbox.pack_start(phbox, False)
        svbox.pack_start(loginbox, False)
        svbox.pack_start(cbhbox, False)
        svbox.pack_start(gtk.LinkButton('http://www.last.fm/home', 'last.fm website'), False)
        
        if not pylastInstalled:
            svbox.set_sensitive(False)
            svbox.pack_start(gtk.Label(_('*** Pylast module is not installed ***')), False)
        
        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)
        notebook.append_page(vbox, gtk.Label('General'))
        notebook.append_page(lvbox, gtk.Label('Library'))
        notebook.append_page(svbox, gtk.Label('Scrobbler'))
        
        dialogBox.pack_start(notebook)
        
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)   
        self.show_all()
        
        response = self.run()
        if response == gtk.RESPONSE_CLOSE or response == gtk.RESPONSE_DELETE_EVENT:
            settings['audiosink'] = gstSinks[audioCombo.get_active()]
            settings['statusicon'] = statusCombo.get_active()
            for c in columns:
                if c != '' and c != _('Name') and c != _('Add'):
                    settings[c] = labels[c].get_active()
            settings['lastplaylist'] = playcb.get_active()
            settings['foldercache'] = cachecb.get_active()
            settings['scrobbler'] = scrobblercb.get_active()
            settings['libraryMode'] = librarycb.get_active()
            settings['libraryFolder'] = browseButton.get_current_folder()
            self.storeLoginData(settings, settings, uentry, pentry)
            self.control.writeSettings(settings)
            self.control.refreshColumnsVisibility()
            self.control.refreshStatusIcon()
            if settings['libraryMode']:
                if self.control.folder != settings['libraryFolder']:
                    self.hide()
                    gtkTrick
                    self.control.loadLibrary()
            self.destroy()        
    
    def storeLoginData(self, settings, newsettings, uentry, pentry):
        """Stores the login data in the newsettings dictionary"""
        if self.pwdChanged and self.userChanged:
            newsettings['user'] = uentry.get_text()
            newsettings['pwdHash'] = md5(pentry.get_text())
            newsettings['fakepwd'] = '*' * len(pentry.get_text())
        elif self.userChanged:
            newsettings['user'] = uentry.get_text()
            newsettings['pwdHash'] = settings['pwdHash']
            newsettings['fakepwd'] = settings['fakepwd']
        elif self.pwdChanged:
            newsettings['user'] = settings['user']
            newsettings['pwdHash'] = md5(pentry.get_text())
            newsettings['fakepwd'] = '*' * len(pentry.get_text())
        else:
            newsettings['user'] = settings['user']
            newsettings['pwdHash'] = settings['pwdHash']
            newsettings['fakepwd'] = settings['fakepwd']
                
    def login(self, button, userentry, pwdentry):
        """Connects to the last.fm server"""
        if self.pwdChanged or self.userChanged:
            u = userentry.get_text()
            ph = md5(pwdentry.get_text())
        else:
            s = self.control.settings
            u = s['user']
            ph = s['pwdHash']
        a = gtk.gdk.PixbufAnimation('images/progress.gif')
        self.loginImage.set_from_animation(a)
        while gtk.events_pending():
                gtk.main_iteration()
        self.control.playerThread.scrobbler = Scrobbler(u, ph)
        self.control.playerThread.scrobbler.thread.join()
        connected = self.control.playerThread.scrobbler.connected
        if connected:
            self.loginImage.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_SMALL_TOOLBAR)
            self.loginLabel.set_text(_('Logged in'))
        else:
            self.loginImage.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_SMALL_TOOLBAR)
            self.loginLabel.set_text(_('Invalid user or password!'))
            
    def setPwdChanged(self, entry):
        if not self.emptyentry:
            if not self.pwdChanged:
                entry.set_text('')
                entry.set_position(0)
        self.pwdChanged = True
        
    def setUserChanged(self, entry):
        self.userChanged = True
    
    def hideLoveIcon(self, togglebutton):
        if togglebutton.get_active():
            self.control.view.scrobblerButton.show()
        else:
            self.control.view.scrobblerButton.hide()