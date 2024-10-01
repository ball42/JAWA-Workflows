# JAWA Workflows
## Greetings, friends.
### Note: this is a repository of various workflows that have been written for and tested with JAWA. These workflows are provided as-is and should be thoroughly tested in non-production environments prior to implementation. I can provide no guarantee, except that I'm trying my best.

<a href="#mobile-device-naming-workflow">Mobile Device Naming Workflow</a>
</br>
<a href="#usb-statistics-workflow">USB Statistics Workflow</a>
</br>
<a href="#update-devices-workflow">Update Devices Workflow</a>
</br>
<a href="#return-to-service-workflows">Return to Service Workflows</a>

## Mobile Device Naming Workflow
This workflow automatically names mobile devices using the `MobileDeviceEnrolled` event and Jamf Pro's Inventory Preload feature. It renames devices based on their asset tag during enrollment.

[View Mobile Device Naming Workflow](Mobile%20Device%20Names/README.md)

## USB Statistics Workflow
This workflow collects and stores USB device insertion events, providing insights into USB device usage across your organization.

[View USB Statistics Workflow](macOS%20USB%20Statistics/README.md)

## Update Devices Workflow
This workflow allows you to update extension attributes on mobile devices based on specific events or criteria.

[View Update Devices Workflow](Update%20Mobile%20Device%20EA/README.md)

## Return to Service Workflows
These workflows provide Return to Service (RtS) functionality for mobile devices managed by Jamf Pro. They work in conjunction with the Jamf Automation and Webhook Assistant (JAWA) to trigger RtS actions based on specific criteria.

### Features
- Automatic RtS triggering based on Smart Group membership changes
- Extension Attribute updates to track RtS enrollment status
- Configurable WiFi payload for RtS process
- OAuth 2.0 token-based authentication for enhanced security
- Compatibility with both Jamf Pro Classic API and newer API endpoints

### Available Scripts
1. `hcl_ea_rts.py`: Tailored for healthcare environments, utilizing a healthcare listener and an extension attribute.
2. `mobile_smartgroup_rts.py`: A general-purpose script suitable for any environment requiring RtS functionality.

[View Return to Service Workflows](Return%20to%20Service/README.md)

## Contributing
Contributions to these workflows are welcome! Please feel free to submit issues or pull requests to improve the functionality or documentation.

## License
These scripts are provided under a BSD-style license. See individual script headers for full license text.

## Disclaimer
This software is provided "AS IS", without warranty of any kind, express or implied. Use at your own risk and always test thoroughly in a non-production environment before implementation.

