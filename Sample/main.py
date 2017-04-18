# -*- coding: utf-8 -*-
#######################
###  Picurl Add On  ###
#######################
import CONFIG as Config
import urllib2
import re
import gzip
import zlib
import StringIO
import requests

import dateutil.parser as dparser
import selenium.webdriver
import json
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from titlecase import titlecase

from bs4 import BeautifulSoup
import linecache
import datetime

import parsedatetime as pdf
import pytz
from pytz import timezone

import os
import sys
sys.path.append(os.path.abspath('../Scripts'))
import dbConnection
from feedData import insertEventData, insertFilter
from getGeoInfo import getGeoInfo
import platform

reload(sys)
sys.setdefaultencoding('utf-8') 

#####################
#database setting
conn = dbConnection.conn
Agnes = conn.Agnes
itemFilter = conn.itemFilter
eventslowercase = Agnes.eventslowercase
#events = Agnes.events_auto
#urlFilter = itemFilter.urlFilter_auto
#events = Agnes.events
#urlFilter = itemFilter.urlFilter
events = Agnes.events
urlFilter = itemFilter.urlFilter
communities = Agnes.communities
evtSource_Community = Agnes.evtSource_Community
######################

visitList = []
visitedList = []
crawledItem = 0

stopSign = False

#preset parameter
evtnamePattern = ""
evtdescPattern = ""
starttimePattern = ""
startdatePattern = ""
endtimePattern = ""
enddatePattern = ""
timePattern = ""
datePattern = ""
dateAndTimePattern = ""
locationPattern = ""
tagsPattern = []
mainUrlList = ""
urlREList = []
subUrlList = []
domain = ""
evtsource = ""
picurl = ""
evtnameModifiedList = []
evtdescModifiedList = []
locationModifiedList = []
urlPrefixList = []
filterElementList = []
additionalTags = []
specificLocation = ""
unqualifiedStarttimeCount = 0
unqualifiedEndtimeCount = 0
unqualifiedFlag = 3

cityCoordinateDict = {}
localityDict = {}
evtsourceCommunityDict = {}
evtsourceYearDict = {}

def main():
	load_element()
	visit()

def visit():
	global mainUrlList

	visitList.extend(mainUrlList)
	visit_page()

def load_element():
	global evtnamePattern
	global evtdescPattern
	global starttimePattern
	global startdatePattern
	global endtimePattern
	global enddatePattern
	global timePattern
	global dateAndTimePattern
	global locationPattern
	global evtsource
	global mainUrlList
	global urlREList
	global domain
	global urlPrefix
	global filterElementList
	global datePattern
	global picurlPattern
	global additionalTags
	global subUrlList
	global evtnameModifiedList
	global evtdescModifiedList
	global locationModifiedList
	global tagsPattern
	global specificLocation
	global timezoneName
	global detailedPageXPath
	global nextPageXPath
	global goBackXPath
	global version

	global starttimeModifiedList
	global startdateModifiedList
	global endtimeModifiedList
	global enddateModifiedList
	global dateModifiedList
	global timeModifiedList
	global dateAndTimeModifiedList

	global cityCoordinateDict
	global localityDict
	global evtsourceCommunityDict
	global evtsourceYearDict

	evtnamePattern = Config.evtname
	evtdescPattern = Config.evtdesc
	starttimePattern = Config.starttime
	startdatePattern = Config.startdate
	endtimePattern = Config.endtime
	enddatePattern = Config.enddate
	timePattern = Config.time
	dateAndTimePattern = Config.dateAndTime
	locationPattern = Config.location
	evtsource = Config.source
	mainUrlList = Config.mainUrlList
	urlREList = Config.urlREList
	subUrlList = Config.subUrlList
	domain = Config.domain
	urlPrefixList = Config.urlPrefixList
	filterElementList = Config.filterElementList
	datePattern = Config.date
	picurlPattern = Config.picurl
	additionalTags = Config.additionalTags
	tagsPattern = Config.tags
	evtnameModifiedList = Config.evtnameModifiedList
	evtdescModifiedList = Config.evtdescModifiedList
	locationModifiedList = Config.locationModifiedList
	specificLocation = Config.specificLocation
	timezoneName = Config.timezoneName
	detailedPageXPath = Config.detailedPageXPath
	nextPageXPath = Config.nextPageXPath
	goBackXPath = Config.goBackXPath
	starttimeModifiedList = Config.starttimeModifiedList
	startdateModifiedList = Config.startdateModifiedList
	endtimeModifiedList = Config.endtimeModifiedList
	enddateModifiedList = Config.enddateModifiedList
	dateModifiedList = Config.dateModifiedList
	timeModifiedList = Config.timeModifiedList
	dateAndTimeModifiedList = Config.dateAndTimeModifiedList
	version = Config.version

	if evtsource == "":
		evtsource = re.sub(r'https?:(//)?(www\.)?', '', mainUrlList[0])
		evtsource = re.sub(r'(?<=com|net|edu|org)/[\w\W]*', '', evtsource)

	if domain == "":
		domain = re.sub(r'(?<=com|net|edu|org)/[\w\W]*', '', mainUrlList[0])

	for eventCommunity in communities.find():
		coordinate = eventCommunity["coordinate"]
		locality = eventCommunity["locality"]
		cityCoordinateDict[eventCommunity["community"]] = coordinate
		if locality not in cityCoordinateDict.keys():
			cityCoordinateDict[locality] = coordinate
		localityDict[eventCommunity["community"]] = locality

	for evtsourceCommunity in evtSource_Community.find():
		evtsourceCommunityDict[evtsourceCommunity["evtsource"]] = evtsourceCommunity["community"]
		evtsourceYearDict[evtsourceCommunity["evtsource"]] = evtsourceCommunity["year"]

