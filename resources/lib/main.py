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
		url = "http://earthtouch.tv/"
		sourceObj = urlhandler.urlopen(url, 3628800)# TTL = 4 Week
		parserCH = parsers.ChannelParser()
		
		# Setup Data Queues to handle Urls and SourceCode
		self.Queue = __import__("Queue")
		self.queueUrls = self.Queue.Queue()
		self.queueHTML = self.Queue.Queue()
		self.queueItem = self.Queue.deque()
		
		# Fetch Url List of Channels to Load and Start Fetcher Thread
		import threading
		for url in parserCH.parse(sourceObj.read()):
			self.queueUrls.put(url)
			threading.Thread(target=self.urlThread).start()
		
		# Start Thread to Handle HTML Source and wait to Finish
		threading.Thread(target=self.dataThread).start()
		self.queueUrls.join()
		self.queueHTML.join()
		
		# Add Youtube and Vimeo Channels
		self.add_youtube_channel("earthtouch", hasPlaylist=True)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("files")
		
		# Return List of Video Listitems
		return list(self.queueItem)
	
	def urlThread(self):
		# Grabs Url from Queue
		url = self.queueUrls.get(timeout=10)
		
		# Fetch SourceCode for url resource
		handle = urlhandler.HttpHandler()
		handle.add_response_handler()
		handle.add_cache_handler(604800)
		source = handle.open(url).read()
		
		# Place Source into HTML Queue
		self.queueHTML.put(source)
		
		# Signals to Queue that job is done
		self.queueUrls.task_done()
	
	def dataThread(self):
		try:
			while True:
				# Grabs Url from Queue
				source = self.queueHTML.get(timeout=10)
				
				# Parse Source
				parserSP = parsers.ShowParser()
				videoItems = parserSP.parse(source)
				self.queueItem.extend(videoItems)
				
				# Signals to Queue that job is done
				self.queueHTML.task_done()
		except self.Queue.Empty: pass

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		sourceCode = urlhandler.urlread(plugin["url"], 28800) # TTL = 8 Hours
		videoItems = parsers.EpisodeParser().parse(sourceCode)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title, self.sort_method_video_runtime)
		self.set_content("episodes")
		
		# Return List of Video Listitems
		return videoItems

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Fetch Page Source
		htmlSource = urlhandler.urlread(plugin["url"], 604800) # TTL = 1 Week
		
		# Fetch Video Url From JavaScript
		import re
		match = re.findall('swfobject.embedSWF\("http://www.youtube.com/v/(\S+?)\?enablejsapi=1', htmlSource)
		if match:
			from xbmcutil import videoResolver
			return videoResolver.youtube_com().decode(match[0])
		else:
			return self.sources(htmlSource)
