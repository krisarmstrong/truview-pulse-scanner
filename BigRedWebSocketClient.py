#!/usr/bin/python
# -*- coding: utf-8 -*-

# Filename: BigRedWebSocketClient.py
# Revision: 2019-09-04
# Converting to Python 3
PROGRAM_VERSION = "2.10"
# 
# Show Usage: python BigRedWebSocketClient.py -help
#
# Notes: 
# - Tested on Python 2.7.3 for Linux. The modules below are required.
#     sudo pip install websocket-client
#     sudo pip install netaddr
# - Tutorial on module "netaddr"...
#   https://pythonhosted.org/netaddr/tutorial_01.html
# - For Linux VM on Windows, enable these "Network connection" settings...
#     Bridged: Connected directly to the physical network
#     Replicate physical network connection state.

import sys
import websocket
import hashlib
from netaddr import *

# Default option values...

macFilter = ""
transLangSelected = "EN"

# Default IP network...
#strNetworkIp = "192.168.1.0/24" # Private Network - scans 255 addresses
#strNetworkIp = "10.250.0.0/23" # Fluke Test Lab - scans 512 addresses
strNetworkIp = "129.196.196.0/23" # Fluke Colorado PRODUCTION network

# Default timeout...
# timeoutSecs=0.20 takes about 50 seconds to scan 255 addresses
# timeoutSecs=0.10 takes about 25 seconds to scan 255 addresses
# timeoutSecs=0.06 usually works and is fast, but sometimes has timeout error
timeoutSecs = 0.10

# Display information level: 
# 0= [ IP Address, MAC Address, Build ]
# 1= add [ CPU Temp (degC), Link, Uptime ]
# 2= add [ Batt, PoE, Gemini URL, Machine Name ]
# 3= add [ Nearest Switch Port Info ]
# 4= add [ Memory Info (total/free/available) ]
# 9= Display all info fields
displayInfoLevel = 0

print("PROGRAM_VERSION=  %s" % PROGRAM_VERSION)
numArgs = len(sys.argv)
#print "DEBUG> num args: %s" % numArgs

"""
if numArgs > 2:
  params = sys.argv[2]
"""

# parse command-line options...
k = -1
for strArg in sys.argv:
	k = k + 1
	#print "DEBUG> Arg= %s" % sys.argv[k]
	#
	# Help on available options...
	if sys.argv[k][:2] == "-h": 
		print("Command Line Options...")
		print("-i<CidrNetworkIp>  e.g. 10.250.0.0/23, default=192.168.1.0")
		print("-m<MacAddress>     e.g. 330030 or 00c017330030, default=none")
		print("-d<DisplayLevel>   e.g. 0-9, default=0 (IP/MAC/Uptime/Build)")
		print("-t<TimeoutSeconds> e.g. 0.20, default=0.10 (25sec for 255 IPs)")
		print("-l<LanguageCode>   e.g. EN=English ES=Spanish, default=EN")
		sys.exit(1)
	#
	# MAC suffix filter option (last 6 hex characters)
	if sys.argv[k][:2] == "-m": 
		macFilter = sys.argv[k][2:]
		print("option: mac filter= %s" % macFilter)
	#
	# IP Network prefix option (last char must be '.')
	if sys.argv[k][:2] == "-i": 
		tmpIpPrefix = sys.argv[k][2:]
		#if tmpIpPrefix[-1] == '.':
		#	strNetworkIp = tmpIpPrefix
		#	print "option: network prefix= %s" % strNetworkIp
		#else:
		#	print "ERROR: invalid network prefix - last char is not '.'"
		#	sys.exit(1)
		slashPos = tmpIpPrefix.find("/")
		if slashPos < 0:
			print("WARNING: network IP missing a '/'"),
			#sys.exit(1)
			print("-- appending '/24'")
			strNetworkIp = tmpIpPrefix + "/24"
		else:
			strNetworkIp = tmpIpPrefix
		print("option: network ip (CIDR notation)= %s" % strNetworkIp)
	#
	# timeout milliseconds option
	if sys.argv[k][:2] == "-t": 
		strTimeout = sys.argv[k][2:]
		timeoutSecs = float(strTimeout)
		print("option: timeout (secs)= %f" % timeoutSecs)
	#
	# language option (current choices are "EN=English", "ES=Spanish")
	if sys.argv[k] == "-lEN": transLangSelected = "EN"
	if sys.argv[k] == "-lES": transLangSelected = "ES"
	#
	# display level option
	if sys.argv[k][:2] == "-d": 
		strDisplayLevel = sys.argv[k][2:]
		displayInfoLevel = int(strDisplayLevel)
		print("option: display info level= %d" % displayInfoLevel)


queryList = [ 
"gtme_web", 
#"uptime",  # this is broken -- shows system clock time instead
"bver", 
"temp", 
"link", 
"up_dhm", 
"batt",
"poev",
"gurl", 
"mach",
"sw_port", 
"sw_addr", 
"sw_name",
"free" ]

transListEN = [
"IP Address",
"MAC Address",
"Build Version",
"CPU Temp (degC)",
"Link Info",
"System UpTime",
"Voltage - Battery",
"Voltage - PoE",
"Gemini Cloud URL",
"Machine Hardware Name",
"Nearest Switch - Port",
"Nearest Switch - IP/MAC",
"Nearest Switch - Name",
"Memory Information..." ]

