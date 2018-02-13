#!/usr/bin/python3

import os
import subprocess

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

def handleWifi(adaptor,network):
	#print("Handle wifi network on {}.".format(adaptor))
	# check if there is a wifi network connected
	if network['GENERAL.STATE'] == "100 (connected)":
		networkName = network['GENERAL.CONNECTION']
		print("Network {} is connected.".format(networkName))
		if networkName in mobileWifiNetworks:
			print("Computer is connected to a mobile wifi network.")
			handleMobileWifi(adaptor,network)

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

	else:
		print("dropbox is not running.")

	# TODO: disable syncthing


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