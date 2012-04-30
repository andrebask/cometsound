##
#    Project: CometSound - A music player written in Python 
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010-2012 Andrea Bernardini
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

from Common import stat
from Common import os
from Common import cerealizer
from Common import time
from Common import gtkTrick
from Common import isAudio
from Common import readSettings
from Common import threading
from Common import Global

from AF import AudioFile
import gobject

class Model:
    """Data structure that represents the file system tree"""
    audioFileList = list()
    count = 0
        
    def __init__(self, directoryList, progressBar = None, group = False):
        self.progressBar = progressBar
        self.numOfFiles = 0
        self.changed = False
        self.MTlist = []
        settings = readSettings()
        self.cachefname = os.path.join(os.environ.get('HOME', None) , '.CometSound' , 'cache')
        if settings != None and settings['libraryMode']:
                self.cachefname = os.path.join(os.environ.get('HOME', None) , '.CometSound' , 'library')
        try:
            self.lastUpdate = os.path.getmtime(self.cachefname)
        except:
            self.lastUpdate = 0    
        self.setDir(directoryList, group)
     
    def getAudioFileList(self):
        return self.audioFileList   
                
    def getDir(self):
        return self.directory
    
    def setDir(self, directoryList, group = False):
        """Sets the directory to scan, calculates the number of files,
           and builds the file system tree (using __searchFiles method)"""
        self.directory = directoryList[0]  
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
            self.playlist = None  
            return
        else:
            try:
                self.numOfFiles = sum((len(f) for _, _, f in os.walk(self.directory)))
                self.fraction = float(1) / self.numOfFiles
                if group:
                    for dir in directoryList:
                        self.numOfFiles += sum((len(f) for _, _, f in os.walk(self.directory)))
                    self.fraction = float(1) / self.numOfFiles
            except:
                self.directory = ''
        threading.Thread(target=self.__updateProgressBarThreaded).start()
        if not group:
            self.playlist = []
            for file in directoryList:
                if isAudio(file):
                    tv = AudioFile(file).getTagValues()
                    cfname, title, album, arist = tv[0], tv[2], tv[4], tv[3]
                    self.playlist.append((cfname, title, album, arist))
            if isAudio(directoryList[0]):
                index = self.directory.rfind("/")    
                if self.numOfFiles < 200:
                    self.directory = self.directory[:index]
                else:
                    self.directory = ''
            gobject.idle_add(self.__searchFilesMThreaded, self.directory)
            self.__waitSearch()
            self.audioFileList = self.MTlist
        else:
            groupdir = directoryList[0][:directoryList[0].rfind("/")]
            self.audioFileList = [groupdir, 'Group']
            for folder in directoryList:
                dirname = folder[folder.rfind("/") + 1:]
                gobject.idle_add(self.__searchFilesMThreaded, self.directory)   
                self.__waitSearch()            
                self.audioFileList.append([dirname] + self.MTlist)
                
    def __searchFiles(self, directory):
        """Recursively scans the file system to find audio files and add them to the tree"""
        #print directory
        list = [self.directory]
        try:
            fileList = os.listdir(directory)
        except:
            print "error reading " + directory + '/'
            return list
        for fileName in fileList:
            if os.access((os.path.join(directory, fileName)), os.R_OK) and fileName[0] != '.':
                try:
                    filestat = os.stat(os.path.join(directory, fileName))
                except:
                    print "error reading " + directory + '/' + fileName
                    Global.PBcount += 1
                    continue
                #print 'processing ' + fileName
                if isAudio(fileName):
                    list.append(AudioFile(directory, fileName).getAudioFileInfos())   
                elif stat.S_ISDIR(filestat.st_mode):
                    #print filestat.st_mtime
                    l = self.__searchFiles(os.path.join(directory, fileName))
                    if len(l) != 0:
                        l.insert(0, fileName)
                        list.append(l)
            Global.PBcount += 1
            gtkTrick()

        return list  

    def __waitSearch(self):
        while Global.PBcount == 0:
            gtkTrick()
        old = 0
        while Global.PBcount < self.numOfFiles:
            time.sleep(.01)  
            if old ==  Global.PBcount:
                break
            else:
                old = Global.PBcount
             
    
    def __searchFilesMThreaded(self, directory):
        """Recursively scans the file system to find audio files and add them to the tree"""
        #print directory
        threadsNum = 4
        self.MTlist = [self.directory]
        try:
            fileList = os.listdir(directory)
        except:
            return list
        
        slot = len(fileList)/threadsNum        
        for i in range(1,threadsNum):
            flist = fileList[ (i-1) * slot : i * slot ]
            if len(flist) > 0:
                gobject.idle_add(self.__searchFilesList, directory, flist)
        flist = fileList[ slot * (threadsNum-1) : ]
        if len(flist) > 0:
            gobject.idle_add(self.__searchFilesList, directory, flist)
        
    def __searchFilesList(self, directory, fileList):
        """Recursively scans the file system to find audio files and add them to the tree"""
        #print directory
        for fileName in fileList:
            if os.access((os.path.join(directory, fileName)), os.R_OK) and fileName[0] != '.':
                try:
                    filestat = os.stat(os.path.join(directory, fileName))
                except:
                    print "error reading " + directory + '/' + fileName
                    Global.PBcount += 1
                    continue
                #print 'processing ' + fileName
                if isAudio(fileName):
                    self.MTlist.append(AudioFile(directory, fileName).getAudioFileInfos())   
                elif stat.S_ISDIR(filestat.st_mode):
                    #print filestat.st_mtime
                    l = self.__searchFiles(os.path.join(directory, fileName))
                    if len(l) != 0:
                        l.insert(0, fileName)
                        self.MTlist.append(l)
            Global.PBcount += 1
            gtkTrick()
            
    def __updateProgressBar(self, par1 = None, par2 = None):
        """Updates the progress bar that shows the current status of the scan"""
        if self.progressBar != None:
            self.progressBar.set_fraction(self.__truncate(Global.PBcount * self.fraction))
            #self.progressBar.set_text(str(self.count * self.fraction)[2:4] + "%")
            
    def __updateProgressBarThreaded(self):
        """Updates the progress bar that shows the current status of the scan"""
        while self.__truncate(Global.PBcount * self.fraction) != 1.0:
            #time.sleep(0.1)
            if self.progressBar != None:
                #print self.__truncate(Global.PBcount * self.fraction)
                gobject.idle_add(self.__updateProgressBar)
                time.sleep(.01)
                
    def __truncate(self, int):
        if int < 1: return int
        else: return 1.0
        
    def updateModel(self):
        """Searches in the file system recently changed or added files to update the model"""
        self.changed = False
        self.__updateModel(self.getAudioFileList(), self.directory)
        self.lastUpdate = time.time()
        
    def __updateModel(self, fileTree, dir):
        gtkTrick()
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
                    self.changed = True
            elif type(element).__name__ == 'instance':
                fname = element.getTagValues()[0]
                if fname in fileList:
                    fileList.remove(fname)
                    path = os.path.join(dir, fname)
                    if os.path.getmtime(path) > self.lastUpdate:
                        print 'updating file %s ' % element.getTagValues()[0]
                        fileTree[fileTree.index(element)] = AudioFile(dir, fname).getAudioFileInfos()
                        self.changed = True
                else:
                    print 'deleting file %s ' % element.getTagValues()[0]
                    toDelete.append(element)
                    self.changed = True
        for old in toDelete:
            fileTree.remove(old)
        for element in fileList:
            path = os.path.join(dir, element)
            if stat.S_ISDIR(os.stat(path).st_mode):
                print 'adding new dir ' + element
                newdir = self.__searchFiles(path)
                fileTree.append([element] + newdir[1:])
                self.changed = True
            elif stat.S_ISREG(os.stat(path).st_mode) and isAudio(element):
                print 'adding new file ' + element
                fileTree.append(AudioFile(dir, element).getAudioFileInfos())
                self.changed = True
     