transListES = [
"Dirección IP",
"Dirección MAC",
"Información de la versión",
"CPU temperatura (degC)",
"Enlace información",
"El tiempo de actividad",
"Voltaje - Batería",
"Voltaje - PoE",
"Gemini Cloud URL",
"Máquina nombre de hardware",
"Conmutador de red - Identificador de puerto",
"Conmutador de red - Dirección (IP/MAC)",
"Conmutador de red - Nombre",
"Información de la memoria..." ]

params = "" # empty string
password = "" # emtpy string

numUnitsFound = 0
macFilterFound = 0

# loop over all IPs in subnet...
ip = IPNetwork(strNetworkIp)
ip_list = list(ip)
rangeBeg = 1
rangeEnd = len(ip_list)-1

print("")
print("Scan IP Network: %s" % strNetworkIp)
print("Scan Begin Addr: %s" % ip[rangeBeg])
print("Scan End Addr:   %s" % ip[rangeEnd-1]) # .254 instead of .255

#for i in range(1,255):
for i in range(rangeBeg, rangeEnd):
	#ipAddr = strNetworkIp + str(i)
	ipAddr = str(ip[i])
	#print "DEBUG> i=%d ipAddr=%s" % (i, ipAddr)
	serverUrl = "ws://" + ipAddr + ":8000"
	#print ""
	#print "DEBUG> serverUrl= %s" % serverUrl
	
	if len(macFilter) > 0:
		print("."),
		sys.stdout.flush()
	
	ws = websocket.WebSocket()
	ws.settimeout(timeoutSecs)
	
	#print "Connecting..."
	try:
		ws.connect(serverUrl)
		#print ""
		#print "DEBUG> serverUrl= %s" % serverUrl
		result = ws.recv()
		#print "DEBUG> Received '%s'" % result
	except Exception, e:
		#print "ERROR: connect failed"
		continue
	
	"""
	# We would normally show the IP Address here, but the printing is delayed 
    # until the handling of a macFilter is done for the first queryList item...
	numUnitsFound = numUnitsFound + 1
	if transLangSelected == "EN": print "%s= %s" % (transListEN[0], ipAddr)
	if transLangSelected == "ES": print "%s= %s" % (transListES[0], ipAddr)
	"""

	# extract and keep nonce to create signature hash for subsequent query...
	nonce = result.partition("nonce\": \"")[2].partition("\", \"uname")[0]
	#print "DEBUG> nonce= '%s'" % nonce
	
	listIndex = 0
	for strQuery in queryList:
		# determine display info level...
		if strQuery == "temp"    and displayInfoLevel < 1: break
		if strQuery == "batt"    and displayInfoLevel < 2: break
		if strQuery == "sw_port" and displayInfoLevel < 3: break
		if strQuery == "free"    and displayInfoLevel < 4: break

		listIndex = listIndex + 1
		#print
		#print "Query: %s" % strQuery,
		#print "%s= " % strQuery,

		instring = params + password + nonce
		#print "DEBUG> instring= '%s'" % instring
		
		instring2 = instring.replace("\u000b", "\v")
		#print "DEBUG> instring2= '%s'" % instring2
		
		instring3 = instring2.decode('string_escape')
		#print "DEBUG> instring3= '%s'" % instring3
		
		
		# Below is from function send_websock() in Gordon's file "test.html"...
		#   signature : CryptoJS.SHA1($('#params').val() + pass + nonce).toString(CryptoJS.enc.Hex)
		# hash calc below usually works, but fails if nonce contains '\u000b'...
		hash_object = hashlib.sha1(instring3)
		hex_dig = hash_object.hexdigest()
		#print(hex_dig)
		#print "DEBUG> sha1hash= '%s'" % hex_dig
		
		ws.send("{\"callType\":\""+strQuery+"\",\"parameter\":\"\",\"signature\":\""+hex_dig+"\"}")
		#print "DEBUG> Sent"
		#print "DEBUG> Receiving..."
		result = ws.recv()
		#print "DEBUG> Received '%s'" % result
		
		result2 = result
		strData = result2.partition("data\": \"")[2].partition("\", \"success")[0].replace("\\n", " ")
		#newStr = strData.replace("\n", ",")
		#print "Data: %s" % strData
		
		if listIndex == 1 and len(macFilter) > 0:
			# NOTE: units MACs may have hex digits in either lower or uppercase
			if strData.lower().find(macFilter) > -1 or strData.upper().find(macFilter) > -1:
				macFilterFound = 1
			else:
				break
		
		if listIndex == 1:
			numUnitsFound = numUnitsFound + 1
			print("")
			if transLangSelected == "EN": print("%s=  %s" % (transListEN[0], ipAddr))
			if transLangSelected == "ES": print("%s=  %s" % (transListES[0], ipAddr))
		
		if strQuery == "free":
			if transLangSelected == "EN": print("%s" % transListEN[listIndex])
			if transLangSelected == "ES": print("%s" % transListES[listIndex])
		else:
			if transLangSelected == "EN": print("%s= " % transListEN[listIndex],)
			if transLangSelected == "ES": print("%s= " % transListES[listIndex],)
		
		if strQuery == "batt" or strQuery == "poev":
			print("%s" % strData[5:])
		elif strQuery == "free":
			print("%s" % strData.replace(':','=').replace('kB ','kB\n').replace('kB','k'))
		else:
			print("%s" % strData)
		
		# extract and keep nonce to create signature hash for subsequent query...
		nonce = result.partition("nonce\": \"")[2].partition("\", \"data")[0]
		#print "DEBUG> nonce= '%s'" % nonce
	
	ws.close()
	if macFilterFound == 1: break

print("")
print("DONE")
if len(macFilter) == 0:
	print("Total BigRed units found= %d" % numUnitsFound)

sys.exit(0)
