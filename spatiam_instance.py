import os
import requests
import subprocess
from subprocess import PIPE
from getpass4 import getpass

MGR_API_URL = "https://www.spatiam.com/ion-dtn-mgr/api/"
CONFIG_FILENAME = "spatiam_config.txt"
NOHUP_OUT_FILENAME = "spatiam_ionstart.out"
PERSIST_OUT_FILENAME = "spatiam_persist.out"
PERSIST_SCRIPT = "spatiam_persist.py"
DEFAULT_NETWORK_ID = None

class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
print(style.UNDERLINE+"\nWelcome to Spatiam Corporation's ION DMI (DTN Manager Interface)"+style.RESET)
print("\nThis software will create, connect, and maintain your ION DTN nodes through Spatiam's DTN Manager "+ style.CYAN+"https://www.spatiam.com/ion-dtn-mgr/"+style.RESET)
print("For a quick tutorial, please visit "+ style.CYAN+"https://youtu.be/LVo4pMIpKQQ"+style.RESET)

print("\nLoading system info, please wait...")

# Attempt to grab Local and Public IPs of the system
try:
    command = "ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\\2/p'"
    proc = subprocess.Popen([command], shell=True, stdout=PIPE)
    (localip,error) = proc.communicate()
    localip = localip.decode('utf-8').strip()
except:
    localip = None

r = requests.get('https://api.ipify.org', timeout=10)
if r.status_code == 200:
    publicip = r.content.decode('utf8')
else:
    try:
        command = "wget -qO- https://ipecho.net/plain ; echo"
        proc = subprocess.Popen([command], shell=True, stdout=PIPE)
        (publicip,error) = proc.communicate()
        publicip = publicip.decode('utf-8').strip()
    except:
        publicip = None

# ----------------------------------------------------------
# download_config: Download configuration file of given node
# ----------------------------------------------------------
def download_config(node_uuid, node_listening_ip):
    print("Downloading ION configuration ...")
    r = requests.get(MGR_API_URL + 'dynamic-config', params={'node': node_uuid, 'listeningip': node_listening_ip, 'length':315360000})

    if r.status_code == 200:
        config = r.text
        try:
            config_file = open(CONFIG_FILENAME, "w")
            config_file.write(config)
            config_file.close()
            print(style.GREEN+ "Node configuration downloaded, written to " + style.CYAN + CONFIG_FILENAME+style.RESET)

            r = requests.get(MGR_API_URL + 'api/network/'+current_network+'/last_change', headers = {'Authorization': 'Token ' + auth_token})
            if r.status_code == 200:
                return r.text
            else:
                print(style.RED+ "Error accessing network timestamp" +style.RESET)
                return None

        except Exception as e:
            print(style.RED+ str(e) +style.RESET)
            return None
    else:
        print(style.RED+ r.text +style.RESET)

# ---------------------------------------------------------
# create_node: Create node with given info at given network
# ---------------------------------------------------------
def create_node(auth_token, publicip, localip, node_network):
    if input("Will this new node sit behind a gateway node (yes/no): ") == "yes":
        parent_uuid = input("Gateway Node UUID: ")
    else:
        parent_uuid = None

    node_eid = input("\nNode EID: ")
    if publicip:
        node_public_ip = input("Node Public IP (ENTER for " + publicip + "): ") or publicip
    else:
        node_public_ip = input("Node Public IP: ")
    
    if localip:
        node_listening_ip = input("Node Local (Listening) IP (Press ENTER for " + localip + "): ") or localip
    else:
        node_listening_ip = input("Node Local (Listening) IP: ")
    node_port = input("Node Listening Port: ")

    node_create_url = MGR_API_URL + 'api/nodes/'
    headers = {'Authorization': 'Token ' + auth_token}
    node_data = {'eid': node_eid, 'public_ip': node_public_ip, 'port': node_port, 'network': node_network}
    if parent_uuid: node_data['parent'] = parent_uuid
    print("Creating node ...")
    r = requests.post(node_create_url, headers=headers, data=node_data)

    if r.status_code == 201:
        node = r.json()
        node["listening_ip"] = node_listening_ip
        print(style.GREEN+"\nNode created successfully"+style.RESET)

        print(style.MAGENTA+"\n--- Configuration Download ---\n"+style.RESET)
        return download_config(node["uuid"], node_listening_ip), node
    
    else:
        print(style.RED+ r.text +style.RESET)
        return None, None

# ----------------------------------------------------------
# switch_network: Checks if user has access to given network
# ----------------------------------------------------------
def switch_network(auth_token, current_network, current_network_name, access_network=None):
    if not access_network:
        access_network = input("\nNetwork UUID: ")
    network_access_url = MGR_API_URL + 'api/network/access_network?uuid=' + access_network
    headers = {'Authorization': 'Token ' + auth_token}
    print("Accessing network ...")
    r = requests.get(network_access_url, headers=headers)
    if r.status_code == 200:
        print(style.GREEN+ "Switched to " + r.json()["name"] + style.RESET)
        return access_network, r.json()["name"], True
    else:
        print(style.RED+ "Switch failed: " + r.text +style.RESET)
        return current_network, current_network_name, False

# ---------------------------------------------------------------
# ion_alive: Checks bplist return code to check if ION is running
# ---------------------------------------------------------------
def ion_alive():
    command = "bplist"
    proc = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    proc.communicate()
    return proc.returncode == 0

