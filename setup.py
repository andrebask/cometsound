from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.dep_util import newer
from distutils.dep_util import DistutilsFileError
from distutils.log import info
from glob import glob
import os
import sys
import string

class InstallData(install_data):
    def run (self):
        self.data_files.extend (self._compile_po_files ())
        install_data.run (self)

    def _compile_po_files (self):

        data_files = []
        PO_DIR = 'po'
	for language in glob('%s/*.po' % PO_DIR):
		lang = language
		lang = lang.split('/')[-1]
		lang = lang.split('.')[0]
		tmp = lang.split('_')
		try:
		    if tmp[0] == string.lower(tmp[1]):
		        lang = tmp[0]
		except:
		    lang = tmp[0]

		if lang:            
		    po = os.path.join(PO_DIR, '%s.po' % lang)
		    mo = os.path.join('build', 'mo', lang, 'LC_MESSAGES','cometsound.mo')

		    directory = os.path.dirname(mo)
		    if not os.path.exists(directory):
		        info('creating %s' % directory)
		        os.makedirs(directory)

		    try:
		        new = newer(po, mo)
		    except DistutilsFileError:
			newpo = po.split('/')[-1:][0]
			newpo = newpo.split('_')[0]
		        po = os.path.join(PO_DIR,'%s.po' % newpo) 
		        lang = newpo
		        new = newer(po, mo)
		    except:
			po = os.path.join(PO_DIR,'en.po') 
		        lang = 'en'
		        new = newer(po, mo)

		    if new:
		        # True if mo doesn't exist
		        cmd = 'msgfmt -o %s %s' % (mo, po)
		        info('compiling %s -> %s' % (po, mo))
		        if os.system(cmd) != 0:
		            raise SystemExit('Error while running msgfmt')
		    dest = os.path.dirname(os.path.join('share', 'locale-langpack', lang, 'LC_MESSAGES', 'cometsound.mo'))
		    data_files.append((dest, [mo]))
        return data_files

files = ['data/*']

setup(name="cometsound",
	version="0.4",
	description="Music player for GNU/Linux written in python, using pygtk and gstreamer libraries.",
	author="Andrea Bernardini",
	author_email="andrebask@gmail.com",
	url="https://launchpad.net/cometsound",
	packages=[''],
	package_dir={'' : 'src'},
	package_data={'': files},
	license='GPL v2', 	
	data_files=[
	('bin/', ['cometsound']),
		('share/applications', ['data/cometsound.desktop']),
		('share/cometsound/images', ['data/icon.png','data/note.svg','data/progress.gif','data/love.png']),
		('share/doc/cometsound', ['doc/copyright', 'doc/COPYING']),
		('share/cometsound', glob('src/*.py'))
	],
	long_description="""Music player for GNU/Linux written in python, using pygtk and gstreamer libraries.""",
	cmdclass={'install_data': InstallData}	
) 

