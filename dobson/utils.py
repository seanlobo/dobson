import configparser
import json
import os
import subprocess
from collections import namedtuple


Device = namedtuple('Device', ['presence', 'user', 'model'])

config = configparser.ConfigParser()
config.read('dobson/config.ini')


SLACK_API_TOKEN = config['dobson']['SlackApiToken']

# Only allow querying for presence in certain channels
ALLOWED_CHANNEL_IDS = config['dobson']['AllowedChannelIds'].split('\n')

# The user ID of the dobson bot
DOBSON_SLACK_ID = config['dobson']['DobsonSlackId']

# file to log current MAC Addresses in
MAC_LOG_FILE = config['dobson']['MacAddressLogFile']

# create KNOWN_DEVICES, which maps mac addresses (str) to Device instances
KNOWN_DEVICES = {}
if os.path.isfile(config['dobson']['KnownDevicesFile']):
    with open(config['dobson']['KnownDevicesFile'], 'r') as f:
        tmp_devices = json.loads(f.read())
    for key, val in tmp_devices.items():
        KNOWN_DEVICES[key.lower()] = Device(**val)
else:
    print("Missing `{}` with device information. If you want to proceed without data, make the file with {} in it".
          format(config['dobson']['KnownDevicesFile']))
    exit(1)


def get_devices():
    """Get all recognized connected devices"""
    for mac_addr in get_mac_addresses():
        if mac_addr in KNOWN_DEVICES:
            found_device = KNOWN_DEVICES[mac_addr]

            if found_device.presence:
                yield found_device


def get_mac_addresses():
    """
    Get a list of MAC addresses connected to the router

    TODO: Make this method less specific to this model of router (TP-Link Archer C50)
    """
    output = subprocess.check_output(
        ('/usr/bin/snmpwalk', '-v1', '-c', 'public', '192.168.0.1', 'iso.3.6.1.2.1.3.1.1.2.12.1'),
    )
    devices = output.decode('utf-8').rstrip().split('\n')

    for device in devices:
        # The output from SNMP looks like this, so we parse it for the IP and MAC address:
        # iso.3.6.1.2.1.3.1.1.2.12.1.192.168.0.100 = Hex-STRING: 74 4A A4 CC 81 A1

        mac_addr = device[-18:].strip(' ').lower().replace(' ', ':')
        yield mac_addr
