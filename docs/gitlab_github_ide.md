# Github 
fds

# Gitlab

Search Plugins in PyCharm’s Settings menu. Then, search for GitLab Projects and install it.

You will be prompted to restart PyCharm.

Now, once PyCharm is re-loaded, go to Version Control --> GitLab in the Settings menu.

Enter the URL https://gitlab.lrz.de/ in GitLab Server Url.

Now you have to fill in the GitLab API Key. To do this you have to paste in your personal access token provided by GitLab. If you do not know it, simply log into your GitLab account, go to Preferences -> access tokens.

Simply create a new one (make sure you select for api). Copy the generated token key and paste in the respective settings field in PyCharm as mentioned earlier.

Set preferred checkout method to HTTPS.

Press apply and ok, now you are set to go.

In order to open the mctl repo, go to git -> Clone... -> Enter the url git@gitlab.lrz.de:strawb/mctl.git