def visit_page():
	global visitList
	global visitedList
	global crawledItem
	global detailedPageXPath
	global goBackXPath
	global nextPageXPath
	global version

	##########################
	# switch driver
	systemPlatform = platform.system()
	if systemPlatform == "Linux":
		driver = selenium.webdriver.PhantomJS(executable_path="../Scripts/linuxOS/phantomjs")
	else:
		if version == "debug":
			driver = selenium.webdriver.Chrome(executable_path="../Scripts/macOS/chromedriver")
		else:
			driver = selenium.webdriver.PhantomJS(executable_path="../Scripts/macOS/phantomjs")
	##########################

	while len(visitList) != 0:
		requrl = visitList[0]
		driver.get(requrl)
		try:
			i = 0
			while i < 3: 
				time.sleep(3)
				elements = driver.find_elements_by_xpath(detailedPageXPath)
				length = len(elements)
				if length != 0:
					print "Data Found!"
					break
				driver.get(requrl)
				i += 1

			if length == 0:
				print "No more data!!"

			for i in range(0, length):
				try:
					elements = driver.find_elements_by_xpath(detailedPageXPath)
					scrollTopPos = i*100
					js = "var q=document.documentElement.scrollTop=" + str(scrollTopPos)
					driver.execute_script(js)
					element = elements[i]
					element.click()
					time.sleep(1)

					# judge there is a new tab or not
					driver.switch_to_window(driver.window_handles[-1])

					fetch_information(driver)

					if len(driver.window_handles) > 1:
						#if there is new tab then close the new tab and switch to the old tab
						driver.close()
						driver.switch_to_window(driver.window_handles[0])
					else:
						#if there is no new tabs then go back
						#go back
						if goBackXPath == "":
							#click go back button to go back
							driver.execute_script("window.history.go(-1)")
						else:
							#click go back element to go back
							gobackELement = driver.find_element_by_xpath(goBackXPath)
							gobackELement.click()
					time.sleep(1)

				except Exception as e:
					print e
					printException()
					driver.get(requrl)

			if nextPageXPath != "":
				nextPageElement = driver.find_element_by_xpath(nextPageXPath)
				nextPageElement.click()
			
		except Exception as e:
			print e
			printException()


		visitList.remove(requrl)
		visitedList.append(requrl)


