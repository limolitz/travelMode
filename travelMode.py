#!/usr/bin/python3

import os
import subprocess
import urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error, http.cookiejar
import configparser
import ssl
import json

ignoreAdaptors = ["lo", "docker0"]
mobileWifiNetworks = ["WIFIonICE"]

def getNetworkManagerInfo(device=""):
	nmcli = subprocess.Popen(["/usr/bin/nmcli", "-t", "dev", "show", device], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
	nmcliRawInfo, errors = nmcli.communicate()
	nmcliInfo = {}
	if len(errors) > 0:
		print("Errors: {}".format(errors.decode("utf-8")))
	for line in nmcliRawInfo.decode("utf-8").rstrip().split("\n"):
		lineContent = line.split(":", 1)
		#print(lineContent)
		if len(lineContent) > 2:
			print("More than one info cell in line {}.".format(lineContent))
			input()
			continue
		if len(lineContent) == 2:
			nmcliInfo[lineContent[0]] = lineContent[1]
		else:
			print("Empty line {}. Setting to None.".format(lineContent[0]))
			nmcliRawInfo[lineContent[0]] = None
		#print("{}\n\n".format(line))
	#print(nmcliInfo)
	return nmcliInfo

def sendNotification(message):
	messageProcess = subprocess.Popen(['notify-send', "Travel Mode", message], env=dict(os.environ, LANG="LC_ALL"))
	return

def handleWifi(adaptor,network):
	#print("Handle wifi network on {}.".format(adaptor))
	# check if there is a wifi network connected
	if network['GENERAL.STATE'] == "100 (connected)":
		networkName = network['GENERAL.CONNECTION']
		print("Network {} is connected.".format(networkName))
		if networkName in mobileWifiNetworks:
			print("Computer is connected to a mobile wifi network.")
			handleMobileWifi(adaptor,network)
		else:
			print("Computer is connected to stationay wifi network {}.".format(networkName))
			handleStationaryWifi(adaptor,network)

def handleMobileWifi(adaptor,network):
	# disable dropbox sync
	dropboxCli1 = subprocess.Popen(["/usr/bin/dropbox", "running"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
	dropboxRunning, errors = dropboxCli1.communicate()
	#print(dropboxRunning,errors)
	if dropboxCli1.returncode == 1:
		print("dropbox is running. Stopping.")
		dropboxCli1 = subprocess.Popen(["/usr/bin/dropbox", "stop"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
		dropboxStopped, errors = dropboxCli1.communicate()
		output = dropboxStopped.decode("utf-8")
		print("Dropbox stopped: {}".format(output))
		sendNotification(output)
	else:
		print("dropbox is not running.")

	# disable syncthing
	config = configparser.ConfigParser()
	config.read('config.ini')
	syncthingPort = config.get("syncthing", "port")
	syncthingApiKey = config.get("syncthing", "apikey")
	url = "https://localhost:{}/rest/system/shutdown".format(syncthingPort)

	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	try:
		request = urllib.request.Request(url, data=b"", headers={"X-API-KEY": syncthingApiKey})
		page = urllib.request.urlopen(request,context=ctx).read()
		response = page.decode("utf-8")
		parsedJson = json.loads(response)
		print(parsedJson)
		if "ok" in parsedJson.keys():
			output = "Syncthing message: {}".format(parsedJson['ok'])
			sendNotification(output)
	except urllib.error.URLError as e:
		print("Error: Syncthing not reachable. Probably not running.")
	except Exception as e:
		print(type(e),e)


def getCurrentNetwork():
	# get all connected adaptors
	adaptors = os.listdir('/sys/class/net/')
	#print(adaptors)
	for adaptor in adaptors:
		if adaptor in ignoreAdaptors:
			continue
		#print("Handling network {}".format(adaptor))
		networkInfo = getNetworkManagerInfo(adaptor)
		# look for wireless network (wifi)
		# TODO: also check for tethered USB connection
		if networkInfo['GENERAL.TYPE'] == "wifi":
			#print("Wifi network found: {}.".format(adaptor))
			handleWifi(adaptor,networkInfo)

if __name__ == '__main__':
	getCurrentNetwork()