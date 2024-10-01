# Jamf Pro Return to Service (RtS) Workflows

## Overview

This repository contains two Python scripts that automate the Return to Service (RtS) process for mobile devices managed by Jamf Pro. These scripts work in conjunction with the Jamf Automation and Webhook Assistant (JAWA) to trigger RtS actions based on specific criteria.

1. `hcl_ea_rts.py`: Utilizes a healthcare listener and an extension attribute.
2. `mobile_smartgroup_rts.py`: Uses a smart group trigger, suitable for any customer needing RtS functionality.

## Features

- Automatic RtS triggering based on Smart Group membership changes
- Extension Attribute updates to track RtS enrollment status
- Configurable WiFi payload for RtS process
- OAuth 2.0 token-based authentication for enhanced security
- Compatibility with both Jamf Pro Classic API and newer API endpoints

## Prerequisites

- Python 3.x
- `requests` library (`python3 -m pip install requests`)
- Jamf Pro instance
- JAWA server
- Jamf Pro API client credentials (for OAuth 2.0 authentication)

## Installation

1. Clone this repository or download the desired script:
   - `hcl_ea_rts.py` for healthcare-specific implementation
   - `mobile_smartgroup_rts.py` for general-purpose implementation
2. Install the required Python library:
   ```
   python3 -m pip install requests
   ```
3. Configure the chosen script (see Configuration section).
4. Set up the appropriate webhook in JAWA:
   - Configure a SmartGroupMobileDeviceMembershipChange webhook event pointing to the script

## Configuration

For both scripts, edit the `Config` class and `static_variables()` function:

```python
class Config:
def init(self):
self.jamf_url = "https://your-instance.jamfcloud.com"
self.token_url = f"{self.jamf_url}/api/oauth/token"
self.client_id = "your_client_id"
self.client_secret = "your_client_secret"
self.scope = "your_scope"
def static_variables():
wifi_payload = b'' # Your base64 encoded WiFi payload
ea_name = "Enrolled (RtS)" # Name of the Extension Attribute
return wifi_payload, ea_name
```

## Usage

Both scripts are designed to run automatically when triggered by JAWA based on Smart Group membership changes. They perform the following actions:

1. Authenticate with Jamf Pro using OAuth 2.0
2. Retrieve devices that entered the specified Smart Group
3. For each device:
   - Set the RtS-related Extension Attribute
   - Retrieve the device's management ID
   - Send an RtS command with the specified WiFi payload

## Key Differences

- `hcl_ea_rts.py` is tailored for healthcare environments and includes specific logic for healthcare-related triggers.
- `mobile_smartgroup_rts.py` is a more general-purpose script suitable for any environment requiring RtS functionality.

## Security Considerations

- The scripts use Jamf API Roles and Clients for enhanced security.
- Regularly rotate your API client credentials.
- Ensure proper security measures on the JAWA server and the machine running these scripts.

## Troubleshooting

If issues occur:
1. Verify Jamf Pro API client credentials and URL in the configuration.
2. Check JAWA webhook configuration.
3. Ensure the WiFi payload is correctly formatted and has a unique PayloadIdentifier.
4. Review script output for error messages.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

These scripts are provided under a BSD-style license. See the script headers for full license text.

## Disclaimer

This software is provided "AS IS", without warranty of any kind, express or implied.
