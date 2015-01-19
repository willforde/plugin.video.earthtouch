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
		if "url" in plugin: url = "http://www.earthtouchnews.com/videos/%s/" % plugin["url"]
		else: url = u"http://www.earthtouchnews.com/videos/shows/"
		sourceObj = urlhandler.urlopen(url, 604800)# TTL = 1 Week
		videoItems = parsers.ShowParser().parse(sourceObj)
		sourceObj.close()
		
		# Add Youtube and Vimeo Channels
		self.add_youtube_channel(u"earthtouch", u"-%s" % plugin.getuni(16100), hasPlaylist=True, hasHD=True)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title_ignore_the)
		
		# Return List of Video Listitems
		return videoItems

class Cat(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode of Site
		url = u"http://www.earthtouchnews.com/videos/shows/"
		sourceCode = urlhandler.urlread(url, 604800, stripEntity=False) # TTL = 1 Week
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title_ignore_the)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode) 
	
	def regex_scraper(self, sourceCode):
		# Create Speedup vars
		import re
		localListitem = listitem.ListItem
		
		# Fetch Video Information from Page Source
		for url in re.findall('<li><a class="" href="/videos/(\S+?)/">', sourceCode):		
		# Create listitem of Data
			item = localListitem()
			item.setLabel(url.replace("-", " ").title())
			item.setParamDict(url=url)
			
			# Store Listitem data
			yield item.getListitemTuple(False)

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		sourceObj = urlhandler.urlopen(plugin["url"], 14400) # TTL = 4 Hours
		videoItems = parsers.EpisodeParser().parse(sourceObj)
		sourceObj.close()
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title_ignore_the, self.sort_method_video_runtime)
		
		# Return List of Video Listitems
		return videoItems