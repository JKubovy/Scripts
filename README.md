# Useful scripts
In this repository I will store all scripts that I use to simplify my life
## Playlist Generator
Scripts to generate .strm file with sports stream from some sites. I use it to play these streams on [Kodi](https://kodi.tv). Scripts were made for **study purposes** only and I **do not** guide anyone to disrespect site rules.

Usually I use [Requests](http://docs.python-requests.org/en/master/) library for HTTP communication. Instructions for [install](http://docs.python-requests.org/en/master/user/install/) this library.

### [Tipsport Playlist Generator](tpg.py)
For now it can generate only ELH (Extraliga ledního hokeje) streams.
#### Using:
Start selector of available streams
```
tpg.py > playlist.strm
```
or generate playlist from specific URL
```
tpg.py URL > playlist.strm
```

### [Hokejka Playlist Generator](hpg.py)
Get stream from [hokej.cz](http://www.hokej.cz/hokejka/tv) site.
#### Using:
Start selector of available streams
```
hpg.py > playlist.strm
```
