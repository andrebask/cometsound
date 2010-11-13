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

import gtk, stat, os, string, commands, cerealizer, time, sys
from AF import AudioFile

class Model:
    """Data structure that represents the file system tree"""
    audioFileList = list()
    count = 0
        
    def __init__(self, directory, progressBar = None):
        self.progressBar = progressBar
        self.cachefname = os.path.join(os.environ.get('HOME', None) , '.CometSound' , 'cache')
        try:
            self.lastUpdate = os.path.getmtime(self.cachefname)
        except:
            self.lastUpdate = 0    
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
                FILE = open(self.cachefname, 'rb')
                self.audioFileList = cerealizer.load(FILE)
                FILE.close()
                self.directory = self.audioFileList[0]
            except:
                self.directory = ''
                print sys.exc_info()    
            return
        else:
            try:
                self.numOfFiles = int(commands.getstatusoutput("find \"%s\" | wc -l" % (directory))[1])
                self.fraction = float(1) / self.numOfFiles
            except:
                self.directory = ''    
        self.audioFileList = self.__searchFiles(self.directory) 
            
    def __searchFiles(self, directory):
        """Recursively scans the file system to find audio files and add them to the tree"""
        list = [self.directory]
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
                if self.isAudio(fileName):
                    list.append(AudioFile(directory, fileName))   
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
            self.progressBar.set_fraction(self.count * self.fraction)
            #self.progressBar.set_text(str(self.count * self.fraction)[2:4] + "%")
            self.count+=1
            while gtk.events_pending():
                gtk.main_iteration() 
    
    def updateModel(self):
        self.__updateModel(self.getAudioFileList(), self.directory)
        self.lastUpdate = time.time()
        
    def __updateModel(self, fileTree, dir):
        fileList = os.listdir(dir)
        for element in fileTree:
            if type(element).__name__ == 'list':
                if element[0] in fileList:
                    fileList.remove(element[0])
                    self.__updateModel(element, os.path.join(dir, element[0]))
                else:
                    fileTree.remove(element)
            elif type(element).__name__ == 'instance':
                fname = element.getTagValue('fileName')
                if fname in fileList:
                    fileList.remove(fname)
                    path = os.path.join(dir, fname)
                    if os.path.getmtime(path) > self.lastUpdate:
                        print 'updating file %s ' % file.getTagValue('fileName')
                        fileTree[fileTree.index(element)] = AudioFile(dir, fname)
                else:
                    fileTree.remove(element)
        for element in fileList:
            path = os.path.join(dir, element)
            if stat.S_ISDIR(os.stat(path).st_mode):
                print 'adding new dir ' + element
                newdir = self.__searchFiles(path)
                fileTree.append([element] + newdir[1:])
            elif stat.S_ISREG(os.stat(path).st_mode) and self.isAudio(element):
                print 'adding new file ' + element
                fileTree.append(AudioFile(dir, element))
     
    def isAudio(self, fileName):
        i = fileName.rfind('.')
        ext = string.lower(fileName[i:])
        return ext in ['.mp3', '.wma', '.ogg', '.flac', 
                       '.m4a', '.mp4', '.aac', '.wav', '.ape', '.mpc', '.wv']                 