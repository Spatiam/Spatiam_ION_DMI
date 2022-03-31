import sys
import time
import requests
import subprocess
from subprocess import PIPE
import datetime

MGR_API_URL = "https://www.spatiam.com/ion-dtn-mgr/api/"
CONFIG_FILENAME = "spatiam_config.txt"

AUTH_TOKEN = sys.argv[1]
NETWORK_ID = sys.argv[4]
NODE_UUID = sys.argv[5]
NODE_LISTENING_IP = sys.argv[6]

node_update = datetime.datetime.fromisoformat(sys.argv[2] + ' ' + sys.argv[3])

print("SPATIAM PERSISTENCE SCRIPT")
print("The provided node will restart if any network updates are detected")
print("\nChecking for updates ...")

# ---------------------------------------------------------------
# ion_alive: Checks bplist return code to check if ION is running
# ---------------------------------------------------------------
def ion_alive():
    command = "bplist"
    proc = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    proc.communicate()
    return proc.returncode == 0

# ---------------------------------------------------------------
# ionrestart: Starts ION, stops it first if it is already running
# ---------------------------------------------------------------
def ionrestart():
    print("Restarting ION ...")

    failed_restart = 1
    while True:
        
        if failed_restart >= 3:
            print("ION failed to respond, exiting program")
            quit()

        if ion_alive():
            ionstop_command = 'ionstop'
            subprocess.Popen([ionstop_command], shell=True, stdout=PIPE, stderr=PIPE).wait()

        ionstart_command = 'ionstart -I ' + CONFIG_FILENAME
        subprocess.Popen([ionstart_command], shell=True, stdout=PIPE, stderr=PIPE).wait()
        time.sleep(5)

        if not ion_alive():
            failed_restart += 1
        else:
            print("ION Successfully restarted")
            break

# ----------------------------------------------------------
# download_config: Download configuration file of given node
# ----------------------------------------------------------
def download_config():
    r = requests.get(MGR_API_URL + 'dynamic-config', params={'node': NODE_UUID, 'listeningip': NODE_LISTENING_IP, 'length':315360000})

    if r.status_code == 200:
        config = r.text
        # Update only if config file has changed (network could be reporting 'cosmetic' change)
        if not config == open(CONFIG_FILENAME).read():
            try:
                print("Network update detected (" + str(datetime.datetime.now())+")")
                config_file = open(CONFIG_FILENAME, "w")
                config_file.write(config)
                config_file.close()
                print("Node configuration downloaded (" +CONFIG_FILENAME +")")
                ionrestart()
                print("\nChecking for updates...")
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return True
    else:
        return False

# -----------------------------------------------------------------
# latest_network_update: Returns timestamp of latest network update
# -----------------------------------------------------------------
def latest_network_update():
    r = requests.get(MGR_API_URL + 'api/network/'+NETWORK_ID+'/last_change', headers = {'Authorization': 'Token ' + AUTH_TOKEN})
    if r.status_code == 200:
        return datetime.datetime.fromisoformat(r.text)
    else:
        return None

while True:
    latest_update = latest_network_update()
    
    # Network has had an update 
    if latest_update is not None and latest_update > node_update:
        if download_config():
            node_update = latest_update

    # In case ION stops working
    elif not ion_alive():
        print("ION failure detected (" + str(datetime.datetime.now()) + ")")
        ionrestart()
    
    time.sleep(10)