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
import HTMLParser
from xbmcutil import listitem, plugin

class ChannelParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://earthtouch.tv/
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Channels """
		
		# Class Vars
		self.section = 0
		self.currentTag = ""
		
		# Proceed with parsing
		self.results = []
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if attrs:
			# Convert To Dict
			attrs = dict(attrs)
		
			# Search for each "ul" Menu Element
			if tag == "ul" and "class" in attrs and ((self.section == 0 and attrs["class"] == "desktop-menu") or (self.section == 2 and attrs["class"] == "dropdown-menu")):
				self.section += 1
			
			# Find Channel Names and Urls
			elif self.section == 3 and tag == "a" and "href" in attrs:
				url = "http://earthtouch.tv" + attrs["href"]
				self.results.append(url)
		
		# Track Current Tag
		self.currentTag = tag
	
	def handle_data(self, data):
		# Check if for Correct Section
		if self.section == 1 and self.currentTag == "a" and data == "CHANNELS":
			self.section += 1
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if self.section == 3 and tag == "ul":
			raise plugin.ParserError

class ShowParser(HTMLParser.HTMLParser):
	"""
		Parses available shows withen categorys, i.e from http://earthtouch.tv/uncensored/
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Show """
		
		# Class Vars
		self.showBlock = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		self.feed(html)
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Videos"
		self.temp = ""
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if attrs: attrs = dict(attrs)
		
		# Find show-block elements and all div sub elements 
		if tag == "div" and (self.showBlock >= 1 or ("class" in attrs and attrs["class"] == "show-block")):
			# Increment div counter
			self.showBlock += 1
		
		# If within show-block fetch show data
		elif self.showBlock >= 1:
			# Fetch Episode Count
			if tag == "span" and "class" in attrs and attrs["class"] == "timestamp":
				self.temp = "episodes"
			
			# Fetch Image url
			elif tag == "img" and "src" in attrs:
				self.item.setThumbnailImage("http://earthtouch.tv" + attrs["src"])
			
			# Fetch Show Name
			elif tag == "h3" and not attrs:
				self.temp = "title"
			
			# Fetch Url to Show
			elif tag == "a" and "href" in attrs:
				url = attrs["href"].rsplit("/", 2)[0]
				if url == "/classic-wildlife/earth-touch-on-tv":
					self.reset_lists()
					self.showBlock = 0
				else:
					self.item.urlParams["url"] = "http://earthtouch.tv" + url
			
			# Fetch Plot Information
			elif tag == "p" and not attrs:
				self.temp = "plot"
	
	def handle_data(self, data):
		# When within show-block fetch data
		if self.showBlock >= 1:
			getTemp = self.temp
			# Check if need to save episodes data
			if getTemp == "episodes":
				self.item.infoLabels["episodes"] = int(data.strip().split()[0])
				self.temp = ""
			
			# Check if need to save plot data
			elif getTemp == "plot":
				self.item.infoLabels["plot"] = data.strip()
				self.temp = ""
			
			# Check if need to save show name
			elif getTemp == "title":
				if "episodes" in self.item.infoLabels: self.item.setLabel("%s (%s)" % (data.strip(), self.item.infoLabels["episodes"]))
				else: self.item.setLabel(data.strip())
				self.temp = ""
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == "div" and self.showBlock >= 1:
			self.showBlock -= 1
			
			# When at closeing 7tag for show-block, save fetched data
			if self.showBlock == 0:
				self.results.append(self.item.getListitemTuple())
				self.reset_lists()

class EpisodeParser(HTMLParser.HTMLParser):
	"""
		Parses available episods for current show, i.e from http://earthtouch.tv/uncensored/wild-sex/
	"""
	
	def parse(self, html):
		""" Parses SourceCode and Scrape Episodes """
		
		# Class Vars
		self.section = 0
		self.fanart = None
		
		# Fetch Quality Setting from Youtube Addon
		setting = plugin.getAddonSetting("plugin.video.youtube", "hd_videos")
		try: setting = int(setting)
		except: self.isHD = None
		else: self.isHD = setting >= 2
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		self.feed(html)
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.setAudioInfo()
		self.item.setIsPlayable(True)
		self.item.urlParams["action"] = "PlayVideo"
		self.temp = ""
		self.title = ""
		
		# Set Quality Overlay
		if self.isHD is not None:
			self.item.setQualityIcon(self.isHD)
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if attrs: attrs = dict(attrs)
		
		# Find Fanart Image
		#if self.fanart: self.item.setFanartImage(self.fanart)
		#elif tag == "img" and "id" in attrs and attrs["id"] == "bgimg":
		#	self.fanart = "http://earthtouch.tv" + attrs["src"]
		#	self.item.setFanartImage(self.fanart)
		
		# Find es-carousel elements and all div sub elements and increment div counter when found
		if tag == "div" and (self.section >=1 or ("id" in attrs and attrs["id"] == "carousel-ep")):
			self.section += 1
		
		# If within eps-container fetch episode data
		elif self.section >= 1:
			# Fetch Episode duration
			if tag == "span" and "class" in attrs and attrs["class"] == "timestamp":
				self.temp = "duration"
			
			# Fetch Image and episode Name
			elif tag == "img" and "src" in attrs:
				self.item.setThumbnailImage("http://earthtouch.tv" + attrs["src"])
			
			# Fetch episode Name
			elif tag == "h3" and not attrs:
				self.temp = "title"
			
			# Fetch Season & episode info
			elif tag == "small" and not attrs:
				self.temp = "episode"
			
			# Fetch Episode Url
			elif tag == "a" and "class" in attrs and attrs["class"] == "ir eps-play":
				self.item.urlParams["url"] = "http://earthtouch.tv" + attrs["href"]
			
			# Fetch Episode Plot
			elif tag == "p" and not attrs:
				self.temp = "plot"
	
	def handle_data(self, data):
		# When within eps-container fetch data
		if self.section >= 1:
			getTemp = self.temp
			# Check if need to save episode duration
			if getTemp == "duration":
				self.item.setDurationInfo(data)
				self.temp = ""
			
			# Check if need to save episode plot
			elif getTemp == "plot":
				self.item.infoLabels["plot"] = data.strip()
				self.temp = ""
			
			# Check if need to save episode name
			elif getTemp == "title":
				self.title = data
				self.temp = ""
			
			# Check if need to save episode number
			elif getTemp == "episode":
				self.item.infoLabels["episode"] = data.title()
				self.temp = ""
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.section >= 1:
			if tag == "div":
				self.section -= 1
			
			# At end if li save episode data
			elif tag == "li":
				# Modify Data Before Saving
				data = self.item.infoLabels["episode"].replace("Season","").replace("Episode","").replace(" ","").split("-")
				
				if len(data) == 2: self.item.setLabel("S%sE%s %s" % (data[0].rjust(2,"0"), data[1].rjust(2,"0"), self.title))
				else: self.item.setLabel("%s. %s" % (data[-1], self.title))
				
				self.results.append(self.item.getListitemTuple())
				self.reset_lists()
