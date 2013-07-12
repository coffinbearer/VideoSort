#!/usr/bin/env python
#
# VideoSort post-processing script for NZBGet.
#
# Copyright (C) 2013 Andrey Prygunkov <hugbug@users.sourceforge.net>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with the program.  If not, see <http://www.gnu.org/licenses/>.
#


##############################################################################
### NZBGET POST-PROCESSING SCRIPT										   ###

# Sort movies and tv shows.
#
# This is a script for downloaded TV shows and movies. It uses scene-standard
# naming conventions to match TV shows and movies and rename/move/sort/organize
# them as you like.
#
# The script relies on python library "guessit" (http://guessit.readthedocs.org)
# to extract information from file names and includes portions of code from
# "SABnzbd+" (http://sabnzbd.org).
#
# Info about pp-script:
# Author: Andrey Prygunkov (nzbget@gmail.com).
# Web-site: http://nzbget.sourceforge.net/VideoSort.
# License: GPLv3 (http://www.gnu.org/licenses/gpl.html).
# PP-Script Version: 1.0.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS																   ###

# Destination directory for movies.
#MoviesDir=${DestDir}/movies

# Destination directory for seasoned TV shows.
#SeriesDir=${DestDir}/series

# Destination directory for dated TV shows.
#DatedDir=${DestDir}/tv

# File extensions for video files.
#
# Only files with these extensions are processed. Extensions must
# be separated with commas.
# Example=.mkv,.avi,.divx,.xvid,.mov,.wmv,.mp4,.mpg,.mpeg,.vob,.iso
#VideoExtensions=.mkv,.avi,.divx,.xvid,.mov,.wmv,.mp4,.mpg,.mpeg,.vob,.iso

# File extensions for satellite files.
#
# Move satellite files such as subtitles to the destination along with
# the files they are related to. Extensions must be separated with commas.
# Example=.srt,.nfo
#SatelliteExtensions=.srt,.sub

# Minimum video file size (Megabytes).
#
# Smaller files are ignored.
#MinSize=100

# Formatting rules for movies.
#
# Specifiers for movies:
# %t, %.t, %_t    - movie title with words separated with spaces, dots
#                   or underscores (case-adjusted);
# %tT, %t.T, %t_T - movie title (original letter case);
# %y			  - year;
# %decade         - two-digits decade (90, 00, 10);
# %0decade        - four-digits decade (1990, 2000, 2010).
#
# Common specifiers (for movies, series and dated tv shows):
# %dn             - original directory name (nzb-name);
# %fn             - original filename;
# %ext            - file extension;
# %Ext            - file extension (case-adjusted);
# %qf             - video format (HTDV, BluRay, WEB-DL);
# %qss            - screen size (720p, 1080i);
# %qvc            - video codec (x264);
# %qac            - audio codec (DTS);
# %qah            - audio channels (5.1);
# %qrg            - release group;
# {{text}}        - uppercase the text;
# {TEXT}          - lowercase the text;
#MoviesFormat=%t (%y)

# Formatting rules for seasoned TV shows.
#
# Specifiers:
# %sn, %s.n, %s_n - show name with words separated with spaces, dots
#                   or underscores (case-adjusted);
# %sN, %s.N, %s_N - show name (original letter case);
# %s              - season number (1, 2);
# %0s             - two-digits season number (01, 02);
# %e              - episode number (1, 2);
# %0e             - two-digits episode number (01, 02);
# %en, %e.n, %e_n - episode name (case-adjusted);
# %eN, %e.N, %e_N - episode name (original letter case);
#
# For a list of common specifiers see option <MoviesFormat>.
#SeriesFormat=%sn/Season %s/%sn - S%0sE%0e - %en

# Formatting rules for dated TV shows.
#
# Specifiers:
# %sn, %s.n, %s_n - show name with words separated with spaces, dots
#                   or underscores (case-adjusted);
# %sN, %s.N, %s_N - show name (original letter case);
# %y			  - year;
# %decade         - two-digits decade (90, 00, 10);
# %0decade        - four-digits decade (1990, 2000, 2010).
# %m			  - month (1-12);
# %0m			  - two-digits month (01-12);
# %d			  - day (1-31);
# %0d			  - two-digits day (01-31);
#
# For a list of common specifiers see option <MoviesFormat>.
#DatedFormat=%sn/%sn - %y-%0m-%0d

