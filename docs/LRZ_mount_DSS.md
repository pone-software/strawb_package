# Mounting the DSS at a VM

This section covers a minimum example mounting (NFS) a DSS Container on a VM including a *Compute Cloud* VM. The only limitation is, that the VM (IP) has to be located in the LRZ data center.

## Prepare the DSS Container
1. Make sure you have the ‘**Is Manager**’ right for the DSS container on dssweb.dss.lrz.de (in case, someone of the ECP group has to give it to you).
1. log in at: dssweb.dss.lrz.de (only accessible in the ‘mwn’, in case use a VPN connection)
1. select the DSS container. You should see: ‘DSS Container Details’
1. Make sure you have the ‘Is Manager’ right for the DSS container in dssweb.dss.lrz.de. ( in case another Manager have to give it to you).
1. Add the ‘Funktionskennung’ of the VM (the one you need to set up the VM in the *Compute Cloud*) to the container user
   1. At **Container User** click `Add new user` and add the `Funktionskennung`
   1. Accept the invitation coming by mail (the person which is liked to the `Funktionskennung`)
1. At **NFS Exports** click `Add new export` and add the a IP of the VM (Floating IP for the *Compute Cloud* VM; the IP you will find at: https://cc.lrz.de/project/ -> Project -> Compute -> Instances)
1. keep the tab open, you’ll need the **Mount Path** (which is `<IP>:<Path>`) later.

## Create the users with the right UID on the VM
1. log in to the VM via `ssh ...`
1. In another tab, log in to: `ssh ab12cde@dsscli.dss.lrz.de` (called dsscli in the following); replace ab12cde with your LRZ ID (not the `Funktionskennung`). (Only accessible in the `mwn`, in case use a VPN connection).
   1. type `login` and log in with your LRZ ID and Password
   1. do the steps under **11.6. NFS helper functions** from the [official docs](https://doku.lrz.de/display/PUBLIC/DSS+documentation+for+data+curators#DSSdocumentationfordatacurators-NFShelperfunctions) which are:
       1. On **dsscli**: `dss passwd list --containername pr74qo-dss-0000 pr74qo` ; replace: `pr74qo-dss-0000` with your container name and `pr74qo` with your project name (you will find the information in the tab from above, dssweb.dss.lrz.de)
       1. **On the VM**: Add the returned lines to: `/etc/passwd`, (e.g., with `sudo vim /etc/passwd`)
       1. To the same with `dss group list --containername pr74qo-dss-0000 pr74qo` on **dsscli** to `/etc/groups` on the VM
       1. Now you have successfully added new user to the VM (passwords aren’t set)
   1. You can close the connection to **dsscli**, (`contr.` + `C`)
   1. Comment: you can also just extract the UID form a listed user <username>:x:1234567:2222::/home/<username>:-> 1234567. Change the UID on the VM of an existing user with useradd -u 1234567 <username_2> (This could cause some side effects like permission to the home directory). As for NFS, only the UID is important.
1. Set a password for one of the added user with: `sudo passwd <username>` (can be anything)
1. **Check**: you can check the UID with `id <username>` on the VM

## **Mount the Container**
1. This is the summary of: **2.2.3. Mounting a DSS Container on a VM** of the [official docs](https://doku.lrz.de/display/PUBLIC/DSS+documentation+for+users#DSSdocumentationforusers-usrgrp)
1. Create a new directory where the DSS is mounted to, here `/dss` and mount it. Replace `<IP>:<Path>` with the **Mount Path** from [**Prepare the DSS Container**](#Prepare-the-DSS-Container)
```bash
  sudo mkdir -p /dss
  sudo mount -t nfs -o rsize=1048576,wsize=1048576,hard,tcp,bg,timeo=600,vers=3 <IP>:<Path> /dss
```
1. Check: You can check with `df -h /dss` or `mount` if the `<Path>` is listed
1. Add it to `/etc/fstab` for **automated mount**
   1. modify the file with: `sudo vim /etc/fstab`
   1. add the line and replace `<IP>:<Path>` with the **Mount Path** from [**Prepare the DSS Container**](#Prepare-the-DSS-Container)
      ```bash
      <IP>:<Path> /dss  nfs    rsize=1048576,wsize=1048576,hard,tcp,bg,timeo=600,vers=3    0       0
      ```
   1. save and close the file
   1. to check if it works 
      ```bash
      sudo umount /dss 
      sudo mount /dss   # this is now enough, it reads the settings from /etc/fstab
      ```
   1. now the DSS is mounted automatically after a reboot
    
## Use the Container
   1. **Comment**: Only the users with the correct UID’s can access the `/dss` (The root-user (i.e. `sudo <cmd>` ) does not work here as it is set to `nobody` which is the wrong UID)
   1. **Option 1: change the user for the one CMD only**
       1. `sudo -u <username> <cmd>` , e.g. `sudo -u <username> ls /dss`
   1. **Option 2: change the user**
       1. `su - <username>` + enter the password you set before in the [section](#Create-the-users-with-the-right-UID-on-the-VM)
       1. execute a `<cmd>` , e.g. `ls /dss`