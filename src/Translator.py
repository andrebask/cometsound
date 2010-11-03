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

import os, locale, gettext, sys

APP_NAME = "cometsound"

class Translator:
    
    def __init__(self):
        #language files path
        localPath = os.path.realpath(os.path.dirname(sys.argv[0]))
        langPath = localPath.split('cometsound')[0]
        langPath = os.path.join(langPath, 'locale-langpack')   
        langs = []
        #Check the default locale
        lc, encoding = locale.getdefaultlocale()
        if (lc):
            #If we have a default, it's the first in the list
            langs = [lc]
        # Get supported languages on the system
        language = os.environ.get('LANG', None)
        if (language):
            langs += language.split(":")
        langs += ["en", "en_US", "en_GB", "it"] #default
        
        gettext.bindtextdomain(APP_NAME, langPath)
        gettext.textdomain(APP_NAME)
        # Get the language to use
        lang = gettext.translation(APP_NAME, langPath
            , languages=langs, fallback = True)
        self._ = lang.gettext
        
    def getTranslationFunc(self):
        return self._