# FFmpeg Combine UI

A small Python application using GTK 3 for GNOME. It has three editable file
paths with Browse dialogs, an output area, and a Combine button.

On Debian/Ubuntu, install `python3-gi` and `gir1.2-gtk-3.0`, then run on a desktop:

```sh
/usr/bin/python3 app.py
```

Combine deletes `/tmp/file1.mp4`, `/tmp/file2.mp4`, and `/tmp/file3.mp4` before
copying existing selected files to those names. Only successfully copied files
are listed in `/tmp/mylist.txt`; leaving the third selection empty omits it.
These fixed paths are shared, so run only one instance at a time and avoid
selecting the destination files themselves as inputs.

The demonstration command is exactly:

```sh
echo hi; sleep 2; cat /tmp/combined_paths.txt
```

The output area streams stdout and stderr as the command produces them, then
displays the exit status after completion.
After the command finishes, the three temporary MP4 copies are deleted,
regardless of its exit status. Other MP4 files in `/tmp` are left alone.
The application writes `mylist.txt`, not `combined_paths.txt`. Unless the latter
already exists, the command displays `hi` followed by a missing-file error.
This demonstration does not yet run FFmpeg or produce a combined video.

Run the file-preparation tests with:

```sh
/usr/bin/python3 -m unittest discover -s tests -v
```
