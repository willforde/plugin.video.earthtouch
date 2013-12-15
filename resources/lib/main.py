"""
	Copyright: (c) 2013 William Forde (willforde+xbmc@gmail.com)
	License: GPLv3, see LICENSE for more details
	
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Call Necessary Imports
from xbmcutil import listitem, urlhandler, plugin
import parsers

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Create urlhandler and Fetch Channel Page
		url = "http://www.earthtouchnews.com/videos/overview.aspx"
		sourceCode = urlhandler.urlread(url, 3628800)# TTL = 4 Week
		parser = parsers.ShowParser()
		
		# Add Youtube and Vimeo Channels
		self.add_youtube_channel("earthtouch", "-All Videos", hasPlaylist=True)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title_ignore_the)
		self.set_content("files")
		
		# Return List of Video Listitems
		return parser.parse(sourceCode)

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		sourceCode = urlhandler.urlread(plugin["url"], 28800) # TTL = 8 Hours
		parser = parsers.EpisodeParser()
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title_ignore_the, self.sort_method_video_runtime)
		self.set_content("episodes")
		
		# Return List of Video Listitems
		return parser.parse(sourceCode)