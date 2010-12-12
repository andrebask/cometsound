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
from Queue import Queue
from threading import Thread

audioTypes = ['.mp3', '.wma', '.ogg', '.flac', 
            '.m4a', '.mp4', '.aac', '.wav',
             '.ape', '.mpc', '.wv']

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
                if type(self.directory).__name__ == 'list':
                    self.audioFileList = []
                    raise Exception
            except:
                self.directory = ''
                #print sys.exc_info()    
            return
        else:
            try:
                self.numOfFiles = int(commands.getstatusoutput("find \"%s\" | wc -l" % (directory))[1])
                self.fraction = float(1) / self.numOfFiles
            except:
                self.directory = ''    
        self.audioFileList = self.__startSearchFiles(self.directory) 
            
    def __startSearchFiles(self, directory):
        """Starts the threads to scan the file system"""
        #print directory
        list = [self.directory]
        try:
            fileList = os.listdir(directory)
        except:
            return list
        queue = Queue()
        dirList = []
        for fileName in fileList:
            if os.access((os.path.join(directory, fileName)), os.R_OK) and fileName[0] != '.':
                try:
                    filestat = os.stat(os.path.join(directory, fileName))
                except:
                    print "error reading " + directory + '/' + fileName
                    continue
                #print 'processing ' + fileName
                if self.isAudio(fileName):
                    list.append(AudioFile(directory, fileName))   
                elif stat.S_ISDIR(filestat.st_mode):
                    #print filestat.st_mtime
                    dirList.append(fileName)
                    t = Thread(target = self.__searchFiles, args = (os.path.join(directory, fileName), queue))
                    t.start()
            self.count += int(commands.getstatusoutput("find \"%s\" | wc -l" % (os.path.join(directory, fileName)))[1])
            self.__updateProgressBar()
            
        for fileName in dirList:
            l = queue.get()
            if len(l) != 0:
                l.insert(0, fileName)
                list.append(l)
                
        return list    

    def __searchFiles(self, directory, queue = None):
        """Recursively scans the file system to find audio files and add them to the tree"""
        #print directory
        list = [self.directory]
        try:
            fileList = os.listdir(directory)
        except:
            return list
        for fileName in fileList:
            if os.access((os.path.join(directory, fileName)), os.R_OK) and fileName[0] != '.':
                try:
                    filestat = os.stat(os.path.join(directory, fileName))
                except:
                    print "error reading " + directory + '/' + fileName
                    continue
                #print 'processing ' + fileName
                if self.isAudio(fileName):
                    list.append(AudioFile(directory, fileName))   
                elif stat.S_ISDIR(filestat.st_mode):
                    #print filestat.st_mtime
                    l = self.__searchFiles(os.path.join(directory, fileName))
                    if len(l) != 0:
                        l.insert(0, fileName)
                        list.append(l)
        if queue == None:
            return list
        else:
            queue.put(list)
    
    def __updateProgressBar(self):
        """Updates the progress bar that shows the current status of the scan"""
        if self.progressBar != None:
            self.progressBar.set_fraction(self.count * self.fraction)
            #self.progressBar.set_text(str(self.count * self.fraction)[2:4] + "%")
            while gtk.events_pending():
                gtk.main_iteration() 
    
    def updateModel(self):
        self.__updateModel(self.getAudioFileList(), self.directory)
        self.lastUpdate = time.time()
        
    def __updateModel(self, fileTree, dir):
        if not os.path.exists(dir):
            return
        fileList = os.listdir(dir)
        toDelete = []
        for element in fileTree:
            if type(element).__name__ == 'list':
                if element[0] in fileList:
                    fileList.remove(element[0])
                    self.__updateModel(element, os.path.join(dir, element[0]))
                else:
                    print 'deleting dir %s ' % element
                    toDelete.append(element)
            elif type(element).__name__ == 'instance':
                fname = element.getTagValue('fileName')
                if fname in fileList:
                    fileList.remove(fname)
                    path = os.path.join(dir, fname)
                    if os.path.getmtime(path) > self.lastUpdate:
                        print 'updating file %s ' % element.getTagValue('fileName')
                        fileTree[fileTree.index(element)] = AudioFile(dir, fname)
                else:
                    print 'deleting file %s ' % element.getTagValue('fileName')
                    toDelete.append(element)
        for old in toDelete:
            fileTree.remove(old)
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
        return ext in audioTypes                 