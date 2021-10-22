# LRZ Documentation

This project uses 2 different LRZ tools. The [DSS](#DSS) is the storage backend and the [Compute Cloud](#compute-cloud---vm-hosting) hosts VMs. (Maybe also the [Linux Cluster](https://doku.lrz.de/display/PUBLIC/Linux+Cluster) in the future.)

## Overview
For STRAW and STRAWb, the `STRAW-LRZ-VM` runs 24/7, has 1 CPU with 4.5 GB RAM and therefore takes care of synchronising the module data from the ONC DB and monitoring both detectors. But it can also do some simple calculations. For more power, another VM has to be set up. On the VM the DSS-Storage is mounted to `/dss`. 

## DSS
The digital scientific storage (DSS) is s service provided by the LRZ (Munich).  Here are the [official docs](https://doku.lrz.de/display/PUBLIC/Data+Science+Storage) for more information. 
You can access the DSS in two different ways. 
1. Mount the DSS container, e.g., on a VM hosted by the *Compute Cloud*. Important only a device with a mwn IP can mount the container. The section [Mounting the DSS at a VM](LRZ_mount_DSS.md) describes the required steps. 
1. Access the DSS via [Globus](https://www.globus.org) which is a web-application similar to any cloud storage. The section [Globus](#Globus) describes the required steps.

### Management platform
At the DSS management webpage https://dssweb.dss.lrz.de (only accessible within the TUM network, in case use a VPN connection), persons with management permission see the DSS Containers. There you can manage the members, add NFS exports and more.

### Globus
A platform to share data like a OwnCloud, NextCloud, DropBox, GoogleDrive, or similar which is linked to the DSS.
At the [Globus webpage](https://www.globus.org) you can log in with your LRZ credentials. By default, your account isn't granted access to the DSS. To do so, follow the [registration section](#Registration).

When your registration was successfully, you can select in the `File Manager`-tab (default after you log in at [Globus](https://www.globus.org)):

| **Collection** | `Leibniz Supercomputing Centre's DSS - CILogon` |
| --- | --- |
| **Path** | `/dss/dsstumfs02/pn69gu/pn69gu-dss-0004/` |

and set a **bookmark** for a faster access the next time.

#### Registration
Before you can use *Globus* the first time, you have to do register that your LRZ credential gets the privileges for *Globus*. 
- Open: [Welcome at LRZ's
Credential Registration Service for
Globus data transfers](https://www.dss.lrz.de/cilogon/register)
- Scroll down for the *Step by Step* guide **before you click the button**.
The important part is the *Select the Identity Provider*: LRZ must be selected and not TUM or LMU

The registration can take a while until it's transferred to the *Globus* server. Afterwards, you can log in with your LRZ credentials and access the DSS at https://app.globus.org/


## Compute Cloud - VM hosting
The *Compute Cloud* is a VM hosting service of the LRZ. Here are the [official docs](https://doku.lrz.de/display/PUBLIC/Compute+Cloud). By default, a project has 10 CPU cores with 4.5 GB RAM per Core. The RAM ratio is fixed, but the total number of CPU cores can be higher. Therefore, contact the LRZ service desk.

The VMs among projects share the same hardware. Once a VM is active, it blocks the resource.
Therefore, it is important to only activate (un-shelf) the VMs if needed and deactivate (shelf) them afterwards. However, VMs with one Core per project can run constantly. Those VMs can do regular jobs which do not require much computation power and can be an entry point to (un-)shelf other VMs which do more intense jobs. (How this works in an automated manner has to be figured out.)

This chapter contains the following sections:
- a list of [Hosted VMs](#hosted-vms---parameters-and-shh_config-entries)
- a summary of the [VM management-portal](#vm-management-portal)
- and how to [access a VM via SSH](#access-a-vm-via-ssh) including ssh basics and 

### Hosted VMs - Parameters and shh_config entries

The list of actual hosted VMs.

| VM Name | resources | <user_name> | <ip_address> |
| --- | --- | --- | --- |
| STRAW-LRZ-VM | Active 24/7, 1 CPU, 4.5GB | di46lez | 138.246.233.224 |

#### SSH config entries
SSH config entries to add to `~/.ssh/config`:
```bash
Host straw-lrz-vm
    User            di46lez
    HostName        138.246.233.224
    IdentityFile    ~/.ssh/cloud.key
```

### VM management-portal
The VM management-portal is https://cc.lrz.de. To login there, you need a special LRZ-ID similar to your normal LRZ-ID but different. For the moment this is: `di46lez` (password is posted in Slack, search for the ID).

#### IPs
You can assign a floating IP to a VM. This IP will never change unless you disassociate (unlink) it from the VM.

You can manage the floating IPs at the [management-portal](https://cc.lrz.de)`-> Project -> Network -> Floting IPs`.
To add a new IP, click `Allocate IP To Project`. The `mwn_pool` is not exposed and therefore not accessible from the internet, which is a major security issue.
In contrast, the `internt_pool` is accessible and exposed to the internet.

#### Key Pairs
You can add key pairs with [management-portal](https://cc.lrz.de)`-> Project -> Compute -> Key Pairs`. All key pairs are added to new created VMs only. For existing VMs you have to add the keys manually to each machine. For more instructions about the ssh key see the [dedicated section](#Access-a-VM-via-SSH).

### Access a VM via SSH

The access to a VM is restricted to ssh with key pair only. First create a new key pair. If you don't know how, search the internet for it. In the following the key 
To add a key, someone with access to the VM has to add your public part (.pub) of the ssh key to the file `~/.ssh/authorized_keys`. Afterwards you can log in with
```bash
ssh -i <your_key.key> <user_name>@<ip-address>
```
Replace `<your_key.key>` with the path to your .key file (not the .pub). The `<user_name>` and `<ip-address>` are in the [table of hosted VMs](#hosted-vms---parameters-and-shh_config-entries).

#### SSH config
To make the ssh command easier, you can set parameter pairs in the ssh-config file. The file is located on your computer at `~/.ssh/config` and add the following lines:
```bash
Host <name_of_the_vm>
    User            <user_name>
    HostName        <ip-address>
    IdentityFile    <your_key.key>
```
Replace `<name_of_the_vm>` with any name you want. Save the file. Now the ssh command reduce to:
```bash
ssh <name_of_the_vm>
```
In addition, the `<name_of_the_vm>` works with `rsync`, and `scp`.


## Some examples to use a VM
### Copy files from/to the VM with rsync or scp
To sync files between different machines (but also on the same machine) you can use `scp` or `rsync`. The usage, especially with a ssh-config is straight forward, e.g., to download/upload files from/to the VM:
```bash
rsync <name_of_the_vm>:"/path/to/files/*.txt" target/dir  # downloads files all txt-files from /path/to/files/
rsync target/dir/*.txt <name_of_the_vm>:"/path/to/files"  # upload files all txt-files from target/dir/
rsync <name_of_the_vm>:"/path/to/files" target/dir/files  # download the whole directory
rsync <name_of_the_vm>:"/path/to/files/" target/dir  # equals the line above
```
For directories, you have to take care to set the source string in the right syntax. Without or with a tailing `/` makes the different. Compare the last two lines of the example. Furthermore, there are many documentations - [like](https://linux.die.net/man/1/rsync) - explaining the difference and the various options.

### Jupyter Notebook 

A jupyter notebook server is running on the `STRAW-LRZ-VM` at port 8080. To use it, on your computer:
1. open a tunnel from your computer: `ssh -L 8080:localhost:8080 <name_of_the_vm>` and leave the terminal open incl. the ssh connection.
1. open http://localhost:8080 in the browser, PW: `strawb`

#### (Re-)start the server, on the VM
Log in to the VM via `ssh -L 8080:localhost:8080 straw-lrz-vm` or `ssh straw-lrz-vm` , does not matter.
For the restart, make sure that the old process isn’t running at the target port. For this, get the PID with e.g., `ps -ef | grep jupyter-notebook` or `htop` or similar. In case, kill it with `kill <PID>`.
```bash
jupyter notebook --no-browser --port=8080&; disown
```
From `&; disown`; `&` will put the task in background and `disown` unlinks it from the user, as closing the ssh connection will stop all linked processes.

#### Ports
You can also use any other port on your end or the vm, e.g., if you connect to different machines at once.
On the VM start the server with an updated `--port=<VM_PORT>` ; `<VM_PORT>` can be any unused port
The tunnel: 
```bash
ssh -L <LOCAL_PORT>:localhost:<VM_PORT> <name_of_the_vm>
```
has to match the `<VM_PORT>` and `<LOCAL_PORT>` can be any unused port + http://localhost:LOCAL_PORT