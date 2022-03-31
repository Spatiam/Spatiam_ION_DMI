# Spatiam-DMI-IPNSIG
This software will create, connect, and maintain your ION DTN nodes through Spatiam Corporation's DTN Network Platform.
Note: This software is in experimental status.

![architecture](https://s3.us-west-2.amazonaws.com/www.spatiam.com/external_media/spatiam_dmi_architecture.png)

### Demo
View our demo at https://youtu.be/LVo4pMIpKQQ

### Scripts
`instance.py` - Creates new nodes or access existing ones, download their ION configuration file, start ION, and run `spatiam_persist.py`

`spatiam_persist.py` - Continuously checks if a node's network has seen any updates, if so, the latest ION configuration file is downloaded, and ION is restarted

### Installation
- For the scripts to work properly you must have already built and installed ION on your machine (ionstart is ready to run). This has been tested with ION version 4.0.2 but is expected to work with all 4.X.X versions.
- Install Python (3) Requirements with `pip3 install -r requirements.txt`
- Run with `python3 instance.py`