def fetch_information(driver):
	requrl = driver.current_url
	global evtnamePattern
	global evtdescPattern
	global starttimePattern
	global startdatePattern
	global endtimePattern
	global enddatePattern
	global timePattern
	global locationPattern
	global dateAndTimePattern
	global evtsource
	global datePattern
	global picurlPattern
	global tagsPattern
	global additionalTags
	global specificLocation
	global evtsourceCommunityDict
	global evtsourceYearDict

	global starttimeModifiedList
	global startdateModifiedList
	global endtimeModifiedList
	global enddateModifiedList
	global dateModifiedList
	global timeModifiedList
	global dateAndTimeModifiedList

	currentTime =  datetime.datetime.now()
	currentDate = currentTime.strftime('%Y-%m-%d')
	currentDate = datetime.datetime.strptime(currentDate, '%Y-%m-%d')
	formerDate = currentDate + datetime.timedelta(days=-1)

	evtname = ""
	evtdesc = ""
	starttime = ""
	startdate = ""
	endtime = ""
	enddate = ""
	time = ""
	dateAndTime = ""
	location = ""
	date = ""
	picurl = ""
	tags = []

	# raw_input(requrl)
	# print HTML
	# raw_input(123)

	print "########################"
	print requrl

	try:
		evtname = driver.find_elements_by_xpath(evtnamePattern)
		evtname = get_text(evtname)
		# print "evtname: ",
		# print evtname
	except:
		print "evtname xpath is empty string or wrong!"
	
	try:
		if evtdescPattern != "":
			evtdesc = driver.find_elements_by_xpath(evtdescPattern)
			evtdesc = get_text(evtdesc)
			# print "evtdesc: ",
			# print evtdesc
	except:
		print "evtdesc xpath is empty string or wrong!"


	if locationPattern != "":
		try:
			location = driver.find_elements_by_xpath(locationPattern)
			location = get_text(location)
			# print "location: ",
			# print location
		except:
			print "location xpath is wrong!"

	if specificLocation != "":
		location = specificLocation

	if evtname == "":
		print "evtname unqualified: ",
		print requrl
		return 0
	elif location == "":
		print "location unqualified: ",
		print requrl
		return 0

	if picurlPattern != "":
		picurl = driver.find_elements_by_xpath(picurlPattern)
		picurl = get_text(picurl)
		picurl = get_picurl(picurl)
		if picurl != "" and picurl[0] == "/" and picurl[1] != "/":
			picurl = evtsource + picurl
		elif picurl != "" and picurl[0] == "/" and picurl[1] == "/":
			picurl = picurl[2:]
		# print "picurl: ",
		# print picurl

	if tagsPattern != "":
		tags = driver.find_elements_by_xpath(tagsPattern)
		tags = get_text(tags)
		tags = analyze_tags(tags)
		# print "tags: "
		# print tags
	
	if dateAndTimePattern != "":
		dateAndTime = driver.find_elements_by_xpath(dateAndTimePattern)
		dateAndTime = get_text(dateAndTime)
		if dateAndTimeModifiedList != []:
			for dateAndTimeModifiedItem in dateAndTimeModifiedList:
				dateAndTime = re.sub(dateAndTimeModifiedItem, '', dateAndTime)
		# print "dateAndTime: ",
		# print dateAndTime


	if datePattern != "":
		date = driver.find_elements_by_xpath(datePattern)
		date = get_text(date)
		if dateModifiedList != []:
			for dateModifiedItem in dateModifiedList:
				date = re.sub(dateModifiedItem, '', date)
		# print "date: ",
		# print date

	if timePattern != "":
		time = driver.find_elements_by_xpath(timePattern)
		time = get_text(time)
		if timeModifiedList != []:
			for timeModifiedItem in timeModifiedList:
				time = re.sub(timeModifiedItem, '', time)
		# print "time: ",
		# print time


	if starttimePattern != "":
		starttime = driver.find_elements_by_xpath(starttimePattern)
		starttime = get_text(starttime)
		if starttimeModifiedList != []:
			for starttimeModifiedItem in starttimeModifiedList:
				starttime = re.sub(starttimeModifiedItem, '', starttime)
		# print "starttime: ",
		# print starttime

	if endtimePattern != "":
		endtime = driver.find_elements_by_xpath(endtimePattern)
		endtime = get_text(endtime)
		if endtimeModifiedList != []:	
			for endtimeModifiedItem in endtimeModifiedList:
				endtime = re.sub(endtimeModifiedItem, '', endtime)
		# print "endtime: ",
		# print endtime


	if startdatePattern != "":
		startdate = driver.find_elements_by_xpath(startdatePattern)
		startdate = get_text(startdate)
		if startdateModifiedList != []:
			for startdateModifiedItem in startdateModifiedList:
				startdate = re.sub(startdateModifiedItem, '', startdate)
		# print "stardate: ",
		# print startdate

	if enddatePattern != "":
		enddate = driver.find_elements_by_xpath(enddatePattern)
		enddate = get_text(enddate)
		if enddateModifiedList != []:
			for enddateModifiedItem in enddateModifiedList:
				enddate = re.sub(enddateModifiedItem, '', enddate)
		# print "enddate: ",
		# print enddate

	url = driver.current_url

	starttime, endtime = analyze_time(dateAndTime, date, time, starttime, endtime, startdate, enddate)

	if starttime == "":
		print "Can't crawl time information: ",
		print requrl
		return 0

	community = evtsourceCommunityDict[evtsource]
	year = evtsourceYearDict[evtsource]
	fetch_data(url, evtname, evtdesc, starttime, endtime, location, community, evtsource, formerDate, tags, additionalTags, picurl, year)

