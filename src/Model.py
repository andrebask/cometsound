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

import gtk, stat, os, string, commands, cerealizer, time
from AF import AudioFile

class Model:
    """Data structure that represents the file system tree"""
    audioFileList = list()
    count = 0
        
    def __init__(self, directory, progressBar = None):
        self.progressBar = progressBar
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
                fname = os.path.join(os.environ.get('HOME', None) , '.CometSound' , 'cache') 
                FILE = open(fname, 'rb')
                self.audioFileList = cerealizer.load(FILE)
                FILE.close()
                self.directory = self.getOldDir()
                self.lastUpdate = os.path.getmtime(fname)
            except:
                self.directory = ''    
            return
        else:
            try:
                self.numOfFiles = int(commands.getstatusoutput("find \"%s\" | wc -l" % (directory))[1])
                self.fraction = float(1) / self.numOfFiles
            except:
                self.directory = ''    
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
                i = fileName.rfind('.')
                ext = string.lower(fileName[i:])
                if ext in ['.mp3', '.wma', '.ogg', '.flac']:
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
        fileTree = self.getAudioFileList()
        self.curDir = ''    
        self.__searchChanged(fileTree, self.directory[1:])
        self.lastUpdate = time.time()

    def __searchChanged(self, fileTree, dir = ''):
        self.curDir += '/' + dir
        loopDir = self.curDir
        for file in fileTree:
            if type(file).__name__ == 'list':
                dir = file[0]
                if os.path.getmtime(self.curDir + '/' + dir) > self.lastUpdate:
                    print 'updating ' + dir 
                    fileTree[fileTree.index(file)] = [dir] + self.__searchFiles(self.curDir + '/' + dir)
                if self.__changed(self.curDir + '/' + dir):#TODO
                    self.__searchChanged(file, dir)
            elif type(file).__name__ == 'instance': 
                if os.path.getmtime(self.curDir + '/' + dir) > self.lastUpdate:
                    fileTree.remove(file)
            self.curDir = loopDir
        for file in os.listdir(self.curDir):
            #TODO           
    
#    def __searchChanged(self, fileTree, path, cfname, dir = ''):
#        self.curDir += '/' + dir
#        loopDir = self.curDir
#        for file in fileTree:
#            if type(file).__name__ == 'list':
#                if cfname == None:
#                    dir = file[0]
#                    if os.path.getmtime(self.curDir + '/' + dir) > self.lastUpdate:
#                        print 'updating ' + dir 
#                        for f in file:
#                            if type(file).__name__ == 'instance':
#                                fileName = f.getTagValue('fileName')
#                                file[file.index(f)] = AudioFile(dir, fileName)
#                    self.__searchChanged(file, path, cfname, dir)
#                elif file[0] == path[0]:
#                    path.remove(path[0])
#                    self.__searchChanged(file, path, cfname)
#            elif type(file).__name__ == 'instance' and len(path) == 1: 
#                if cfname == None and type(fileTree[0]).__name__ != 'str':                     
#                    fileName = file.getTagValue('fileName')
#                    dir = file.getDir()
#                    if os.path.getmtime(dir + '/' + fileName) > self.lastUpdate:
#                        print 'updating ' + fileName
#                        fileTree[fileTree.index(file)] = AudioFile(dir, fileName)
#                elif file.getTagValue('fileName') == path[0]:
#                    print 'updating ' + cfname
#                    dir, fileName = os.path.split(cfname)
#                    fileTree[fileTree.index(file)] = AudioFile(dir, fileName)
#            self.curDir = loopDir                   