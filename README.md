# Useful scripts
In this repository I will store all scripts that I use to simplify my life

## Rensub
Script renaming subtitles to match video filenames. Using module Guessit to compare filenames to be sure that renaming file belongs to specific video file. Filename has to contain name and eventually season and episode number. (*e.g. Counterpart.S01E04.1080p.HEVC.x265-MeGusta.mkv*)

To rename subtitles in current folder:
```
rensub
```

To rename subtitles recursively in given **Folder** with debug information:
```
rensub -r --verbose Folder
```

It is possible to use complex folder matching
```
rensub [PH]*_movie
```
matches all folder starting with letter **P** or **H** and ending with **_movie**

All possible script argument can be found with ```rensub --help```