# List of words to keep in lower case.
#
# This option has effect on "case-adjusted"-specifiers.
#LowerWords=the,of,and,at,vs,a,an,but,nor,for,on,so,yet

# List of words to keep in upper case.
#
# This option has effect on "case-adjusted"-specifiers.
#UpperWords=III,II,IV

# Overwrite files at destination (yes, no).
#
# If not active the files are still moved into destination but
# unique suffixes are added at the end of file names, e.g. My.Show.(2).mkv.
#Overwrite=no

# Delete download directory after renaming (yes, no).
#
# If after successful sorting all remaining files in the download directory
# are smaller than "MinSize" the directory with all files is removed. If no
# files could be processed, the directory remains untouched.
#Cleanup=yes

# Preview mode (yes, no).
#
# When active no changes to file system are made but the destination
# file names are logged. Useful to test formating rules; to restart
# the script use "Post-Process-Again" on history tab in NZBGet web-interface.
#Preview=no

# Print more logging messages (yes, no).
#
# For debugging or if you need to report a bug.
#Verbose=no

### NZBGET POST-PROCESSING SCRIPT										   ###
##############################################################################

import sys
from os.path import dirname
sys.path.append(dirname(__file__) + '/lib')

import os
import string
import traceback
import re
import shutil
import guessit


# Exit codes used by NZBGet
POSTPROCESS_SUCCESS=93
POSTPROCESS_NONE=95
POSTPROCESS_ERROR=94

# Check if the script is called from nzbget 11.0 or later
if not 'NZBOP_SCRIPTDIR' in os.environ:
	print('*** NZBGet post-processing script ***')
	print('This script is supposed to be called from nzbget (11.0 or later).')
	sys.exit(POSTPROCESS_ERROR)

# Check if directory still exist (for post-process again)
if not os.path.exists(os.environ['NZBPP_DIRECTORY']):
	print('[INFO] Destination directory doesn\'t exist, exiting')
	sys.exit(POSTPROCESS_NONE)

# Check par and unpack status for errors
if os.environ['NZBPP_PARSTATUS'] == '1' or os.environ['NZBPP_PARSTATUS'] == '4' or os.environ['NZBPP_UNPACKSTATUS'] == '1':
	print('[WARNING] Download of "%s" has failed, exiting' % (os.environ['NZBPP_NZBNAME']))
	sys.exit(POSTPROCESS_NONE)

# Check if all required script config options are present in config file
required_options = ('NZBPO_MOVIESDIR', 'NZBPO_SERIESDIR', 'NZBPO_DATEDDIR', 'NZBPO_VIDEOEXTENSIONS',
	'NZBPO_SATELLITEEXTENSIONS', 'NZBPO_MINSIZE', 'NZBPO_MOVIESFORMAT', 'NZBPO_SERIESFORMAT',
	'NZBPO_DATEDFORMAT', 'NZBPO_OVERWRITE', 'NZBPO_CLEANUP', 'NZBPO_LOWERWORDS', 'NZBPO_UPPERWORDS',
	'NZBPO_PREVIEW', 'NZBPO_VERBOSE')
for optname in required_options:
	if (not optname in os.environ):
		print('[ERROR] Option %s is missing in configuration file. Please check script settings' % optname[6:])
		sys.exit(POSTPROCESS_ERROR)

# Init script config options
download_dir=os.environ['NZBPP_DIRECTORY']
series_format=os.environ['NZBPO_SERIESFORMAT']
dated_format=os.environ['NZBPO_DATEDFORMAT']
movies_format=os.environ['NZBPO_MOVIESFORMAT']
movies_dir=os.environ['NZBPO_MOVIESDIR']
series_dir=os.environ['NZBPO_SERIESDIR']
dated_dir=os.environ['NZBPO_DATEDDIR']
video_extensions=os.environ['NZBPO_VIDEOEXTENSIONS'].split(',')
satellite_extensions=os.environ['NZBPO_SATELLITEEXTENSIONS'].split(',')
min_size=int(os.environ['NZBPO_MINSIZE'])
min_size <<= 20
overwrite=os.environ['NZBPO_OVERWRITE'] == 'yes'
cleanup=os.environ['NZBPO_CLEANUP'] == 'yes'
preview=os.environ['NZBPO_PREVIEW'] == 'yes'
verbose=os.environ['NZBPO_VERBOSE'] == 'yes'
satellites=len(satellite_extensions)>0
lower_words=os.environ['NZBPO_LOWERWORDS'].replace(' ', '').split(',')
upper_words=os.environ['NZBPO_UPPERWORDS'].replace(' ', '').split(',')

