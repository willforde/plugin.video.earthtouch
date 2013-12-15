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

# Host Url
host = "http://www.earthtouchnews.com%s"

class ShowParser(HTMLParser.HTMLParser):
	"""
		Parses available shows withen categorys, i.e from http://www.earthtouchnews.com/videos/overview.aspx
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Show """
		
		# Class Vars
		self.divcount = None
		
		# Fetch MetaData Database and extract image
		from xbmcutil import storageDB
		self.metaData = storageDB.Metadata()
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Videos"
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif attrs:
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Find show-block elements and all div sub elements
			if tag == "div":
				# Increment div counter when within show-block
				if self.divcount is None and "class" in attrs and attrs["class"] == "gallery": self.divcount = 1
				elif self.divcount: self.divcount +=1
			
			# When within show-block fetch show data
			elif self.divcount == 5:
				# Fetch Video Url and Title
				if tag == "a" and "href" in attrs: 
					url = attrs["href"]
					if url[:4] == "http": self.item.urlParams["url"] = url
					else: self.item.urlParams["url"] = host % url
					title = url[url.rfind("/")+1:url.rfind(".")]
					self.item.setLabel(title.replace("-"," ").title())
					self.item.setIdentifier(title)
					if title in self.metaData: self.item.setFanartImage(self.metaData[title])
				
				# Fetch Image Url
				elif tag == "img" and "src" in attrs:
					if attrs["src"][:4] == "http": self.item.setThumbnailImage(attrs["src"])
					else: self.item.setThumbnailImage(host % attrs["src"])
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == "div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 4:
				self.append(self.item.getListitemTuple())
				self.reset_lists()

class EpisodeParser(HTMLParser.HTMLParser):
	"""
		Parses available episods for current show, i.e from http://www.earthtouchnews.com/videos/wild-sex.aspx
	"""
	
	def parse(self, html):
		""" Parses SourceCode and Scrape Episodes """
		
		# Class Vars
		self.divcount = None
		self.fanart = None
		self.section = 0
		self.epcount = 0
		
		# Fetch Quality Setting from Youtube Addon
		setting = plugin.getAddonSetting("plugin.video.youtube", "hd_videos")
		try: setting = int(setting)
		except: self.isHD = None
		else: self.isHD = setting >= 2
		
		# Strip out head info from html to fix malformed html
		headend = html.find("</head>") + 7
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try: self.feed(html[headend:])
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.setAudioInfo()
		self.item.setIsPlayable(True)
		self.item.urlParams["action"] = "system.source"
		
		# Set Quality Overlay
		if self.isHD is not None:
			self.item.setQualityIcon(self.isHD)
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif attrs:
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
		
			# Find show-block elements and all div sub elements
			if tag == "div":
				# Increment div counter when within show-block
				if self.divcount is None and "class" in attrs and attrs["class"] == "stories-gallery": self.divcount = 1
				elif self.divcount: self.divcount +=1
				elif self.fanart is None and "class" in attrs and "style" in attrs and attrs["class"] == "slidebgholder":
					fanart = attrs["style"]
					fanart = fanart[fanart.find("(")+1:fanart.find(")")]
					if fanart[:4] == "http": self.fanart = fanart
					else: self.fanart = host % fanart
					from xbmcutil import storageDB
					with storageDB.Metadata() as metaData:
						metaData[plugin["identifier"]] = self.fanart
						metaData.sync()
			
			# When within show-block fetch show data
			elif self.divcount == 5:
				# Fetch Video Url
				if tag == "a" and "href" in attrs and not "url" in self.item.urlParams:
					if attrs["href"][:4] == "http": self.item.urlParams["url"] = attrs["href"]
					else: self.item.urlParams["url"] = host % attrs["href"]
				
				# Fetch Image url
				elif tag == "span" and "style"  in attrs and "class" in attrs and attrs["class"] == "episodeImg":
					img = attrs["style"]
					img = img[img.find("(")+1:img.find(")")]
					if img[:4] == "http": self.item.setThumbnailImage(img)
					else: self.item.setThumbnailImage(host % img)
				
				# Fetch Title
				elif tag == "img" and "alt" in attrs:
					self.epcount += 1
					self.item.setLabel("%i. %s" % (self.epcount, attrs["alt"]))
				
				# Fetch Video runtime
				elif tag == "strong" and "class" in attrs and attrs["class"] == "title":
					self.section = 101
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101:
			self.item.setDurationInfo(data[data.find(" ")+1:])
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == "div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 3:
				if self.fanart: self.item.setFanartImage(self.fanart)
				self.append(self.item.getListitemTuple())
				self.reset_lists()
