# Comprehensive Lab Guide

This guide outlines the setup requirements for installing and configuring the entire distributed honeypot system including:  
- **Chapter One** Setting up Virtual Machines   
- **Chapter Two** Setting up Honeypot Loggers
    - Cowrie Installation
    - Dionaea Installation
- **Chapter Three** Deploying Server & Worker Code  
    - Server Code Requirements
    - Worker Code Requirements  
- **Chapter Four** Deploying Machine Learning Classification Code 

---
## Chapter One: Virtual Machine Setup Guide

This guide outlines the setup requirements setting up both Master and Honeypot Virtual Machines using VMware Workstation.

---

#### 1. Download Ubuntu 22.04.3 LTS ISO
``` 
Go to Ubuntus offical download page: https://ubuntu.com/download/desktop
Select the latest version "22.04.3" and download it
```

#### 2. Create Virtual Machines
```
Open VMware Workstation 
    Create a New Virtual Machine  
    Configuration Type -> Custom
    Install from -> "Installer disc image file (iso)" (Select the .iso you just downloaded from Ubuntu)
    Virtual Machine Name -> (Master_server), (Honeypot-Cowrie), or (Honeypot_dionaea) depending on which one you are making
    Network Type -> Bridged or Host-only (Chose host-only if you want a more secure isolated environment)
    For all other settings select what works best for your environment
```

#### 3. Setup Ubuntu 
```bash 
sudo apt update && sudo apt upgrade -y
sudo apt install git curl python3 python3-pip ufw -y
```
Optionally 
```bash
sudo ufw allow ssh
sudo ufw enable
#name the VM
sudo nano /etc/hostname
    #cowrie-node
    #dionaea-node
    #master-node
```
## Chapter Two: Honeypot Loggers Setup

This guide outlines the steps required to clone, configure, and start **Cowrie** and **Dionaea**.

---
### Cowrie Setup

In order to run `Cowrie`, the following installation and setup is required on one of the **worker / honeypot Ubuntu virtual machines**.

#### 1. Create A Cowrie User
```bash
sudo adduser --disabled-password cowrie
sudo su - cowrie
```

#### 2. Clone Cowrie Over
```bash
git clone http://github.com/cowrie/cowrie
cd cowrie
```

#### 3. Setup Virtual Environment
```bash
#Ensure you are in the directory
/home/cowrie/cowrie
#Check using 
pwd
#Create Virtual Environment
python3 -m venv cowrie-env
#Start Virtual Environment
source cowrie-env/bin/activate
#Install all dependencies for Cowrie
python -m pip install -e .
```

#### 4. Start Cowrie
```bash 
cowrie start
```
**Note**: If you want to change any configurations such as to switch logging to port 22 and enable telnet edit the config.cfg file
```bash
cd /cowrie/etc
vi config.cfg

[telnet]
enabled = true

[ssh]
enabled = true
listen_port = 22
```

### Dionaea Setup

In order to run `Dionaea`, the following installation and setup is required on the other **worker / honeypot Ubuntu virtual machines**.
(PLACEHOLDER FOR NOW)


## Chapter Three: Code Setup Guide

This guide outlines the setup requirements for running both the **master/server** (`server_code.py`) and **worker/honeypot** (`honeypot_code.py`) components of the distributed honeypot system.

---

### Server Code Requirements

In order to run `server_code.py`, the following installation and setup is required on the **master/server Ubuntu virtual machine**.

#### 1. Update System and Install Python
```bash
sudo apt update
sudo apt install -y python3 python3-pip
```
#### 2. Create Project Directory
```bash
mkdir ~/server
cd ~/server
```
#### 3. Install Python Dependencies
```bash
pip install fastapi uvicorn requests
```

#### 4. Create File Infastructure
```bash
mkdir master_data
touch master_data/aggregated_logs.jsonl
touch master_data/workers.json
```

#### 5. Start (`server_code.py`)
```bash
python3 server_code.py
```

### Honeypot / Worker Code Requirements

In order to run `honeypot_code.py`, the following installation and setup is required on the **worker / honeypot Ubuntu virtual machine**.

#### 1. Update System and Install Python
```bash
sudo apt update
sudo apt install -y python3 python3-pip
```
#### 2. Create Project Directory
```bash
mkdir ~/honeypot_worker
cd ~/honeypot_worker
```
#### 3. Create File Infastructure
```bash
mkdir -p /cowrie/var/log/cowrie/sent
```
#### 4. Configure Server URL
```bash
vi honeypot_code.py
#Change MASTER_URL to include your Master servers IP address
MASTER_URL = "http://<MASTER_IP>:6967/submit"
```
#### 5. Start (`honeypot_code.py`)
```bash
python3 honeypot_code.py
```

## Chapter Four: Machine Learning Code Setup

This guide outlines the setup requirements for running the classification base machine learning alorithm `placeholdername.py` on the **master/server**. 

---