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

from mutagen.easyid3 import EasyID3
from mutagen.asf import ASF
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.oggflac import OggFLAC
from mutagen.oggspeex import OggSpeex
from mutagen.ogg import error as OggError

import string, os


fname = "fileName"	
keyList = ["title", "artist", "album", "genre", "year", "num"]
formatDict = dict()
formatDict['mp3'] = ["title", "artist", "album", "genre", "date", "tracknumber"]
formatDict['ogg'] = ["title", "artist", "album", "genre", "year", "tracknumber"]
formatDict['wma'] = ["Title", "Author", "WM/AlbumTitle", "WM/Genre", "WM/Year", "WM/TrackNumber"]
formatDict['flac'] = ["title", "artist", "album", "genre", "date", "tracknumber"]

class AudioFile:
	"""Data structure that represents an audio file,
	   it reads and stores tags from the file"""

	def __init__(self, directory, fileName):
		"""Builds the audio file structure from the file system path"""
		self.tagsDict = dict()
		self.tagsDict[fname] = fileName
		self.keyDict = dict()
		self.directoryName = directory + '/'
		self.cfname = os.path.join(directory, fileName)
		self.__readAudioFile(self.cfname)	
			
	def __readAudioFile(self, fileName):
		"""Detects the file extension, reads and stores tags""" 
		try:
			tags, fileext = self.read(fileName)
		except:
			for key in keyList:
				self.tagsDict[key] = ''
			#print sys.exc_info()	
		else:
			list = [(key, keyTag) for key in keyList for keyTag in formatDict[string.lower(fileext)]
					 if keyList.index(key) == formatDict[string.lower(fileext)].index(keyTag)]
			for couple in list:
				try:
					self.tagsDict[couple[0]] = str(tags[couple[1]][0])
				except:
					self.tagsDict[couple[0]] = ''
				self.keyDict[couple[0]] = couple[1]
	
	def read(self, fileName):		
		fileext = fileName.split('.')[-1:][0]
		if(fileext == ('mp3' or 'MP3')):
			tags = EasyID3(fileName)
			
		elif(fileext == ('wma' or 'WMA')):
			tags = ASF(fileName)
			
		elif(fileext == ('ogg' or 'OGG')):
			try:
				tags = OggVorbis(fileName)
			except OggError:	
				tags = OggFLAC(fileName)
			except:
				tags = OggSpeex(fileName)
					
		elif(fileext == ('flac' or 'FLAC')):
			tags = FLAC(fileName)
		return tags, fileext
				
	def getTagValues(self):
		"""Returns a list with the tag values:
		   file name, title, artist, album, genre, year, track number"""
		return [
                self.getTagValue(fname),
                self.getTagValue(keyList[5]),
                self.getTagValue(keyList[0]),
                self.getTagValue(keyList[1]),
                self.getTagValue(keyList[2]),
                self.getTagValue(keyList[3]),
                self.getTagValue(keyList[4]),
                ]
		
	
	def getTagValue(self, key):
		"""Returns the specific tag associated with the given key""" 
		return self.tagsDict[key]
	
	def writeTagValue(self, key, value):
		tags, fileext = self.read(self.cfname)
		key = self.keyDict[key]
		tags[key] = unicode(value)
		tags.pprint()
		tags.save()

	def getDir(self):
		"""Returns the name of this file's directory"""
		return self.directoryName		