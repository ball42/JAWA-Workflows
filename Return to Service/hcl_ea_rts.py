#!/usr/bin/env python3

import base64
import json
import logging
import requests
import sys
import time
from xml.etree.ElementTree import Element, tostring

##########################################################################################
##
##      Copyright (c) 2024 Jamf.  All rights reserved.
##
##      Redistribution and use in source and binary forms, with or without
##      modification, are permitted provided that the following conditions are met:
##              * Redistributions of source code must retain the above copyright
##                notice, this list of conditions and the following disclaimer.
##              * Redistributions in binary form must reproduce the above copyright
##                notice, this list of conditions and the following disclaimer in the
##                documentation and#or other materials provided with the distribution.
##              * Neither the name of the Jamf nor the names of its contributors may be
##                used to endorse or promote products derived from this software without
##                specific prior written permission.
##
##      THIS SOFTWARE IS PROVIDED BY JAMF SOFTWARE, LLC "AS IS" AND ANY
##      EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
##      WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
##      DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE, LLC BE LIABLE FOR ANY
##      DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
##      (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
##      LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##      ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
##      (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
##      SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
##########################################################################################
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   hcl_ea_rts.py # mobile device smart group return to service
#
#   The purpose of this script is to  provide Return to Service (RtS) functionality to mobile devices using webhooks.
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
#       • flyin' shoes (optional)
#
#   Please also note:
#       • be excellent to each other
#       • party on, dudes & dudettes
#
# # # # # # # # # # # # # # # # # # # # #


# Define token cache globally
token_cache = {"access_token": None, "expires_in": 0, "timestamp": 0}


class Config:
    def __init__(self, api_url="JSSResource"):
        server_url = "https://example.jamfcloud.com"
        self.token_url = f"{server_url}/api/oauth/token"
        self.api_url = f"{server_url}{api_url}"  #
        self.client_id = ""  # jamf pro api client id
        self.client_secret = ""  # jamf pro api client secret
        self.scope = ""  # jamf pro api client scope (role)


def static_variables():
    """
    Returns the static variables needed for the procedure.

    :return: A tuple containing the Wi-Fi payload as bytes and the extension attribute name as a string.
    """
    wifi_payload = b"<XML version of your wifi profile goes here!>"
    ea_name = (
        "RtS Status"  # Name should match the EA that is used for the smart group event
    )
    return wifi_payload, ea_name


def main():
    """
    Main function serving as the entry point for the script.

    This function initializes the necessary variables,
    retrieves a list of IDs, verifies entry through a turnstile mechanism,
    encodes the payload in base64 format, and sets the required
    attributes and real-time status for the IDs.

    :return: None
    """
    payload, ea_name = static_variables()

    id_list = get_list_of_ids()
    turnstile(
        id_list
    )  # verifies that there are devices that ENTERED the group. If not, the script exits.
    payload = base64.b64encode(payload).decode("ascii")
    set_ea_and_rts(id_list, payload, ea_name)


def get_oauth_token():
    global token_cache
    current_time = time.time()
    config = Config()

    # Check if the token is still valid
    if (
        token_cache["access_token"]
        and (current_time - token_cache["timestamp"]) < token_cache["expires_in"]
    ):
        return token_cache["access_token"]

        # Request a new token
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
    logging.info(response_data)
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
        "Content-Type": (
            "application/json" if content_type == "json" else "application/xml"
        ),
    }
    return headers


def convert_dict_to_xml(data):
    elem = Element("root")
    for key, val in data.items():
        child = Element(key)
        child.text = str(val)
        elem.append(child)
    return tostring(elem)