if preview:
	print('[WARNING] *** PREVIEW MODE ON - NO CHANGES TO FILE SYSTEM ***')

# List of moved files (source path)
moved_src_files = []

# List of moved files (destination path)
moved_dst_files = []

# Separator character used between file name and opening brace
# for duplicate files such as "My Movie (2).mkv"
dupe_separator = ' '

def guess_dupe_separator(format):
	""" Find out a char most suitable as dupe_separator
	""" 
	global dupe_separator
	
	dupe_separator = ' '
	format_fname = os.path.basename(format)

	for x in ('%.t', '%s.n', '%s.N'):
		if (format_fname.find(x) > -1):
			dupe_separator = '.'
			return
			
	for x in ('%_t', '%s_n', '%s_N'):
		if (format_fname.find(x) > -1):
			dupe_separator = '_'
			return

def unique_name(new):
	""" Adds unique numeric suffix to destination file name to avoid overwriting
		such as "filename.(2).ext", "filename.(3).ext", etc.
		If existing file was created by the script it is renamed to "filename.(1).ext".
	"""
	fname, fext = os.path.splitext(new)
	suffix_num = 2
	while True:
		new_name = fname + dupe_separator + '(' + str(suffix_num) + ')' + fext
		if not os.path.exists(new_name) and new_name not in moved_dst_files:
			break
		suffix_num += 1
	return new_name

def rename(old, new):
	""" Moves the file to its sorted location.
		It creates any necessary directories to place the new file and moves it.
	"""
	if os.path.exists(new) or new in moved_dst_files:
		if overwrite and new not in moved_dst_files:
			os.remove(new)
			shutil.move(old, new)
			print('[INFO] Overwrote: %s' % new)
		else:
			# rename to filename.(2).ext, filename.(3).ext, etc.
			new = unique_name(new)
			rename(old, new)
	else:
		if not preview:
			if not os.path.exists(os.path.dirname(new)):
				os.makedirs(os.path.dirname(new))
			shutil.move(old, new)
		print('[INFO] Moved: %s' % new)
	moved_src_files.append(old)
	moved_dst_files.append(new)
	return new

def move_satellites(videofile, dest):
	""" Moves satellite files such as subtitles that are associated with base
		and stored in root to the correct dest.
	"""
	if verbose:
		print('Move satellites for %s' % videofile)
		
	root = os.path.dirname(videofile)
	destbasenm = os.path.splitext(dest)[0]
	base = os.path.basename(os.path.splitext(videofile)[0])
	for filename in os.listdir(root):
		fbase, fext = os.path.splitext(filename)
		if fext in satellite_extensions and fbase.lower() == base.lower():
			old = os.path.join(root, filename)
			new = destbasenm + fext
			if verbose:
				print('Satellite: %s' % os.path.basename(new))
			rename(old, new)

def cleanup_download_dir():
	""" Remove the download directory if it (or any subfodler) does not contain "important" files
		(important = size >= min_size)
	"""
	if verbose:
		print('Cleanup')

	# Check if there are any big files remaining
	for root, dirs, files in os.walk(download_dir):
		for filename in files:
			path = os.path.join(root, filename)
			# Check minimum file size			 
			if os.path.getsize(path) >= min_size and (not preview or path not in moved_src_files):
				print('[WARNING] Skipping clean up due to large files remaining in the directory')
				return

	# Now delete all files with nice logging				
	for root, dirs, files in os.walk(download_dir):
		for filename in files:
			path = os.path.join(root, filename)
			if not preview or path not in moved_src_files:
				if not preview:
					os.remove(path)
				print('[INFO] Deleted: %s' % path)
	if not preview:
		shutil.rmtree(download_dir)
	print('[INFO] Deleted: %s' % download_dir)

STRIP_AFTER = ('_', '.', '-')

# * From SABnzbd+ (with modifications) *

REPLACE_AFTER = {
	'()': '',
	'..': '.',
	'__': '_',
	'  ': ' ',
	'//': '/',
	' - - ': ' - ',
	'__': '_'
}

