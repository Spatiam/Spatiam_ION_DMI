# Spatiam-DMI-IPNSIG
This software will create, connect, and maintain your ION DTN nodes through Spatiam Corporation's DTN Manager (https://www.spatiam.com/dtn-mgr/).
Note: This software is in experimental status.

![architecture](https://s3.us-west-2.amazonaws.com/www.spatiam.com/external_media/spatiam_dmi_architecture.png)

## Demo
View our demo at https://youtu.be/LVo4pMIpKQQ

### Features
- Spatiam DTN Manager Login
- Network Access through UUID
- Node Creation (Including Gateway Nodes)
- ION Launch and Relaunch
- Network Update Fetch
- Automatic ION Relaunch with Network Updates

### Installation
- For the scripts to work properly you must have already built and installed ION on your machine (`ionstart` is ready to run). The DMI has been tested with ION version 4.0.2 but it is expected to work with 4.X.X versions.
- Install Python (3) Requirements with `pip3 install -r requirements.txt`
- Run with `python3 instance.py`

### Scripts
`spatiam_instance.py` - Creates new nodes or access existing ones, download their ION configuration file, start ION, and run `spatiam_persist.py`

`spatiam_persist.py` - Continuously checks if a node's network has seen any updates, if so, the latest ION configuration file is downloaded, and ION is restarted
