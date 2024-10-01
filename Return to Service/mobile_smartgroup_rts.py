#!/usr/bin/env python3

import base64
import json
import requests
import sys
import time
import logging

"""
      Copyright (c) 2024 Jamf.  All rights reserved.

      Redistribution and use in source and binary forms, with or without
      modification, are permitted provided that the following conditions are met:
              * Redistributions of source code must retain the above copyright
                notice, this list of conditions and the following disclaimer.
              * Redistributions in binary form must reproduce the above copyright
                notice, this list of conditions and the following disclaimer in the
                documentation and#or other materials provided with the distribution.
              * Neither the name of the Jamf nor the names of its contributors may be
                used to endorse or promote products derived from this software without
                specific prior written permission.

      THIS SOFTWARE IS PROVIDED BY JAMF SOFTWARE, LLC "AS IS" AND ANY
      EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
      WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
      DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE, LLC BE LIABLE FOR ANY
      DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
      (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
      LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
      ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
      (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
      SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   mobile_smartgroup_rts.py # mobile device smart group return to service
#
#   The purpose of this script is to provide Return to Service (RtS) functionality to mobile devices using webhooks.
#   The script should be linked to a SmartGroupMobileDeviceMembershipChange webhook event in JAWA. When devices enter
#   this Smart Group, the script will gather the device's management ID and queue up a Return to Service command using
#   the wifi payload provided in the static_variables() method.
#
#   Please note:  the PayloadIdentifier key of the wifi payload must not match your an existing config profile's wifi
#   payload.  This makes sure that the WiFi profile is not removed by Jamf Pro and remains on the device throughout
#   the enrollment process.  You can get the payload using the Classic API, link below:
#   https://developer.jamf.com/jamf-pro/reference/findmobiledeviceconfigurationprofilesbyid
#
#   Requirements:
#       • requests (python3 -m pip install requests)
#       • JAWA server
#       • A positive attitude (highly recommended)
#
#   Please also note:
#       • Keep calm and code on
#       • May the force be with your scripts
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Define token cache globally
token_cache = {"access_token": None, "expires_in": 0, "timestamp": 0}

class Config:
    def __init__(self):
        self.jamf_url = "https://example.jamfcloud.com"
        self.token_url = f"{self.jamf_url}/api/oauth/token"
        self.client_id = "your_client_id"
        self.client_secret = "your_client_secret"
        self.scope = "your_scope"

def static_variables():
    """
    Returns static variables for Jamf Pro authentication and configuration.

    Returns:
        tuple: A tuple containing the following static variables:
            - wifi_payload (bytes): The payload UUID for WiFi configuration.
            - ea_name (str): The name of the EA used for the smart group event.
    """
    wifi_payload = b''  # make sure the payload UUID is different than what is in Jamf
    ea_name = "Enrolled (RtS)"  # Name should match the EA that is used for the smart group event
    return wifi_payload, ea_name

def get_oauth_token():
    global token_cache
    current_time = time.time()
    config = Config()

    if token_cache["access_token"] and (current_time - token_cache["timestamp"]) < token_cache["expires_in"]:
        return token_cache["access_token"]

    response = requests.post(
        config.token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": config.client_id,
            "grant_type": "client_credentials",
            "client_secret": config.client_secret,
            "scope": config.scope,
        },
    )

    response_data = response.json()
    token_cache = {
        "access_token": response_data["access_token"],
        "expires_in": response_data["expires_in"],
        "timestamp": current_time,
    }

    return token_cache["access_token"]

def get_headers(content_type="json"):
    token = get_oauth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json" if content_type == "json" else "application/xml",
    }
    return headers

def main():
    """
    Executes the main workflow for providing Return to Service (RtS) functionality to mobile devices using webhooks.

    This function orchestrates the process by obtaining authentication, retrieving device IDs, setting Extension Attributes, and triggering Return to Service commands.
    """
    config = Config()
    wifi_payload, ea_name = static_variables()
    id_list = get_list_of_ids()
    turnstile(id_list)  # verifies that there are devices that ENTERED the group. If not, the script exits.
    payload = base64.b64encode(wifi_payload).decode('ascii')
    set_ea_and_rts(id_list, config.jamf_url, payload, ea_name)

def set_ea_and_rts(id_list, jamf_url, payload, ea_name):
    for jss_id in id_list:
        print(jss_id)
        data = build_xml(ea_name, "Enrolled")
        change_ea_of_device(data, jss_id, jamf_url)
        mgmt_id = get_mgid_from_jssid(jamf_url, jss_id)
        if return_to_service(jamf_url, mgmt_id, payload):
            print("success!")

def change_ea_of_device(data, device_id, jps_url):
    full_url = f"{jps_url}/JSSResource/mobiledevices/id/{device_id}"
    headers = get_headers("xml")
    response = requests.put(full_url, headers=headers, data=data)
    print(response)  # Display HTTP status code

def build_xml(ea_name, value):
    return f"<mobile_device><extension_attributes><extension_attribute><name>{ea_name}</name><value>{value}</value></extension_attribute></extension_attributes></mobile_device>"

def turnstile(id_list):
    if not id_list:
        print("No devices entered the group, exiting...")
        exit(12)

def get_list_of_ids():
    event_data = json.loads(sys.argv[1])
    print(event_data)
    id_list = event_data['event']['groupAddedDevicesIds']
    return id_list

def get_mgid_from_jssid(jamf_url, jss_id):
    headers = get_headers()
    resp = requests.get(f"{jamf_url}/api/v2/mobile-devices/{jss_id}", headers=headers)
    resp_json = resp.json()
    mgmt_id = resp_json.get('managementId')
    print(mgmt_id)
    return mgmt_id

def return_to_service(jamf_url, management_id, payload):
    erase_device_json = {
        "clientData": [
            {
                "managementId": management_id
            }
        ],
        "commandData": {
            "commandType": "ERASE_DEVICE",
            "preserveDataPlan": True,
            "disallowProximitySetup": False,
            "returnToService": {
                "enabled": True,
                "wifiProfileData": f"{payload}"
            }
        }
    }
    try:
        headers = get_headers()
        resp = requests.post(f"{jamf_url}/api/preview/mdm/commands", json=erase_device_json, headers=headers)
        resp.raise_for_status()
        print(resp.text)
    except Exception as err:
        print(err)
        return False
    return True

if __name__ == '__main__':
    main()