def path_subst(path, mapping):
	""" Replace the sort sting elements by real values.
		Non-elements are copied literally.
		path = the sort string
		mapping = array of tuples that maps all elements to their values
	"""
	newpath = []
	plen = len(path)
	n = 0
	while n < plen:
		result = path[n]
		if result == '%':
			for key, value in mapping:
				if path.startswith(key, n):
					n += len(key)-1
					result = value
					break
		newpath.append(result)
		n += 1
	return ''.join(newpath)

def get_titles(name, titleing=False):
	'''
	The title will be the part before the match
	Clean it up and title() it

	''.title() isn't very good under python so this contains
	a lot of little hacks to make it better and for more control
	'''

	title = name.replace('.', ' ').replace('_', ' ')
	title = title.strip().strip('(').strip('_').strip('-').strip().strip('_')

	if titleing:
		title = titler(title) # title the show name so it is in a consistant letter case

		#title applied uppercase to 's Python bug?
		title = title.replace("'S", "'s")

		# Make sure some words such as 'and' or 'of' stay lowercased.
		for x in lower_words:
			xtitled = titler(x)
			title = replace_word(title, xtitled, x)

		# Make sure some words such as 'III' or 'IV' stay uppercased.
		for x in upper_words:
			xtitled = titler(x)
			title = replace_word(title, xtitled, x)

		# Make sure the first letter of the title is always uppercase
		if title:
			title = titler(title[0]) + title[1:]

	# The title with spaces replaced by dots
	dots = title.replace(" - ", "-").replace(' ','.').replace('_','.')
	dots = dots.replace('(', '.').replace(')','.').replace('..','.').rstrip('.')

	# The title with spaces replaced by underscores
	underscores = title.replace(' ','_').replace('.','_').replace('__','_').rstrip('_')

	return title, dots, underscores

def titler(p):
	""" title() replacement
		Python's title() fails with Latin-1, so use Unicode detour.
	"""
	if isinstance(p, unicode):
		return p.title()
	elif gUTF:
		try:
			return p.decode('utf-8').title().encode('utf-8')
		except:
			return p.decode('latin-1', 'replace').title().encode('latin-1', 'replace')
	else:
		return p.decode('latin-1', 'replace').title().encode('latin-1', 'replace')

def replace_word(input, one, two):
	''' Regex replace on just words '''
	regex = re.compile(r'\W(%s)(\W|$)' % one, re.I)
	matches = regex.findall(input)
	if matches:
		for m in matches:
			input = input.replace(one, two)
	return input

def get_decades(year):
	""" Return 4 digit and 2 digit decades given 'year'
	"""
	if year:
		try:
			decade = year[2:3]+'0'
			decade2 = year[:3]+'0'
		except:
			decade = ''
			decade2 = ''
	else:
		decade = ''
		decade2 = ''
	return decade, decade2

_RE_LOWERCASE = re.compile(r'{([^{]*)}')
def to_lowercase(path):
	''' Lowercases any characters enclosed in {} '''
	while True:
		m = _RE_LOWERCASE.search(path)
		if not m:
			break
		path = path[:m.start()] + m.group(1).lower() + path[m.end():]

	# just incase
	path = path.replace('{', '')
	path = path.replace('}', '')
	return path

_RE_UPPERCASE = re.compile(r'{{([^{]*)}}')
def to_uppercase(path):
	''' Lowercases any characters enclosed in {{}} '''
	while True:
		m = _RE_UPPERCASE.search(path)
		if not m:
			break
		path = path[:m.start()] + m.group(1).upper() + path[m.end():]
	return path

def strip_folders(path):
	""" Return 'path' without leading and trailing strip-characters in each element
	"""
	f = path.strip('/').split('/')

	# For path beginning with a slash, insert empty element to prevent loss
	if path.strip()[0] in '/\\':
		f.insert(0, '')

	def strip_all(x):
		""" Strip all leading/trailing underscores and hyphens
			also dots for Windows
		"""
		old_name = ''
		while old_name != x:
			old_name = x
			for strip_char in STRIP_AFTER:
				x = x.strip().strip(strip_char)
		
		return x

	return os.path.normpath('/'.join([strip_all(x) for x in f]))

gUTF = False
try:
	if sys.platform == 'darwin':
		gUTF = True
	else:
		gUTF = locale.getdefaultlocale()[1].lower().find('utf') >= 0
except:
	# Incorrect locale implementation, assume the worst
	gUTF = False

# END * From SABnzbd+ * END

