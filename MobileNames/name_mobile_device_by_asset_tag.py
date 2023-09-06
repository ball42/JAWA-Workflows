#!/usr/bin/python3

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#       THIS SCRIPT IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
#       BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#       PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE, LLC BE LIABLE
#       FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#       (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#       ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#       SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#   PURPOSE
#   This script is intended to be used with the Jamf Automation and Webhook Assistant (JAWA).
#   It performs the following:
#   1.  Catches a MobileDeviceEnrolled event
#   2. Parses enrolling device information
#   3. Performs a call to Jamf Pro using the Classic API to get the asset tag of the device
#   4. Uses the Classic API to rename the device to the asset tag
#
#
# INSTRUCTIONS
#   1. Fill out the variables in the config() method
#   2. Log into JAWA
#   3. Navigate to Webhooks > Jamf Pro and create a new webhook
#   5. Choose "MobileDeviceEnrolled" as the Jamf Pro event
#   6. Upload your copy of this script
#   7. Make sure your device names are seeded in the Asset Tag field using Jamf's Inventory Preload
#   8. Enroll a mobile device and verify that the name is automatically changed
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import json
import requests
import sys
import time

#  Edit the config() method's variables, add your Jamf Pro information
def config():
    jps_username = ""  # Least-privileged access = READ Mobile Devices and Send Mobile Device Name command
    jps_password = "" # secrets go here.  Consider pulling these values from environment variables instead
    jps_url = "https://example.jamfcloud.com"  # include port, no trailing slash (/) please!
    return jps_username, jps_password, jps_url

#  Don't edit below this point unless you know what you're doing
def main():
    jps_username, jps_password, jps_url = config()
    event_data = webhook_handler()
    old_name, jamf_time, jps_id, room, serial_number = get_event_info(event_data)
    if room:
        print(f"This device has an assigned room ({room}) - this is a bedside device.  Exiting through door 5.")
        exit(5)
    new_name = get_asset_tag(jps_url, jps_username, jps_password, jps_id)
    set_name(jps_id, jps_password, jps_url, jps_username, new_name)
    print(f"Device with SN {serial_number} was enrolled at {jamf_time} and renamed from {old_name} to {new_name} ")


def set_name(jps_id, jss_password, jss_url, jss_username, new_name):
    if new_name:
        endpoint_uri = f"/JSSResource/mobiledevicecommands/command/DeviceName/{new_name}/id/{jps_id}"
        resp = requests.post(f"{jss_url}{endpoint_uri}",
                             auth=(jss_username, jss_password))
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"Could not rename the device (ID {jps_id}")
            print(err)
            exit(4)


def get_event_info(event_data):
    jps_id = str(event_data['event']['jssID'])  # finding ID from enrollment event
    ts = event_data['webhook']['eventTimestamp']
    device_name = event_data['event']['deviceName']
    serial_number = event_data['event']['serialNumber']
    room = event_data['event']['room']
    jamf_time = convert_time(ts)
    return device_name, jamf_time, jps_id, room, serial_number


def convert_time(ts):
    ts = ts / 1000.0
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))


def webhook_handler():
    webhook_content = sys.argv[1]
    webhook_content = json.dumps(webhook_content)
    try:
        webhook_json = json.loads(webhook_content)
    except Exception as err:
        print(f"Error {err} - couldn't load event JSON for processing, exiting.")
        exit(1)
    return webhook_json


def get_asset_tag(jps_url, jps_username, jps_password, jps_id):
    resp = requests.get(f"{jps_url}/JSSResource/mobiledevices/id/{jps_id}", auth=(jps_username, jps_password),
                        headers={"Accept": "application/json"})
    try:
        resp.raise_for_status()
        device_record = resp.json()
        asset_tag = device_record['mobile_device']['general'].get('asset_tag')
        if not asset_tag:
            print(f'No asset tag detected for ID{jps_id}.  Exiting without renaming.')
            exit(3)
    except Exception as err:
        print(f"Could not GET device record with ID {jps_id}, error: {err}")
        exit(2)
    return asset_tag


if __name__ == '__main__':
    main()