# -------------------------------------------------------------
# ionrestart: Starts ION, stops it first if it is already running
# -------------------------------------------------------------
def ionrestart():
    if ion_alive():
        ionstop_command = 'ionstop'
        print("\nExecuting command: " + style.CYAN + ionstop_command + style.RESET)
        subprocess.Popen([ionstop_command], shell=True).wait()

    ionstart_command = 'ionstart -I ' + CONFIG_FILENAME
    print("\nExecuting command: " + style.CYAN + ionstart_command + style.RESET)
    subprocess.Popen([ionstart_command], shell=True).wait()

auth_success = False

# ---------------------------------
# Step 1: User authentication phase
# ---------------------------------
print(style.MAGENTA+"\n--- User Auth ---"+style.RESET)
while not auth_success:

    username = input("Username: ")
    password = getpass('Password: ')

    auth_url = MGR_API_URL + 'auth/'
    user_auth = {'username': username, 'password': password}
    
    print("Loging in ...")
    r = requests.post(auth_url, data=user_auth)

    if r.status_code == 200:
        auth_success = True
        auth_token = str(r.json()["token"])
        print(style.GREEN+"Auth successful"+style.RESET)

    else:
        print(style.RED+ "Auth failed, please try again." +style.RESET)

# ---------------------------------------
# Step 2: Check access to default network
# ---------------------------------------
switch_success = False
if DEFAULT_NETWORK_ID:
    current_network, current_network_name, switch_success = switch_network(auth_token, DEFAULT_NETWORK_ID, None, DEFAULT_NETWORK_ID)
while not switch_success:
    print(style.MAGENTA+"\n--- Access a Network ---"+style.RESET)
    current_network, current_network_name, switch_success = switch_network(auth_token, None, None)

# ----------------------------------------------------------------------
# Step 3: Node Initialization (create node, access node, switch network)
# ----------------------------------------------------------------------
choice = None
while not (choice in ["1","2"]):
    print(style.MAGENTA+"\n--- Node Initialization ---\n"+style.RESET)
    print("[1] Create new node (" + current_network_name + ")")
    print("[2] Access existing node")
    print("[3] Switch to another network")
    choice = input("\nEnter action: ").strip(' ').strip('[').strip(']')
    while not (choice in ["1","2","3"]):
        choice = input("Invalid, enter action:")

    if choice == "1":
        last_update, node = create_node(auth_token, publicip, localip, current_network)
        if not last_update:
            choice = "failed"
        elif node:
          node_uuid = node["uuid"]
          node_listening_ip = node["listening_ip"]

    elif choice == "2": 
        node_uuid = input("\nNode UUID: ")

        if localip:
            node_listening_ip = input("Node Local (Listening) IP (Press ENTER for " + localip + "): ") or localip
        else:
            node_listening_ip = input("Node Local (Listening) IP: ")

        last_update = download_config(node_uuid, node_listening_ip)
        
        if not last_update:
            choice = "failed"

    elif choice == "3": 
        current_network, current_network_name, switch_success = switch_network(auth_token, current_network, current_network_name)

# -------------------
# Step 4: ION Startup
# -------------------
print(style.MAGENTA+"\n--- ION Startup ---\n"+style.RESET)
print("[1] Launch ION Node")
print("[2] More actions")
print("[q] Quit program")
choice = input("\nEnter action: ").strip(' ').strip('[').strip(']')
while not (choice in ["1","2","q"]):
    choice = input("Invalid, enter action:")

if choice in ["1","2"] :
    
    if choice == "1":
        ionrestart()

    script_exit = False
    while not script_exit:
    
        print(style.MAGENTA+"\n--- More Actions ---\n"+style.RESET)

        # -------------------
        # Step 5: More Actions
        # -------------------
        if(choice == "1"):
            print("[1] Relaunch ION Node")
        if(choice == "2"):
            print("[1] Launch ION Node")
        print("[2] Run persistence script")
        print("[3] Run persistence script in the background (nohup) and quit")
        print("[q] Quit program")
        choice = input("\nEnter action: ").strip(' ').strip('[').strip(']')
        while not (choice in ["1", "2", "3", "q"]):
            choice = input("Invalid, enter action:")
        
        if choice == "1":
            ionrestart()
        
        elif choice == "2":
            try:
                persistence_command = "python3 ./{script} {auth} {lastupdate} {network} {uuid} {listeningip}".format(
                script = PERSIST_SCRIPT, auth= auth_token, lastupdate = last_update, network=current_network, uuid=node_uuid, listeningip=node_listening_ip)
                subprocess.Popen([persistence_command], shell=True).wait()
            except KeyboardInterrupt:
                pass
        
        elif choice == "3":
            persistence_command_background = "nohup python3 -u ./{script} {auth} {lastupdate} {network} {uuid} {listeningip} > ./{outfile} 2>&1 &".format(
                script = PERSIST_SCRIPT, auth= auth_token, lastupdate = last_update, network=current_network, uuid=node_uuid, listeningip=node_listening_ip, outfile=PERSIST_OUT_FILENAME)
            
            # Change to subprocess
            os.system(persistence_command_background)
            script_exit = True
        else:
            script_exit = True