def guess_hacks(filename, guess):
	""" fix some strange guessit guessing:
		if guessit doesn't find a year in the file name it thinks it is episode,
		but we prefer it to be handled as movie instead
	"""
	if guess.get('type') == 'episode' and not guess.get('episodeNumber'):
		guess['type'] = 'movie'
		guess['title'] = guess.get('series')
		guess['year'] = '1900'

def add_common_mapping(old_filename, guess, mapping):

	# Original dir name, file name and extension
	original_dirname = os.path.basename(download_dir)
	original_fname, original_fext = os.path.splitext(os.path.split(os.path.basename(old_filename))[1])
	mapping.append(('%dn', original_dirname))
	mapping.append(('%fn', original_fname))
	mapping.append(('%ext', original_fext))
	mapping.append(('%EXT', original_fext.upper()))
	mapping.append(('%Ext', original_fext.title()))

	# Video information
	mapping.append(('%qf', guess.get('format', '')))
	mapping.append(('%qss', guess.get('screenSize', '')))
	mapping.append(('%qvc', guess.get('videoCodec', '')))
	mapping.append(('%qac', guess.get('audioCodec', '')))
	mapping.append(('%qah', guess.get('audioChannels', '')))
	mapping.append(('%qrg', guess.get('releaseGroup', '')))

def add_series_mapping(guess, mapping):

	# Show name
	series = guess.get('series', '')
	show_tname, show_tname_two, show_tname_three = get_titles(series, True)
	show_name, show_name_two, show_name_three = get_titles(series, False)
	mapping.append(('%sn', show_tname))
	mapping.append(('%s.n', show_tname_two))
	mapping.append(('%s_n', show_tname_three))
	mapping.append(('%sN', show_name))
	mapping.append(('%s.N', show_name_two))
	mapping.append(('%s_N', show_name_three))

	# season number
	season_num = str(guess.get('season', ''))
	mapping.append(('%s', season_num))
	mapping.append(('%0s', season_num.rjust(2,'0')))

	# episode names
	title = guess.get('title')
	if title:
		ep_tname, ep_tname_two, ep_tname_three = get_titles(title, True)
		ep_name, ep_name_two, ep_name_three = get_titles(title, False)
		mapping.append(('%en', ep_tname))
		mapping.append(('%e.n', ep_tname_two))
		mapping.append(('%e_n', ep_tname_three))
		mapping.append(('%eN', ep_name))
		mapping.append(('%e.N', ep_name_two))
		mapping.append(('%e_N', ep_name_three))
	else:
		mapping.append(('%en', ''))
		mapping.append(('%e.n', ''))
		mapping.append(('%e_n', ''))
		mapping.append(('%eN', ''))
		mapping.append(('%e.N', ''))
		mapping.append(('%e_N', ''))

	# episode number
	episode_num = str(guess.get('episodeNumber', ''))
	mapping.append(('%e', episode_num))
	mapping.append(('%0e', episode_num.rjust(2,'0')))

def add_movies_mapping(guess, mapping):

	# title
	name = guess.get('title', '')
	ttitle, ttitle_two, ttitle_three = get_titles(name, True)
	title, title_two, title_three = get_titles(name, True)
	mapping.append(('%title', title))
	mapping.append(('%.title', title_two))
	mapping.append(('%_title', title_three))

	# title (short forms)
	mapping.append(('%t', title))
	mapping.append(('%.t', title_two))
	mapping.append(('%_t', title_three))

	mapping.append(('%sn', title))
	mapping.append(('%s.n', title_two))
	mapping.append(('%s_n', title_three))

	mapping.append(('%sN', ttitle))
	mapping.append(('%s.N', ttitle_two))
	mapping.append(('%s_N', ttitle_three))

	# year
	year = str(guess.get('year', ''))
	mapping.append(('%y', year))

	# decades
	decade, decade_two = get_decades(year)
	mapping.append(('%decade', decade))
	mapping.append(('%0decade', decade_two))

