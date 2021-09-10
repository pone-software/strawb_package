# Github 


## Download a repository (git clone)
In order to download an exiting repository, follow the [official GitHub guid](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository).
GitLab works nearly the same, only search for the `Clone`(GitLab) instead of the `Code`(GitHub) button. Make sure you select the HTTPS (Token) or SSH link, depending on your setup.


# PyCharm
PyCharm is a powerful IDE for various coding languages. And it helps to develop python code way faster and more professional.

To start [download the latest PyCharm version](https://www.jetbrains.com/pycharm/download), connect your GitHub or GitLab or booth accounts and clone an existing repository.

## Connect GitLab/GitHub - ssh key
In PyCharm, open `Settings/Preferences -> Version Control -> Subversion -> SSH` and add the path to your `Private Key`.
Add your public key to GitHub or GitLab via the webpage. Follow the links for
[GitLab](https://docs.gitlab.com/ee/ssh/#add-an-ssh-key-to-your-gitlab-account) or
[GitHub](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).

## Connect GitLab with https token
First you have to install the Gitlab Plugin:
1. In PyCharm, open `Settings/Preferences -> Plugins` ([official Plugins doc](https://www.jetbrains.com/help/pycharm/managing-plugins.html)).
2. Make sure to select `Marketplace`, search for `GitLab Projects`([plugin homepage](https://plugins.jetbrains.com/plugin/14110-gitlab-projects-2020)) and install it. 
3. Restart PyCharm - You will be prompted usually.
4. [And add a new GitLab Server](#Add-a-new-GitLab-Server)

### Add a new GitLab Server
1. Open `Settings/Preferences -> Version Control -> GitLab`, click `Add new GitLab Server` and fill in:
2. GitLab UI Server Url: https://gitlab.lrz.de/
3. GitLab Personal Access Token: [Create a new token](https://gitlab.lrz.de/-/profile/personal_access_tokens) and make sure you select `api`.
   1. If the link doesn't work. On [gitlab.lrz.de](https://gitlab.lrz.de): `'Avatar' (upper right corner) -> Edit profil -> Access Tokens`
4. Preferred checkout method: `HTTPS`
5. Press apply and ok, now you are set to go.

## Connect GitHub with https token
The steps and logic is nearly the same as in the [GitLab-https-Token](#Connect-GitLab-with-https-token) section.
Here the official PyCharm guid to [register an existing account](https://www.jetbrains.com/help/pycharm/github.html#register-existing-account). If you don't have an GitHub account, create one first.
