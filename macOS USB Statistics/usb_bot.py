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

from __future__ import annotations
import datetime
import json
import mongoengine
# import requests
# import sqlite3
import sys

# from typing import Dict, List

alias_core = 'core'


def init():
    db = 'protect'
    mongoengine.register_connection(alias=alias_core, name=db)


class USB_Inserted(mongoengine.Document):
    event_names = mongoengine.ListField(required=True)
    event_uuid = mongoengine.StringField(required=True)
    event_timestamp = mongoengine.DateTimeField(default=datetime.datetime.now)
    event_body = mongoengine.DictField()
    media_name = mongoengine.StringField()
    encryption_status = mongoengine.BooleanField()
    host_name = mongoengine.StringField()
    host_serial = mongoengine.StringField()
    host = mongoengine.DictField()
    device_vendor = mongoengine.StringField()
    device_model = mongoengine.StringField()
    device_serial = mongoengine.StringField()

    meta = {
        'db_alias': 'core',
        'collection': 'usb_events',
        'indexes': [
            'event_names',
            'host_serial',
            'encryption_status'
        ]
    }


init()

webhook_content = sys.argv[1]  # catch the webhook
data = json.loads(webhook_content)
print(data)
event = USB_Inserted()

event_names = []
facts = data['input']['match']['facts']
for each_fact in facts:
    print(each_fact.get('name'))
    event_names.append(each_fact.get('name'))

if 'USBInserted' not in event_names:
    print('Not a USB inserted event')
    exit(2)

event_type = data['input']['eventType']
host: dict[str, str | list[str]] = data['input']['host']
media_name = data['input']['match']['event']['device']['mediaName']
encryption_status = data['input']['match']['event']['device']['isEncrypted']
timestamp = data['input']['match']['event']['timestamp']
event_uuid = data['input']['match']['event']['uuid']
device_vendor = data['input']['match']['event']['device'].get('vendorName')
device_model = data['input']['match']['event']['device'].get('deviceModel')
device_serial = data['input']['match']['event']['device'].get('serialNumber')

print(media_name)
print(host)

event.event_names = event_names
event.event_uuid = event_uuid
event.event_timestamp = datetime.datetime.fromtimestamp(timestamp)
event.encryption_status = encryption_status
event.media_name = media_name
event.event_body = data
event.host_name = host.get('hostname')
event.host_serial = host.get('serial')
event.host = host
event.device_vendor = device_vendor
event.device_model = device_model
event.device_serial = device_serial
event.save()