def get_text(elementList):
	text = ""
	for element in elementList:
		tempText = element.get_attribute("outerHTML")
		tempText = re.sub(r'<[\w\W]*?>', '', tempText)
		text += tempText + " "
	text = text.strip()
	return text

def get_picurl(picurlHTML):
	picurl = ""
	if "src" in picurlHTML:
		picurl = re.sub(r'[\w\W]*src=[\"|\']', '', picurl)
		picurl = re.sub(r'\"[\w\W]*', '', picurl)

	if picurl == "":
		urlPicStr = "url\([\w\W]*?\)"
		urlPicPattern = re.compile(urlPicStr)
		picurlList = urlPicPattern.findall(picurl)
		if len(picurlList) > 0:
			picurl = picurlList[0]
		if picurl != "":
			picurl = re.sub(r'url\(', '', picurl)
			picurl = re.sub(r'\)', '', picurl)
	
	picurl = picurl.strip()
	return picurl

def analyze_tags(tags):
	tags = tags.strip()
	tagsSplitCharList = [",", "|", ";", "\\", "/", ".", "\r\n"]
	tagsSplitChar = ""
	for tagsSplitCharItem in tagsSplitCharList:
		if tagsSplitCharItem in tags:
			tagsSplitChar = tagsSplitCharItem
			break
	if tagsSplitChar != "":
		tagsList = tags.split(tagsSplitChar)
	else:
		tagsList = [tags]
	returnedTagsList = []
	for tag in tagsList:
		tag = tag.strip()
		if tag != "":
			returnedTagsList.append(tag)
	return returnedTagsList


#precoss some time format
def format_time(timeString):
	timeString = timeString.lower()
	uselessCharList = [
		"|", "@", ",", "from", 
		" est", " cst", " mst", " pst", " akst", " hast", " edt", " cdt", " mdt", " pdt", " akdt", " hadt", " et", " ct", " mt", " pt",
		"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
		"mon ", "tue ", "tues ", "wed ", "thu ", "thur ", "thurs ", "fri ", "sat ", "sun ", "·"
		]

	if "time:" or "time" in timeString:
		timeString = re.sub(r'time:?', '', timeString)
	if "date:" or "date" in timeString:
		timeString = re.sub(r'date:?', '', timeString)

	for uselessChar in uselessCharList:
		#build regex format
		if len(uselessChar) == 1:
			uselessChar = "\\" + uselessChar
		timeString = re.sub(uselessChar, '', timeString, flags = re.I)

	timeString = re.sub(r'\([\w\W]*?\)', '', timeString)
	timeString = re.sub(r'noon', '12:00 pm', timeString)
	timeString = re.sub(r'midnight', '12:00 am', timeString)

	timeString = re.sub(r'\s{2,}', ' ', timeString)
	timeString = timeString.strip()
	return timeString