def perform_api_call(
    endpoint, method="GET", data=None, api_url=None, content_type="json"
):
    config = Config(api_url)
    headers = get_headers(content_type)
    url = f"{config.api_url}/{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method in ["POST", "PUT"]:
            if content_type == "json":
                headers["Content-Type"] = "application/json"
                response = requests.request(method, url, headers=headers, json=data)
            elif content_type == "xml":
                headers["Content-Type"] = "application/xml"
                response = requests.request(method, url, headers=headers, data=data)
            else:
                raise ValueError("Unsupported content type")
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        response_content_type = response.headers.get("Content-Type", "")
        if "application/json" in response_content_type:
            return response.json()
        elif (
            "application/xml" in response_content_type
            or "text/xml" in response_content_type
        ):
            return (
                response.text
            )  # Return the XML as a string, or use an XML parser if needed
        elif "text/plain" in response_content_type:
            try:
                return response.json()
            except ValueError:
                logging.warning("Failed to parse response as JSON")
                return response.text
        else:
            return response.text  # For other content types, return the raw text

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None


def set_ea_and_rts(id_list, payload, ea_name):
    """
    :param id_list: List of device IDs to be processed.
    :param payload: Payload data required for returning devices to service.
    :param ea_name: Name of the extension attribute to be set.
    :return: None
    """
    for jss_id in id_list:
        data = build_xml(ea_name, "Enrolled")
        change_ea_of_device(data, jss_id)
        mgmt_id = get_mgid_from_jssid(jss_id)
        if return_to_service(mgmt_id, payload):
            logging.info(
                f"Great success! Device id {jss_id} has been returned to service."
            )


def change_ea_of_device(data, device_id):
    """
    :param data: The data to be updated for the device. Should be in a format compatible with the API.
    :param device_id: The unique identifier of the device that needs to be updated.
    :return: The response from the API call indicating success or failure of the operation.
    """
    endpoint = f"mobiledevices/id/{device_id}"
    method = "PUT"
    resp = perform_api_call(
        endpoint, method, data, api_url="JSSResource", content_type="xml"
    )


def build_xml(ea_name, value):
    """
    :param ea_name: The name for the extension attribute to include in the XML.
    :param value: The value corresponding to the extension attribute name.
    :return: A string representing the XML snippet containing the extension attribute with its value.
    """
    return (f"<mobile_device>"
                f"<extension_attributes>"
                    f"<extension_attribute>"
                        f"<name>{ea_name}</name>"
                        f"<value>{value}</value"
                    f"></extension_attribute>"
                f"</extension_attributes>"
            f"</mobile_device>")


def turnstile(id_list):
    """
    :param id_list: A list containing IDs of the devices that entered the group.
    :return: None. Prints a message if the id_list is empty and exits the program with status code 12.
    """
    if not id_list:
        logging.info("No devices entered the group, exiting...")
        exit(12)


def get_list_of_ids():
    """
    :return: A list of IDs extracted from the webhook event data provided
    """
    event_data = json.loads(sys.argv[1])  # i.e., for JAWA
    id_list = event_data["event"]["groupAddedDevicesIds"]
    return id_list


def get_mgid_from_jssid(jss_id):
    """
    :param jss_id: The ID of the mobile device in the Jamf Pro Server.
    :return: The management ID of the mobile device.
    """
    endpoint = f"mobile-devices/{jss_id}"
    method = "GET"
    resp = perform_api_call(endpoint, method, api_url="api/v2", content_type="json")
    mgmt_id = resp.get("managementId")
    return mgmt_id


def return_to_service(management_id, payload):
    """
    :param management_id: The unique identifier for the management system.
    :param payload: The data to be included in the `wifiProfileData` of the return to service command.
    :return: Returns True if the operation was successful, otherwise False.
    """
    erase_device_json = {
        "clientData": [{"managementId": management_id}],
        "commandData": {
            "commandType": "ERASE_DEVICE",
            "preserveDataPlan": True,
            "disallowProximitySetup": False,
            "returnToService": {"enabled": True, "wifiProfileData": f"{payload}"},
        },
    }
    try:
        resp = perform_api_call("mdm/commands", "POST",
                                data=erase_device_json, api_url="api/preview",content_type="json")
        resp.raise_for_status()
        logging.info(f"Successfully sent RtS command: {resp.status_code, resp.text}")
    except Exception as err:
        logging.error(f"Error sending RtS command: {err}")
        return False
    return True


if __name__ == "__main__":
    main()
