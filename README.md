# Useful scripts
In this repository I will store all scripts that I use to simplify my life

## Kodi Addon
For watching CZ and SK Tipsport hockey matches I recommend **Tipsport ELH** addon from [**KODI CZ/SK**](http://kodi-czsk.github.io/repository/) repository. You don't need to worry about playlists and other staff. Just start the addon and select match. For Kodi 17+ is necessary to enable *RTMP Input* Add-on and *InputStream Adaptive* Add-on in *VideoPlayer InputStream* section. If you can't see *VideoPlayer InputStream* section, you have to install new version of Kodi on Windows or install it manually on Linux with `sudo apt-get install kodi-inputstream-adaptive kodi-inputstream-rtmp` command.

## Deprecated
### Playlist Generator
Scripts to generate .strm file with sports stream from some sites. I use it to play these streams on [Kodi](https://kodi.tv). For Kodi 17+ is necessary to enable RTMP Input Add-on and InputStream Adaptive Add-on in VideoPlayer InputStream section. Scripts were made for **study purposes** only and I **do not** guide anyone to disrespect site rules.

Usually I use [Requests](http://docs.python-requests.org/en/master/) library for HTTP communication. Instructions for [install](http://docs.python-requests.org/en/master/user/install/) this library.

#### [Tipsport Playlist Generator](tpg.py)
For now it can generate only ELH (Extraliga ledního hokeje) streams.

Before start you have to fill credentials to **your** tipsport.cz account in tpg.py:
```
credentials = ('user', 'password')
```
##### Using:
Start selector of available streams
```
tpg.py > playlist.strm
```
or generate playlist from specific URL
```
tpg.py URL > playlist.strm
```
##### Update:
You can check if a new version exist on GitHub by typing
```
tpg.py -c
```
and update script by following command
```
tpg.py -u
```

#### [Hokejka Playlist Generator](hpg.py)
Get stream from [hokej.cz](http://www.hokej.cz/hokejka/tv) site.
##### Using:
Start selector of available streams
```
hpg.py > playlist.strm
```