def analyze_time(dateAndTime, date, time, starttime, endtime, startdate, enddate):
	returnedStarttime = ""
	returnedEndtime = ""

	splitCharList = [" to ", "until", "-", u"–", "—"]
	splitCharacter = ""

	dateAndTime = format_time(dateAndTime)
	date = format_time(date)
	time = format_time(time)
	starttime = format_time(starttime)
	endtime = format_time(endtime)
	startdate = format_time(startdate)
	enddate = format_time(enddate)

	try:
		if startdate != "" and enddate != "" and starttime != "" and endtime != "":
			starttime = starttime.encode("ascii","ignore")
			endtime = endtime.encode("ascii","ignore")
			
			returnedStarttime = parsetime(startdate + " " + starttime)
			returnedEndtime = parsetime(enddate + " " + endtime)
		else:
			if dateAndTime != "":
				for splitChar in splitCharList:
					if splitChar in dateAndTime:
						splitCharacter = splitChar
						break

				if splitCharacter != "":
					# rawStarttime = dateAndTime.split(splitCharacter)[0]
					# rawEndtime = dateAndTime.split(splitCharacter)[1]

					rawStarttime, rawEndtime = splittime(dateAndTime, splitCharacter)

					rawStarttime = rawStarttime.encode("ascii","ignore")
					rawEndtime = rawEndtime.encode("ascii","ignore")

					isStarttimeDateExist = isDateExist(rawStarttime)
					isEndtimeDateExist = isDateExist(rawEndtime)

					if isEndtimeDateExist == False:
						returnedStarttime = parsetime(rawStarttime)
						if isDateExistInEndDay(rawEndtime):
							returnedEndtime = parsetime(rawEndtime)
						else:
							returnedEndtime = parsetime(returnedStarttime.strftime('%Y-%m-%d') + " " + rawEndtime)
					elif isStarttimeDateExist == True:
						returnedStarttime = parsetime(rawStarttime)
						returnedEndtime = parsetime(rawEndtime)
					elif isStarttimeDateExist == False:
						returnedEndtime = parsetime(rawEndtime)
						returnedStarttime = parsetime(returnedEndtime.strftime('%Y-%m-%d') + " " + rawStarttime)
					else:
						print "ERROR"
						raise NameError("returnTimeError")

					"""
					returnedStarttime = parsetime(dateAndTime.split(splitCharacter)[0])
					if isDateExist(dateAndTime.split(splitCharacter)[1]):
						returnedEndtime = parsetime(dateAndTime.split(splitCharacter)[1])
					else:
						returnedEndtime = parsetime(returnedStarttime.strftime('%Y-%m-%d') + " " + dateAndTime.split(splitCharacter)[1])
					"""
				elif endtime != "":
					dateAndTime = dateAndTime.encode("ascii","ignore")
					endtime = endtime.encode("ascii","ignore")
					returnedStarttime = parsetime(dateAndTime)
					returnedEndtime = parsetime(returnedStarttime.strftime('%Y-%m-%d') + " " + endtime)
				else:
					dateAndTime = dateAndTime.encode("ascii","ignore")
					returnedStarttime = parsetime(dateAndTime)
					returnedEndtime = returnedStarttime + datetime.timedelta(hours=1)

			else:
				if date != "":
					if time != "":
						for splitChar in splitCharList:
							if splitChar in time:
								splitCharacter = splitChar
								break
						if splitCharacter != "":

							# rawStarttime = time.split(splitCharacter)[0]
							# rawEndtime = time.split(splitCharacter)[1]

							rawStarttime, rawEndtime = splittime(time, splitCharacter)

							rawStarttime = rawStarttime.encode("ascii","ignore")
							rawEndtime = rawEndtime.encode("ascii","ignore")

							returnedStarttime = parsetime(date + " " + rawStarttime)
							returnedEndtime = parsetime(date + " " + rawEndtime)

						else:
							date = date.encode("ascii","ignore")
							time = time.encode("ascii","ignore")

							returnedStarttime = parsetime(date + " " + time)
							returnedEndtime = returnedStarttime + datetime.timedelta(hours=1)
					else:
						date = date.encode("ascii","ignore")
						starttime = starttime.encode("ascii","ignore")
						endtime = endtime.encode("ascii","ignore")

						if starttime != "" and endtime != "":
							returnedStarttime = parsetime(date + " " + starttime)
							returnedEndtime = parsetime(date + " " + endtime)
						else:
							returnedStarttime = parsetime(date + " " + "00:01:00")
							returnedEndtime = returnedStarttime
				else:
					starttime = starttime.encode("ascii","ignore")
					endtime = endtime.encode("ascii","ignore")

					if starttime != "" and endtime != "":
						returnedStarttime = parsetime(starttime)
						returnedEndtime = parsetime(endtime)
					else:
						returnedStarttime = ""
						returnedEndtime = ""
	except Exception as e:
		print e
		print "Something wrong in parsing time"
		printException()

	return returnedStarttime, returnedEndtime

