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

from Common import gtk
from Common import registerClasses
from Common import getArg
from Common import singleInstaceCheck
from Common import setproctitle as spt

from Model import Model
from View import View
from Controller import Controller
from DbusService import DbusService

#Gives a Name to the main process
spt.setproctitle('CometSound')
        
def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    singleInstaceCheck()
    registerClasses()
    m = Model(getArg())
    c = Controller(m)
    View(m, c)
    DbusService(c)
    main() 
