# Overview

This is a small Python-based tool for saving your Spotify playlists (and, optionally, your saved songs) as [xspf](https://www.xspf.org/) files, allowing you share them and/or import them into other software.

This is a fork of another repository that used the OAuth tokens previously available from Spotify's developer dashboard for testing. Since Spotify removed that functionality, I modified the code to use a client key and secret key from an apps created on the [Spotify developer dashboard](https://developer.spotify.com/dashboard). This process is a little bit more involved to get running, but not too bad.

# Usage
## Spotify app setup
1. Navigate to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) in your browser.
2. Log into your Spotify account.
3. Click _Create App_ if you haven't already created one.
4. Enter a name and description for your app.
5. In the redirect URIs section, enter `https://www.example.com/`. Note: if you want to use another redirect URI, you will have to modify the `REDIRECT\_URI` variable in `main.py`.
6. Check the checkbox for `Web API`, sign your soul away to your music overlords and click Save.
7. Click on the app you just created in the Dashboard, then click Settings.
8. Click on the User Management tab. Then, enter your full name and the email address associated with your Spotify account and click Add User.
9. Then, go back to Basic Information. Here, your can find your Client ID and Client Secret behind the link `View client secret`.
10. Enter these values into the terminal when asked in the next steps.

Security note: your client secret, as the name implies, should not be shared with anyone! Anyone with access to it will be able to access the Spotify API through your user. This app won't share your key with anyone but Spotify, but do be mindful with dealing with API keys like this.

After your are done with using this tool, you may decide to delete your app in the Spotify Developer Dashboard to secure yourself. You have been warned.

## Python setup
1. If you haven't already, be sure you have installed Python3 on your system.
3. Download or clone this repository, for example via the green `Code` button on Github. (You may need the extract a .zip file)
4. Open a terminal/command line window and navigate to the directory the `main.py` file resides in.
5. Then, enter these commands, one at a time:
``` 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
6. If everything has gone as it should, you should be greeted by a prompt asking you for your client ID. This is where you will use the credentials obtained in the last section.
7. If this is the first time you're running the script, it should open a browser where you will need to authorize your app to access your Spotify account.
8. After authorizing, you will be redirected to `https://example.org/callback?code=somereallylongcodehere`. Copy the URL into the console when prompted.
8. After authourizing the app, the script should start outputting your playlists to `~/Playlists` (on Windows: `C:\Users\YOUR USERNAME\Playlists`). You can change this directory in main.py if you wish.