def splittime(timeString, splitCharacter):
	tempStarttime = timeString.split(splitCharacter)[0]
	tempEndtime = timeString.split(splitCharacter)[1]
	if "am" in tempEndtime:
		if "am" not in tempStarttime and "pm" not in tempStarttime:
			tempStarttime += "am"
	elif "pm" in tempEndtime:
		if "am" not in tempStarttime and "pm" not in tempStarttime:
			tempStarttime += "pm"
	return tempStarttime, tempEndtime


# use two ways to parse time string: dparser and parsedatetime
def parsetime(timeString):
	try:
		returnTime = dparser.parse(timeString)
	except Exception as e:
		print e
		print "parser doesn't work, using parsedatetime instead"
		cal = pdf.Calendar()
		returnTime, code = cal.parseDT(timeString)
		if code == 0:
			raise AttributeError("time parameter error")
	return returnTime

def isDateExist(time):
	cal = pdf.Calendar()
	time, code = cal.parseDT(time)
	if code == 2:
		return False
	elif code == 0:
		return False
	return True

def isDateExistInEndDay(time):
	try:
		currentTime = datetime.datetime.now()
		time = dparser.parse(time)
		timeDate = time.strftime('%Y-%m-%d')
		currentTimeDate = currentTime.strftime('%Y-%m-%d')
		return timeDate != currentTimeDate
	except Exception as e:
		print e
		return False

def modify_evtname(evtname):
	global evtnameModifiedList

	for evtnameModifiedItem in evtnameModifiedList:
		evtname = re.sub(evtnameModifiedItem, '', evtname)
	return evtname

def modify_evtdesc(evtdesc):
	global evtdescModifiedList

	for evtdescModifiedItem in evtdescModifiedList:
		evtdesc = re.sub(evtdescModifiedItem, '', evtdesc)
	return evtdesc

def modify_location(location):
	global locationModifiedList

	for locationModifiedItem in locationModifiedList:
		location = re.sub(locationModifiedItem, '', location)

	location = re.sub(r'\s+', ' ', location)
	location = location.encode("ascii","ignore")
	return location


def fetch_data(url, evtname, evtdesc, starttime, endtime, location, community, evtsource, formerDate, tags, additionalTags, picurl, year):
	identity = str(evtname) + str(evtsource) + str(starttime)
	if not check_identity(identity):
		evtname = modify_evtname(evtname)
		evtdesc = modify_evtdesc(evtdesc)
		location = modify_location(location)
		evtname = titlecase(evtname)

		feed_item(url, evtname, evtdesc, starttime, endtime, location, community, evtsource, formerDate, tags, additionalTags, picurl, year)
	else:
		print "Exist: ",
		print evtname