def add_dated_mapping(guess, mapping):

	# title
	name = guess.get('title', '')
	ttitle, ttitle_two, ttitle_three = get_titles(name, True)
	title, title_two, title_three = get_titles(name, True)
	mapping.append(('%title', title))
	mapping.append(('%.title', title_two))
	mapping.append(('%_title', title_three))

	# title (short forms)
	mapping.append(('%t', title))
	mapping.append(('%.t', title_two))
	mapping.append(('%_t', title_three))

	mapping.append(('%sn', title))
	mapping.append(('%s.n', title_two))
	mapping.append(('%s_n', title_three))

	mapping.append(('%sN', ttitle))
	mapping.append(('%s.N', ttitle_two))
	mapping.append(('%s_N', ttitle_three))

	# Guessit doesn't provide episode names for dated tv shows
	mapping.append(('%desc', ''))
	mapping.append(('%.desc', ''))
	mapping.append(('%_desc', ''))

	# date
	date = guess.get('date')
	
	# year
	year = str(date.year)
	mapping.append(('%year', year))
	mapping.append(('%y', year))

	# decades
	decade, decade_two = get_decades(year)
	mapping.append(('%decade', decade))
	mapping.append(('%0decade', decade_two))

	# month
	month = str(date.month)
	mapping.append(('%m', month))
	mapping.append(('%0m', month.rjust(2, '0')))

	# day
	day = str(date.day)
	mapping.append(('%d', day))
	mapping.append(('%0d', day.rjust(2, '0')))

def construct_path(filename):
	""" Parses the filename and generates new name for renaming """

	if verbose:
		print("filename: %s" % filename)

	guess = guessit.guess_file_info(filename, filetype = 'autodetect', info = ['filename'])
	
	if verbose:
		print(guess.nice_string())

	type = guess.get('type')

	mapping = []
	
	# fix some strange guessit guessing:
	guess_hacks(filename, guess)

	add_common_mapping(filename, guess, mapping)

	if type == 'movie':
		date = guess.get('date')
		if date:
			dest_dir = dated_dir
			format = dated_format
			add_dated_mapping(guess, mapping)
		else:
			dest_dir = movies_dir
			format = movies_format
			add_movies_mapping(guess, mapping)
	elif type == 'episode':
		dest_dir = series_dir
		format = series_format
		add_series_mapping(guess, mapping)
	else:
		if verbose:
			print('Could not determine video type for %s' % filename)
		return None

	# Find out a char most suitable as dupe_separator
	guess_dupe_separator(format)
	
	# Add extension specifier if the format string doesn't end with it
	if format.rstrip('}')[-5:] != '.%ext':
		format += '.%ext'
	
	sorter = format.replace('\\', '/')

	if verbose:
		print('format: %s' % sorter)

	# Replace elements
	path = path_subst(sorter, mapping)

	if verbose:
		print('path after subst: %s' % path)

	# Cleanup file name 
	old_path = ''
	while old_path != path:
		old_path = path
		for key, name in REPLACE_AFTER.iteritems():
			path = path.replace(key, name)

	# Uppercase all characters encased in {{}}
	path = to_uppercase(path)

	# Lowercase all characters encased in {}
	path = to_lowercase(path)

	# Strip any extra strippable characters around foldernames and filename
	path, ext = os.path.splitext(path)
	path = strip_folders(path)
	path = path + ext

	path = os.path.normpath(path)

	if verbose:
		print('path after cleanup: %s' % path)

	new_path = os.path.join(dest_dir, path)
	
	if verbose:
		print('destination path: %s' % new_path)
		
	return new_path

# Flag indicating that anything was moved. Cleanup possible.
files_moved = False

# Flag indicating any error. Cleanup is disabled.
errors = False

# Process all the files in download_dir and its subdirectories
for root, dirs, files in os.walk(download_dir):
	for old_filename in files:
		try:
			old_path = os.path.join(root, old_filename)

			# Check extension
			ext = os.path.splitext(old_filename)[1]
			if ext not in video_extensions: continue
			
			# Check minimum file size			 
			if os.path.getsize(old_path) < min_size: continue
			
			# This is our video file, we should process it
			new_path = construct_path(old_path)
			
			# Move video file
			if new_path:
				new_path = rename(old_path, new_path)
				files_moved = True

				# Move satellite files
				if satellites:
					move_satellites(old_path, new_path)

		except Exception as e:
			errors = True
			print('[ERROR] Failed: %s' % old_filename)
			print('[ERROR] %s' % e)
			if verbose:
				traceback.print_exc()

# Cleanup if:
# 1) files were moved AND
# 2) no errors happen AND
# 3) all remaining files are smaller than <MinSize>
if cleanup and files_moved and not errors:
	cleanup_download_dir()

# Returing status to NZBGet
if errors:
	sys.exit(POSTPROCESS_ERROR)
elif files_moved:
	sys.exit(POSTPROCESS_SUCCESS)
else:
	sys.exit(POSTPROCESS_NONE)
