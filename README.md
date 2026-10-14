# FFmpeg Combine UI

A small Python application using GTK 3 for GNOME. It has three editable file
paths with Browse dialogs, an output area, and a Combine button.

On Debian/Ubuntu, install `python3-gi`, `gir1.2-gtk-3.0`, `ffmpeg`, and `handbrake-cli`, then run on a desktop:

```sh
/usr/bin/python3 app.py
```

Combine deletes `/tmp/file1.mp4`, `/tmp/file2.mp4`, and `/tmp/file3.mp4` before
copying existing selected files to those names. Only successfully copied files
are listed in `/tmp/mylist.txt`; leaving the third selection empty omits it.
These fixed paths are shared, so run only one instance at a time and avoid
selecting the destination files themselves as inputs.

Combine runs these steps, advancing only when the previous exit status is zero:

1. Concatenate the selected videos with FFmpeg into `/tmp/joined.mp4`.
2. Scale to 720 pixels high with FFmpeg using `scale=trunc(oh*a/2)*2:720`,
   copying the audio into `/tmp/joined720.mp4`.
3. Encode `/tmp/joined720.mp4` with HandBrakeCLI using x264, quality 26, the slow preset, and the
   requested audio, anamorphic, subtitle, and language options into `/tmp/joined.mkv`.
4. Move the MKV into the first selected file's directory. For example,
   `/videos/holiday.mp4` produces `/videos/holiday_joined.mkv`.
   An existing output with that name is replaced.

The output area streams stdout and stderr, then displays the exit status.
After success or failure, the three temporary MP4 copies, `joined.mp4`, `joined720.mp4`, and
`joined.mkv` are deleted. Other files in `/tmp` are left alone. `mylist.txt` is
retained. The first file must exist; the third file remains optional.

Run the file-preparation tests with:

```sh
/usr/bin/python3 -m unittest discover -s tests -v
```
