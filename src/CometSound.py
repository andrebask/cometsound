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

import AF, cerealizer, gtk, fcntl, sys, os
import mutagen.asf as mtgasf
cacheDir = os.path.join(os.environ.get('HOME', None), ".CometSound")  
from Model import Model
from View import View
from Controller import Controller
    
def registerClasses():
    cerealizer.register(AF.AudioFile)            

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

def getArg():
    if len(sys.argv) > 1 and sys.argv[1] != '':
        dir = sys.argv[1]
        if dir[0] != '/':
            dir = os.path.join(os.environ.get('HOME', None), dir)
    else:
        dir = ''
    return dir
        
def main():
    gtk.main()
    return 0
if __name__ == "__main__":
    registerClasses()
    m = Model(getArg())
    c = Controller(m)
    View(m, c)
    main()       
