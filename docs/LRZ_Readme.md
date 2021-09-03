# LRZ Documentation

This project uses 2 different LRZ tools. The [DSS](#DSS) is the storage backend and the [Compute Cloud](#Compute Cloud) hosts VMs. (Maybe also the [Linux Cluster](https://doku.lrz.de/display/PUBLIC/Linux+Cluster) in the future.)

## Overview
For STRAW and STRAWb, the `straw-lrz-vm` runs 24/7, has 1 CPU with 4.5 GB RAM and therefore takes care of synchronising the module data and monitoring both detectors. But it can also do some simple calculations. For more power, another VM has to be set up. On the VM the DSS-Storage is mounted to `/dss`. 

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


## Compute Cloud
The *Compute Cloud* is a VM hosting service of the LRZ. Here are the (official docs)[https://doku.lrz.de/display/PUBLIC/Compute+Cloud]. By default, a project has 10 CPU cores with 4.5 GB RAM per Core. The RAM ratio is fixed, but the total number of CPU cores can be higher. Therefore, contact the LRZ service desk. The VMs among projects share the same hardware. Once a VM is active, it blocks the resource.
Therefore, it is important to only activate (un-shelf) the VMs if needed and deactivate (shelf) them afterwards. However, VMs with one Core per project can run constantly. Those VMs can do regular jobs which do not require much computation power and can be an entry point to (un-)shelf other VMs which do more intense jobs. (How this works precisely has to be figured out.)

### VM management-portal
The VM management-portal is https://cc.lrz.de. To login there, you need a special LRZ-ID similar to your normal LRZ-ID but different. For the moment this is: `di46lez` (password is posted in Slack, search for the ID).

#### IPs
You can assign a floating IP to a VM. This IP will never change unless you disassociate (unlink) it from the VM.

You can manage the floating IPs at the [management-portal](https://cc.lrz.de)`-> Project -> Network -> Floting IPs`.
To add a new IP, click `Allocate IP To Project`. The `mwn_pool` is not exposed and therefore not accessible from the internet, which is a major security issue.
In contrast, the `internt_pool` is accessible and exposed to the internet.

#### Key Pairs
You can add key pairs with [management-portal](https://cc.lrz.de)`-> Project -> Compute -> Key Pairs`. All key pairs are added to new created VMs only. For existing VMs you have to add the keys manually to each machine. For more instructions about the ssh key see the [dedicated section](#Access a VM via SSH).

### Access a VM via SSH
The access to a VM is restricted to ssh with key pair only. First create a new key pair. If you don't know how, search the internet for it. In the following the key 
To add a key, someone with access to the VM has to add your public part (.pub) of the ssh key to the file `~/.ssh/authorized_keys`. Afterwards you can log in with
```bash
ssh -i <your_key.key> <user_name>@<ip-address>
```
Replace `<your_key.key>` with the path to your .key file (not the .pub). The `<user_name>` and `<ip-address>` are in the [table below](#Parameters of hosted VMs and shh_config entries).

#### SSH config
To make the ssh command easier, you can set parameter pairs in the ssh-config file. The file is located on your computer at `~/.ssh/config` and add the following lines:
```bash
Host <name_for_the_vm>
    User            <user_name>
    HostName        <ip-address>
    IdentityFile    <your_key.key>
```
Replace `<name_for_the_vm>` with any name you want. Save the file. Now the ssh command reduce to:
```bash
ssh <name_for_the_vm>
```
In addition, the `<name_for_the_vm>` works with `rsync`, and `scp`.

#### Copy files from/to the VM with rsync or scp
To sync files between different machines (but also on the same machine) you can use `scp` or `rsync`. The usage, especially with a ssh-config is straight forward, e.g., to download/upload files from/to the VM:
```bash
rsync <name_for_the_vm>:"/path/to/files/*.txt" target/dir  # downloads files all txt-files from /path/to/files/
rsync target/dir/*.txt <name_for_the_vm>:"/path/to/files"  # upload files all txt-files from target/dir/
rsync <name_for_the_vm>:"/path/to/files" target/dir/files  # download the whole directory
rsync <name_for_the_vm>:"/path/to/files/" target/dir  # equals the line above
```
For directories, you have to take care to set the source string in the right syntax. Without or with a tailing `/` makes the different. Compare the last two lines of the example. Furthermore, there are many documentations - [like](https://linux.die.net/man/1/rsync) - explaining the difference and the various options.

#### Parameters of hosted VMs and shh_config entries

| Name | straw-lrz-vm (24/7, 1 CPU) |
| --- | --- |
| <user_name> | di46lez |
| <ip-address> | 138.246.233.224 |

SSH config entry:
```bash
Host straw-lrz-vm
    User            di46lez
    HostName        138.246.233.224
    IdentityFile    ~/.ssh/cloud.key
```

### 