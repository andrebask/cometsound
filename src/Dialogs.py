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

import gtk, CometSound

_ = CometSound.t.getTranslationFunc()

class AboutDialog(gtk.AboutDialog):
    
    def __init__(self, icon, version):  
        gtk.AboutDialog.__init__(self)
        self.set_name('CometSound')    
        self.set_version(version)
        self.set_copyright(u'Copyright \u00A9 2010 Andrea Bernardini')
        self.set_website('https://launchpad.net/cometsound')
        pix = icon.get_pixbuf().scale_simple(60, 60, gtk.gdk.INTERP_BILINEAR)
        self.set_logo(pix)
        response = self.run()
        if response == -6 or response == -4:
            self.hide()
            
class SavePlaylistDialog(gtk.Dialog):
    
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_title(_('Save Playlist'))
        self.set_size_request(200, 100)
        l = gtk.Label(_('Insert playlist name:'))
        e = gtk.Entry()
        vbox = self.get_child()
        vbox.pack_start(l)
        vbox.pack_start(e)
        self.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        self.show_all()
        response = self.run()
        if response == gtk.RESPONSE_OK:
            self.savePlaylist(e.get_text())
            self.destroy()
                
class PreferencesDialog(gtk.Dialog):
    
    def __init__(self, columns, control):
        gtk.Dialog.__init__(self)
        self.set_size_request(300,320)
        self.control = control
        self.control.readSettings()
        settings = self.control.settings
        if settings == None:
            settings = {'audiosink': 'autoaudiosink',
                    'statusicon': 0,    
                    '#': True,
                     _('Title'): True,
                     _('Artist'): True,
                      _('Album'): True,
                       _('Genre'): True,
                        _('Year'): True,
                         _('Add'): True
                         } 
            
        self.set_title(_('CometSound preferences'))
        sinks = ['Auto', 'ALSA', 'PulseAudio', 'OSS', 'Jack']
        gstSinks = ['autoaudiosink', 'alsasink', 'pulsesink', 'osssink', 'jackaudiosink']
        vbox = self.get_child()
        audioLabel = gtk.Label()
        audioLabel.set_alignment(0,0)
        audioLabel.set_padding(0,6)
        audioLabel.set_markup(_('<b>Audio output (Restart required)</b>'))
        audioCombo = gtk.combo_box_new_text()
        for s in sinks:
            audioCombo.append_text(s)
        audioCombo.set_active(gstSinks.index(settings['audiosink']))
        
        columnsLabel = gtk.Label()
        columnsLabel.set_alignment(0,0)
        columnsLabel.set_padding(0,6)
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
        for c in columns:
            if c != '' and c != _('Name'):
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
        statusLabel.set_padding(0,6)
        statusLabel.set_markup(_('<b>Status Icon</b>'))
        statusCombo = gtk.combo_box_new_text()
        statusCombo.append_text(_('Enable status icon with track\'s informations'))
        statusCombo.append_text(_('Enable status icon'))
        statusCombo.append_text(_('Disable status icon'))
        statusCombo.set_active(settings['statusicon'])
                
        vbox.pack_start(audioLabel)
        vbox.pack_start(audioCombo)
        vbox.pack_start(columnsLabel)
        vbox.pack_start(hbox) 
        vbox.pack_start(statusLabel)
        vbox.pack_start(statusCombo)
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)   
        self.show_all()
        response = self.run()
        if response == -7 or response == -4:
            newsettings = {'audiosink': gstSinks[audioCombo.get_active()]}
            newsettings['statusicon'] = statusCombo.get_active()
            for c in columns:
                if c != '' and c != _('Name'):
                    newsettings[c] = labels[c].get_active()
            self.control.writeSettings(newsettings)
            self.control.refreshColumnsVisibility()
            self.control.refreshStatusIcon()
            self.destroy()        