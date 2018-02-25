#!/usr/bin/python3

import os
import subprocess
import urllib.request, urllib.error, urllib.parse, urllib.request, urllib.parse, urllib.error, http.cookiejar
import configparser
import ssl
import json

ignoreAdaptors = ["lo", "docker0"]
mobileWifiNetworks = ["WIFIonICE"]
#mobileWifiNetworks = [""]

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
	return nmcliInfo

def sendNotification(message):
	messageProcess = subprocess.Popen(['notify-send', "Travel Mode", message], env=dict(os.environ, LANG="LC_ALL"))
	return

def checkIfDropboxIsRunning():
	dropboxCli1 = subprocess.Popen(["/usr/bin/dropbox", "running"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
	dropboxRunning, errors = dropboxCli1.communicate()
	return dropboxCli1.returncode == 1

def checkIfSyncthingIsRunning():
	syncthingCheck = subprocess.Popen(["pidof", "syncthing"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
	syncthingOutput, errors = syncthingCheck.communicate()
	if len(syncthingOutput) > 0:
		return True
	else:
		return False

def handleWifi(adaptor,network):
	#print("Handle wifi network on {}.".format(adaptor))
	# check if there is a wifi network connected
	if network['GENERAL.STATE'] == "100 (connected)":
		networkName = network['GENERAL.CONNECTION']
		print("Network {} is connected.".format(networkName))
		if networkName in mobileWifiNetworks:
			print("Computer is connected to a mobile wifi network.")
			handleMobileWifi()
		else:
			print("Computer is connected to stationay wifi network {}.".format(networkName))
			handleStationaryWifi()

def handleMobileWifi():
	# stop dropbox
	if checkIfDropboxIsRunning():
		print("dropbox is running. Stopping.")
		dropboxCli1 = subprocess.Popen(["/usr/bin/dropbox", "stop"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
		dropboxStopped, errors = dropboxCli1.communicate()
		output = dropboxStopped.decode("utf-8")
		print("Dropbox stopped: {}".format(output))
		sendNotification(output)
	else:
		print("dropbox is not running.")

	# stop syncthing
	if checkIfSyncthingIsRunning():
		print("Stopping syncthing")
		config = configparser.ConfigParser()
		config.read('config.ini')
		syncthingPort = config.get("syncthing", "port")
		syncthingApiKey = config.get("syncthing", "apikey")
		url = "https://localhost:{}/rest/system/shutdown".format(syncthingPort)

		# disable cert checking on local connection
		ctx = ssl.create_default_context()
		ctx.check_hostname = False
		ctx.verify_mode = ssl.CERT_NONE

		try:
			request = urllib.request.Request(url, data=b"", headers={"X-API-KEY": syncthingApiKey})
			page = urllib.request.urlopen(request,context=ctx).read()
			response = page.decode("utf-8")
			parsedJson = json.loads(response)

			if "ok" in parsedJson.keys():
				output = "Syncthing message: {}".format(parsedJson['ok'])
				sendNotification(output)
			else:
				print("Unexpected message: {}".format(parsedJson))
		except urllib.error.URLError as e:
			print("Error: Syncthing not reachable. Probably not running.")
		except Exception as e:
			print(type(e),e)
	else:
		print("Syncthing not running.")

def handleStationaryWifi():
	# check if dropbox is running
	if not(checkIfDropboxIsRunning()):
		# start dropbox
		print("Starting dropbox")
		dropboxCli1 = subprocess.Popen(["dbus-launch", "dropbox", "start"], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
		dropboxRunning, errors = dropboxCli1.communicate()
		print(dropboxRunning)
		if errors is not None and len(errors) > 0:
			print("Errors: {}".format(errors.decode("utf-8")))
		else:
			sendNotification("Dropbox started.")
	else:
		print("Dropbox already running.")
	# start syncthing
	if not(checkIfSyncthingIsRunning()):
		print("Starting syncthing")
		syncthingLaunch = subprocess.Popen(["/home/florin/bin/syncthing.sh"], close_fds=True, env=dict(os.environ, LANG="LC_ALL"))
		sendNotification("Syncthing started.")
	else:
		print("Syncthing already running.")

def getCurrentNetwork():
	# get all connected adaptors
	adaptors = os.listdir('/sys/class/net/')
	#print(adaptors)
	for adaptor in adaptors:
		if adaptor in ignoreAdaptors:
			continue
		#print("Handling adaptor {}".format(adaptor))
		networkInfo = getNetworkManagerInfo(adaptor)
		#print(networkInfo)
		# look for wireless network (wifi)
		# TODO: also check for tethered USB connection
		if networkInfo['GENERAL.TYPE'] == "wifi":
			#print("Wifi network found: {}.".format(adaptor))
			handleWifi(adaptor,networkInfo)
		elif networkInfo['GENERAL.TYPE'] == "ethernet":
			# ethernet connection, might still be tethered USB, probably metered as well
			# get driver via ethtool
			ethtool = subprocess.Popen(["ethtool", "-i", adaptor], stdout=subprocess.PIPE, env=dict(os.environ, LANG="LC_ALL"))
			ethtoolOutput, errors = ethtool.communicate()
			ethInfo = {}
			for line in ethtoolOutput.decode("utf-8").rstrip().split("\n"):
				lineContent = line.split(":", 1)
				identifier = lineContent[0].strip()
				value = lineContent[1].strip()
				#print(identifier,value)
				ethInfo[identifier] = value
			#print(ethInfo)
			if "driver" in ethInfo.keys():
				if ethInfo["driver"] == "ipheth":
					print("iPhone network. Assuming as metered.")
					sendNotification("Tethered to an iPhone.")
					handleMobileWifi()
				elif ethInfo["driver"] == "e1000e":
					# normal ethernet connection, ignoring
					True
				else:
					print("Unknown driver {} on adaptor {}.".format(ethInfo["driver"],adaptor))
					sendNotification("Unknown driver {} on adaptor {}.".format(ethInfo["driver"],adaptor))
if __name__ == '__main__':
	getCurrentNetwork()