def check_identity(identity):
	isExist = False
	ele = {"JS_Identity":identity}
	for flag in urlFilter.find(ele):
		isExist = True
	return isExist

def getLowercase(field):
	if isinstance(field, str):
		newField = field.lower()
	elif isinstance(field, unicode):
		newField = field.encode('ascii', 'ignore').lower()
	elif isinstance(field, list):
		newField = []
		for item in field:
			item = getLowercase(item)
			newField.append(item)
	elif isinstance(field, dict):
		newField = {}
		for key, value in field.iteritems():
			newField[key.lower()] = getLowercase(value)
	else:
		newField = field
	return newField

def feed_item(url, evtname, evtdesc, starttime, endtime, location, community, evtsource, formerDate, tags, additionalTags, picurl, year):

	item = {}
	item["url"] = url
	item["grps"] = []
	item["evtname"] = evtname
	item["evtdesc"] = evtdesc
	item["createdate"] = formerDate

	item["starttime"] = starttime
	item["endtime"] = endtime
	item["location"] = location

	item["picurl"] = picurl
	item["weburl"] = []
	item["weburl"].append(url)

	item["status"] = False
	item["evttype"] = "public"
	item["featured"] = False

	item["attendees"] = []
	item["attendcount"] = 0

	item["attended"] = []
	item["attendedCount"] = 0

	item["admin"] = []
	item["keywords"] = []
	item["community"] = community
	item["other"] = {"tags":tags, "year":year}
	item["just_crawled"] = True
	item["evtsource"] = evtsource
	item["isAvailable"] = True
	
	timeFilter(item)


def timeFilter(item):
	global crawledItem
	global stopSign
	global unqualifiedStarttimeCount
	global unqualifiedEndtimeCount
	global unqualifiedFlag
	global timezoneName

	global cityCoordinateDict
	global localityDict

	currentTime = datetime.datetime.now()

	# add timezone information to current time
	endTime = currentTime + datetime.timedelta(weeks=8)

	tempStarttime = item["starttime"]

	if item["starttime"] > endTime:
		#if there are 10 continuous events that starttime is later than our period, we will stop running our spider
		if unqualifiedFlag != 1:
			unqualifiedStarttimeCount = 0
			unqualifiedFlag = 1
		else:
			unqualifiedStarttimeCount += 1
		if unqualifiedStarttimeCount == 10:
			print "Ten continuous events that starttime is later than our period endtime, stop running spider"
			stopSign = True

		print "Drop Item: starttime is not qualified"
		return 0
	elif item["endtime"] < currentTime:
		#if there are 40 continuous events that endtime is earlier than current time, we will stop running our spider
		if unqualifiedFlag != 2:
			unqualifiedEndtimeCount = 0
			unqualifiedFlag = 2
		else:
			unqualifiedEndtimeCount += 1
		if unqualifiedEndtimeCount == 40:
			print "Forty continuous events that endtime is earlier than our period endtime, stop running spider"
			stopSign = True

		print "Drop Item: endtime is not qualified"
		feed_identity(item, tempStarttime)
		return 0
	else:
		unqualifiedFlag = 3

		if selfDefFilter(item):
			print "Insert!"
			crawledItem += 1
			if insertEventData(events, item, cityCoordinateDict, localityDict, timezoneName):
				feed_identity(item, tempStarttime)
		else:
			print "Filtered by selfDefFilter!! Event doesn't insert into MongoDB"
			feed_identity(item, tempStarttime)
		#raw_input(item["url"])

def feed_identity(item, tempStarttime):
	identity = str(item["evtname"]) + str(item["evtsource"]) + str(tempStarttime)
	insert_identity(identity)
	pass

def insert_identity(identity):
	ele = {"JS_Identity":identity}
	insertFilter(urlFilter, ele)

def printException():
	exc_type, exc_obj, tb = sys.exc_info()
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)
	print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

def selfDefFilter(item):
	return True

if __name__ == '__main__':
	main()


