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

import gtk, stat, AF, os, string, commands, cerealizer

class Model:
    """Data structure that represents the file system tree"""
    audioFileList = list()
    count = 0
        
    def __init__(self, directory, progressBar = None):
        self.progressBar = progressBar
        self.setDir(directory)
     
    def getAudioFileList(self):
        return self.audioFileList   
                
    def getDir(self):
        return self.directory
    
    def setDir(self, directory):
        """Sets the directory to scan, calculates the number of files,
           and builds the file system tree (using __searchFiles method)"""
        self.directory = directory   
        if self.directory == '':  
            try: 
                FILE = open(os.path.join(os.environ.get('HOME', None) , '.CometSound' , 'cache'), 'rb')
                self.audioFileList = cerealizer.load(FILE)
                FILE.close()
            except:
                self.directory = ''    
            return
        else:
            try:
                self.numOfFiles = int(commands.getstatusoutput("find \"%s\" | wc -l" % (directory))[1]) #find /home/andrebask/ -name "[[:alnum:]]*.mp3" | wc -l
            except:
                self.folder = ''    
        self.audioFileList = self.__searchFiles(self.directory) 
    
    def getOldDir(self):
        """Extracts the name of the current directory"""
        f = self.audioFileList[0]
        if type(f).__name__ == 'instance':
            dirname = f.getDir()[:-1]
        elif type(f).__name__ == 'list':
            subdir = f[1].getDir()
            i = subdir[:-1].rfind('/')
            dirname = subdir[:i]
        return dirname
            
    def __searchFiles(self, directory):
        """Recursively scans the file system to find audio files and add them to the tree"""
        list = []
        try:
            fileList = os.listdir(directory)
        except:
            return list
        for fileName in fileList:
            self.__updateProgressBar()
            if os.access((directory + '/' + fileName), os.R_OK) and fileName[0] != '.':
                try:
                    filestat = os.stat(directory + '/' + fileName)
                except:
                    print "error reading " + directory + '/' + fileName
                    continue
                if string.lower(fileName[-4:]) == '.mp3':
                    list.append(AF.AudioFile(directory, fileName))
                elif string.lower(fileName[-4:]) == '.wma':
                    list.append(AF.AudioFile(directory, fileName))
                elif string.lower(fileName[-4:]) == '.ogg':
                    list.append(AF.AudioFile(directory, fileName))
                elif stat.S_ISDIR(filestat.st_mode):
                    #print filestat.st_mtime
                    l = self.__searchFiles(directory + '/' + fileName)
                    if len(l) != 0:
                        l.insert(0, fileName)
                        list.append(l)
        return list    
    
    def __updateProgressBar(self):
        """Updates the progress bar that shows the current status of the scan"""
        if self.progressBar != None:
            fraction = float(self.count) / self.numOfFiles
            self.progressBar.set_fraction(fraction)
            #self.progressBar.set_text(str(fraction)[2:4] + "%")
            self.count+=1
            while gtk.events_pending():
                gtk.main_iteration() 