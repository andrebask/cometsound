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

import AF, cerealizer, gtk
import mutagen.asf as mtgasf
import Model
import Controller
import View
from Translator import Translator
    
def registerClasses():
    cerealizer.register(mtgasf.ASFUnicodeAttribute)
    cerealizer.register(mtgasf.ASFDWordAttribute)
    cerealizer.register(AF.AudioFile)            
          
t = Translator()

import fcntl, sys, os
dir = os.path.join(os.environ.get('HOME', None), '.CometSound')
pidFile = os.path.join(dir, 'program.pid') 
if not os.path.exists(dir):
    os.makedirs(dir)
fp = open(pidFile, 'w')
try:
    fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print 'CometSound is already running'
    sys.exit(0)

            
def main():
    gtk.main()
    return 0
if __name__ == "__main__":
    registerClasses()
    m = Model.Model('')
    c = Controller.Controller(m)
    View.View(m, c)
    main()       
