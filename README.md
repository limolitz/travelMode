# travelMode
Travel mode checks your currently used wifi to disable traffic-heavy applications on metered connections. All tethered connections are assumed to be metered.

## Currently supported applications
* `dropbox`
* `syncthing`

## Currently supported network types
* Wifi (determined to be mobile after a list of network names inside `travelMode.py`)
* Tethered iPhones (determined after network driver as shown by `ethtool`)
* Tethered Android phones (determined after network driver as shown by `ethtool`)

## Planned
* Any other applications you need?

# Installation
* Adjust the path inside `cron.sh` to your current project directory
* Copy the `cron.sh` to the location `/etc/NetworkManager/dispatcher.d/90travelMode`
** (Don't symlink unless the project is owned by root, as the NetworkManager won't launch scripts which are not owned by root)
* Adjust the network list inside `travelMode.py` which are assumed to be mobile
