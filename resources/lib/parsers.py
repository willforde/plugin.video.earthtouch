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
host = u"http://www.earthtouchnews.com%s"

class ShowParser(HTMLParser.HTMLParser):
	"""
		Parses available shows withen categorys, i.e from http://www.earthtouchnews.com/videos/overview.aspx
	"""
	
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Show """
		
		# Class Vars
		self.divcount = None
		self.section = None
		
		# Fetch MetaData Database and extract image
		from xbmcutil import storageDB
		self.metaData = storageDB.Metadata()
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError:
			pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Videos"
		self.item.addContextMenuItem(plugin.getstr(21866), "XBMC.Container.Update", action="Cat", updatelisting="true")
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		
		# Find show-block elements and all div sub elements
		elif tag == u"div":
			# Increment div counter when within show-block
			if self.divcount: self.divcount +=1
			else:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				if u"class" in attrs and attrs[u"class"] == u"gallery": self.divcount = 1
		
		# When within show-block fetch show data
		elif self.divcount >= 5:
			if attrs:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				
				# Fetch Video Url and Title
				if tag == u"a" and u"href" in attrs: 
					url = attrs[u"href"]
					if url[:4] == u"http": self.item.urlParams["url"] = url
					else: self.item.urlParams["url"] = host % url
					title = url.replace(u"/videos/",u"").replace(u"/",u"")
					self.item.setLabel(title.replace(u"-",u" ").title())
					self.item.setIdentifier(title)
					if title in self.metaData: self.item.setFanart(self.metaData[title])
				
				# Fetch Image Url
				elif tag == u"img" and u"src" in attrs:
					if attrs[u"src"][:4] == u"http": self.item.setThumb(attrs[u"src"])
					else: self.item.setThumb(host % attrs[u"src"])
				
				# Fetch Episode Count
				elif tag == u"span" and u"class" in attrs and attrs[u"class"] == u"item":
					self.section = 101
			
			# Fetch Plot info
			elif tag == u"p":
				self.section = 102
	
	def handle_data(self, data):
		# Fetch Episode Count
		if self.section == 101: # title
			title = u"%s (%s)" % (self.item.infoLabels["title"], data[:data.find(u" ")])
			self.item.setLabel(title)
			self.section = None
		# Fetch Plot info when within "p" block
		if self.section == 102: # Plot
			self.item.infoLabels["plot"] = data.strip()
			self.section = None
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 4:
				self.append(self.item.getListitemTuple())
				self.reset_lists()

class EpisodeParser(HTMLParser.HTMLParser):
	"""
		Parses available episods for current show, i.e from http://www.earthtouchnews.com/videos/wild-sex.aspx
	"""
	
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Episodes """
		
		# Class Vars
		self.divcount = None
		self.fanart = None
		self.section = 0
		self.epcount = 0
		
		# Fetch Quality Setting from Youtube Addon
		try: setting = int(plugin.getAddonSetting("plugin.video.youtube", "hd_videos"))
		except: self.isHD = None
		else:
			if setting == 1: self.isHD = False
			elif setting == 0 or setting >= 2: self.isHD = True
			else: self.isHD = None
		
		# Strip out head info from html to fix malformed html
		if encoding: html = html.decode(encoding)
		headend = html.find(u"</head>") + 7
		
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
		self.item.setAudioFlags()
		self.item.urlParams["action"] = "system.source"
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif attrs:
			# Find show-block elements and all div sub elements
			if tag == u"div":
				# Increment div counter when within show-block
				if self.divcount: self.divcount +=1
				else:
					# Convert Attributes to a Dictionary
					attrs = dict(attrs)
					
					# Check for required section
					if u"class" in attrs and attrs[u"class"] == u"episodes-gallery": self.divcount = 1
					elif self.fanart is None and u"class" in attrs and u"style" in attrs and attrs[u"class"] == u"slidebgholder":
						fanart = attrs[u"style"]
						fanart = fanart[fanart.find(u"(")+1:fanart.find(u")")]
						if fanart[:4] == u"http": self.fanart = fanart
						else: self.fanart = host % fanart
						from xbmcutil import storageDB
						with storageDB.Metadata() as metaData:
							metaData[plugin["identifier"]] = self.fanart
							metaData.sync()
			
			# When within show-block fetch show data
			elif self.divcount >= 4:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				
				# Fetch Video Url
				if tag == u"a" and u"href" in attrs and not u"url" in self.item.urlParams:
					if attrs[u"href"][:4] == u"http": self.item.urlParams["url"] = attrs[u"href"]
					else: self.item.urlParams["url"] = host % attrs[u"href"]
				
				# Fetch Image url
				elif tag == u"span" and u"style" in attrs and u"class" in attrs and attrs[u"class"] == u"episodeImg":
					img = attrs[u"style"]
					img = img[img.find(u"(")+1:img.find(u")")].replace("/remote.axd?","")
					if img[:4] == u"http": self.item.setThumb(img)
					else: self.item.setThumb(host % img)
				
				# Fetch Title
				elif tag == u"img" and u"alt" in attrs:
					self.epcount += 1
					self.item.setLabel(u"%i. %s" % (self.epcount, attrs[u"alt"]))
				
				# Fetch Video runtime
				elif tag == u"strong" and u"class" in attrs and attrs[u"class"] == u"title":
					self.section = 101
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101:
			data = data[data.find(u" ")+1:].strip()
			if data: self.item.setDuration(data)
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 3:
				if self.fanart: self.item.setFanart(self.fanart)
				self.append(self.item.getListitemTuple(True, self.isHD))
				self.reset_lists()
