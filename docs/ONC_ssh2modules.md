# SSH to Modules
The deployed modules aren't exposed to the internet for security reasons. A VM, hosted by ONC, is in place to and works as a proxy and is accessible from the internet.
This means, you first have to `ssh` to the ONC VM and from there `ssh` to the module. Furthermore, the login to the ONC VM is only possible with a ssh key.
Which means, if your keys isn't added there, contact someone with access to the VM and ask her if she can add your key. 

First login to the VM with
```bash
ssh -i ~/.ssh/straw -p 10022 straw@strawb.onc.uvic.ca
```

from there you can access a module another ssh connection.
```bash
ssh odroid@<IP>   # e.g. <IP>=10.136.117.166 for standardmodule001,... ; PW: odroid
```
Quite complicated! To make your life easier, use [ssh configs from the next section](#SSH-Config-file).

## SSH Config file

For a fast and easy access to all modules add the lines from the [entries for the config-file](#Entries-for-the-config-file) to your `~/.ssh/config`. (Open it with a txt editor, e.g. `vim`, add the lines and save it.)

In addition, add the [module ssh key pair](#Module ssh key pair) (`~/.ssh/id_rsa_mctl.pub` and `~/.ssh/id_rsa_mctl`) to your computer for password-less login to the model.

Once this is done, commands simplify to (when connecting the first time, you have to accept the fingerprint):

| Command | explanation |
| --- | --- |
| `ssh lidar1` | log in to the model |
|`ssh lidar1 '/home/odroid/mctl/mctl/mctl_client.py module temp` | execute a command via ssh directly |
| `scp lidar1:'/d/sdaq/*' .` | download directly from the module with scp |
| `rsync lidar1:'/d/sdaq/*' .` | download directly from the module with rsync |
| `rsync --info=progress2 -au lidar1:'/d/sdaq/*' .` | above + total progress information, timestamps, and permission |

#### Entries for the config file
Add to the `~/.ssh/config` file, e.g., with `vim ~/.ssh/config`.

The entries use `~/.ssh/straw` as the ssh key for the ONC-VM. This means,  you have 3 options:
- you have created a key pair with this name, and this key is authenticated on the VM
- you copy your exiting key which is authenticated on the VM with, e.g., `cp <orignial_key> ~/.ssh/straw`
- or you replace `~/.ssh/straw` in all lines with the absolute path to your key file (`id_rsa_file`) you use to log in to the VM from ONC.
For this you can use the [attached script below](#script-to-create-the-above-lines) and replace the `id_rsa_file` in `a` or `find and replace` in any editor.
  
``` shell
Host strawb
        User            straw
        HostName        strawb.onc.uvic.ca
        Port            10022
        IdentityFile    ~/.ssh/straw
        
Host standard1
        User            odroid
        HostName        10.136.117.166
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host lidar1
        User            odroid
        HostName        10.136.117.167
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host lidar2
        User            odroid
        HostName        10.136.117.160
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host pmtspec1
        User            odroid
        HostName        10.136.117.168
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host pmtspec2
        User            odroid
        HostName        10.136.117.161
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host muontracker1
        User            odroid
        HostName        10.136.117.164
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host minispec1
        User            odroid
        HostName        10.136.117.165
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl

Host standard4
        User            odroid
        HostName        10.136.117.180
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p
        IdentityFile    ~/.ssh/id_rsa_mctl
```

#### Explanation
```bash
Host standard1
        User            odroid  # user on the module/odroid
        HostName        10.136.117.166  # IP of the module
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p  # routes through the VM
        IdentityFile    ~/.ssh/id_rsa_mctl  # key file for the module/odroid
```

### Module ssh key pair
If you don't want to use the password (`odroid`) to log in to the modules, you can create the following key pair (`~/.ssh/id_rsa_mctl.pub` and `~/.ssh/id_rsa_mctl`) with the following commands. Each module has this key already listed as authenticated.
Adding private keys to repositories is general a bad idea. However, the security comes here from the key to the ONC VM. Important is also to do the `chmod` which is included in the commands, already. Run the commands in the terminal:
```bash
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCn3S2f2/TwOGnbT/H4G5buGlNqctmt6ZjZvdrESwgE5jgMsnMeOf1dyrIsBj5ESNM+5N4kZnNya/Gly1eLHdlrJaVD4OjrRsPwaFS6N3G8eq0jVmn/8hnjurWePCyoJeaQ6aFcGB7bJUmmuQccxRptOICC/qYmoxNbETK0XDODklAUHKtUl7AIoFNxBkmvp/nFwxfVotehfEVzzMVJDI47xoBjnTjzU5mhQlYySx3Gb/BjjY8+vgLjDkp2VZKjMqdEc3XeLsxTDh/b88RwXWtJ+PgwCiiNmWz3g7c46CvoEHUsceREAnIxDoEFL7V2eWAvPNLS3ua3Cz3qcLojZqZP odroid@odroidc2' > ~/.ssh/id_rsa_mctl.pub
# creates and writes the public key to the file
chmod g-w,o-w ~/.ssh/id_rsa_mctl.pub
```

```bash
echo '-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABFwAAAAdzc2gtcn
NhAAAAAwEAAQAAAQEAp90tn9v08Dhp20/x+BuW7hpTanLZremY2b3axEsIBOY4DLJzHjn9
XcqyLAY+REjTPuTeJGZzcmvxpctXix3ZayWlQ+Do60bD8GhUujdxvHqtI1Zp//IZ47q1nj
wsqCXmkOmhXBge2yVJprkHHMUabTiAgv6mJqMTWxEytFwzg5JQFByrVJewCKBTcQZJr6f5
xcMX1aLXoXxFc8zFSQyOO8aAY50481OZoUJWMksdxm/wY42PPr4C4w5KdlWSozKnRHN13i
7MUw4f2/PEcF1rSfj4MAoojZls94O3OOgr6BB1LHHkRAJyMQ6BBS+1dnlgLzzS0t7mtws9
6nC6I2amTwAAA8gWnq6bFp6umwAAAAdzc2gtcnNhAAABAQCn3S2f2/TwOGnbT/H4G5buGl
Nqctmt6ZjZvdrESwgE5jgMsnMeOf1dyrIsBj5ESNM+5N4kZnNya/Gly1eLHdlrJaVD4Ojr
RsPwaFS6N3G8eq0jVmn/8hnjurWePCyoJeaQ6aFcGB7bJUmmuQccxRptOICC/qYmoxNbET
K0XDODklAUHKtUl7AIoFNxBkmvp/nFwxfVotehfEVzzMVJDI47xoBjnTjzU5mhQlYySx3G
b/BjjY8+vgLjDkp2VZKjMqdEc3XeLsxTDh/b88RwXWtJ+PgwCiiNmWz3g7c46CvoEHUsce
REAnIxDoEFL7V2eWAvPNLS3ua3Cz3qcLojZqZPAAAAAwEAAQAAAQAw08YspLdnlJE+CNAS
YjwRwDiZUxT8YGFknLPguw53FlwhXVrc5PNM7+PJqHs+M4y2063GGsLj+oAMwMwTHDic0R
N0XhyCK1BdQou6qtv7fheUmtM0bsCXHD0t7MT0mCmr5zlXZ3C6P+tfgpyOAstAD9pZwCam
QHMl3yfHjLYzQ8gOuqhSLGHMJD/11HHUiX2HO7wISj0yLxb+5UxkJN8RS6beOi9gOVdvpk
TwcNu6u5J8VWn5k04lqMcXLAp+Z4/EfFb6a4nyjtHvNn4k7/mcrjyUkAVdPG/3tM17WZi3
WEwDBwAJ+SfKVgmuCDS5ond21yZyQTrDqqrx33eeiESpAAAAgQCNmve/F4b71lbfNMrIPD
xkxf5li2kYei4MWQCFXIIy7v0K3ddCY/CtcXuXjts9hP91jJm7onKk/Op/29ixnZSzVyOO
E/HHir9jXQQMZz9xIALDO9e/Cs+f9eqBKBeVWCNJ2cUZDFadJCkgZ0ou4PdO3HD+IPBGqo
vOfeKw9ze1XgAAAIEA3MwfjR3PESaVTymuoXRwvSlKvZ2vnVhAfHjlK4Q8/FTui5g7zdQc
sHbKaeAwELYcrCJ64s2pq0qJpjwQnd9F6Zm4/R6jyv/xnSnlTQhb3N+yHv7ZQIMPOJXYEc
SYJeA2aw5hYsBB1ZkM58OvceuumX0OmT0M+jGGilw6IvxlVz0AAACBAMKgkj+FRIS3SLIJ
lvd9jS63OxylQoHDh23ZnB/8vV7eYxEQf+vgDCudDMp0zy/8LW8Kblmtj4SjPFDArhWDV9
zqeaSVjncHp/PIMgkUeaHnzRUu0cZ2/xNpOIQAEZqclFZglDRrESZGvDyiUDezJOXcaDHb
p+5BXA56IZE0CGx7AAAAD29kcm9pZEBvZHJvaWRjMgECAw==
-----END OPENSSH PRIVATE KEY-----' > ~/.ssh/id_rsa_mctl
chmod g-rw,o-rw ~/.ssh/id_rsa_mctl  # keys are only accepted with those permissions
```



### Script to create the above lines

Check for changes of `module_onc_id` in the [source MCTL config file](https://gitlab.lrz.de/strawb/mctl/-/blob/master/mctl/config.py) or you can import it directly. The code tries to import it directly, if it fails it use the hardcoded `module_onc_id`.
For the later you have to take care that the specs are correct. 

``` Python
try:
    from mctl.config import Config
    dev_code2ip_add = Config.dev_code2ip_add
except Exception as a:
    print(f'Failed with: {a}\n\n')
    module_onc_id: dict = {'0000006605b0': {'ip_add': '10.136.117.166', 'dev_code': 'TUMSTANDARDMODULE001'},
                           '000000661e33': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TUMSTANDARDMODULE002'},
                           '00000065e581': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TUMSTANDARDMODULE003'},
                           '00000066127f': {'ip_add': '10.136.117.167', 'dev_code': 'TUMLIDAR001'},
                           '00000066178e': {'ip_add': '10.136.117.160', 'dev_code': 'TUMLIDAR002'},
                           '00000065fa1b': {'ip_add': '10.136.117.168', 'dev_code': 'TUMPMTSPECTROMETER001'},
                           '0000006606bd': {'ip_add': '10.136.117.161', 'dev_code': 'TUMPMTSPECTROMETER002'},
                           '00000065e091': {'ip_add': '10.136.117.164', 'dev_code': 'TUMMUONTRACKER001'},
                           '00000065ff9b': {'ip_add': '10.136.117.165', 'dev_code': 'TUMMINISPECTROMETER001'},
                           '0000006601ee': {'ip_add': '10.136.117.180', 'dev_code': 'TUMSTANDARDMODULE004'},
                           '00000065fcc0': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TEST'}}
    
    dev_code2ip_add = {i['dev_code']: i['ip_add'] for i in module_onc_id.values()}

a = "Host {name}\n\
        User            odroid\n\
        HostName        {ip}\n\
        ProxyCommand    ssh -p 10022 -i ~/.ssh/straw straw@strawb.onc.uvic.ca -W %h:%p\n\
        IdentityFile    ~/.ssh/id_rsa_mctl"

for key_i, value_i in dev_code2ip_add.items():
    if value_i != 'XX.XXX.XXX.XXX':
        key_i = key_i.replace('TUM','')
        key_i = key_i.replace('MODULE','')
        key_i = key_i.replace('SPECTROMETER','PMTSPEC')
        key_i = key_i.replace('00','')
        print(a.format(name=key_i.lower(), ip=value_i))
        print()
```