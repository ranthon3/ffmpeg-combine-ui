"""Prepare, concatenate, encode, and clean up video files."""

from pathlib import Path
import codecs
import shutil
import subprocess


WORK_DIRECTORY = Path('/tmp')


def prepare_files(paths, destination=Path('/tmp')):
    """Remove old copies, copy existing selections, and write the concat list."""
    destination = Path(destination)
    paths = list(paths)
    if len(paths) not in (2, 3):
        raise ValueError('Expected two or three file selections.')
    targets = [destination / f'file{number}.mp4' for number in range(1, 4)]
    for target in targets:
        target.unlink(missing_ok=True)
    entries = []
    for source, target in zip(paths, targets):
        if source and Path(source).is_file():
            shutil.copyfile(source, target)
            entries.append(f"file '{target.name}'\n")
    (destination / 'mylist.txt').write_text(''.join(entries), encoding='utf-8')


def run_command(command, on_output=None):
    """Run an argument list and stream merged stdout/stderr."""
    chunks = []
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    with subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ) as process:
        while data := process.stdout.read1(4096):
            text = decoder.decode(data)
            if text:
                chunks.append(text)
                if on_output is not None:
                    on_output(text)
        tail = decoder.decode(b'', final=True)
        if tail:
            chunks.append(tail)
            if on_output is not None:
                on_output(tail)
        status = process.wait()
    return ''.join(chunks), status


def combine_files(paths, on_output=None):
    paths = list(paths)
    if not paths or not paths[0] or not Path(paths[0]).is_file():
        raise ValueError('Choose an existing first MP4 file.')
    source = Path(paths[0]).resolve()
    output_path = source.with_name(f'{source.stem}_joined.mkv')
    work = WORK_DIRECTORY
    joined_mp4 = work / 'joined.mp4'
    joined720_mp4 = work / 'joined720.mp4'
    joined_mkv = work / 'joined.mkv'
    working_files = [work / f'file{n}.mp4' for n in range(1, 4)]
    working_files.extend([joined_mp4, joined720_mp4, joined_mkv])
    commands = [
        ['ffmpeg', '-f', 'concat', '-i', str(work / 'mylist.txt'),
         '-c', 'copy', str(joined_mp4)],
        ['ffmpeg', '-i', str(joined_mp4), '-filter:v',
         'scale=trunc(oh*a/2)*2:720', '-c:a', 'copy', str(joined720_mp4)],
        ['HandBrakeCLI', '-i', str(joined720_mp4), '-e', 'x264', '-q', '26',
         '--encoder-preset', 'slow', '--aencoder', 'copy',
         '--audio-copy-mask', 'ac3,dts,dtshd', '--custom-anamorphic',
         '--keep-display-aspect', '-O', '-Neng', '-s', 'none',
         '-o', str(joined_mkv)],
        ['mv', '--', str(joined_mkv), str(output_path)],
    ]
    output = []
    try:
        joined_mp4.unlink(missing_ok=True)
        joined720_mp4.unlink(missing_ok=True)
        joined_mkv.unlink(missing_ok=True)
        prepare_files(paths, work)
        for command in commands:
            text, status = run_command(command, on_output)
            output.append(text)
            if status != 0:
                return ''.join(output), status
        return ''.join(output), 0
    finally:
        for target in working_files:
            target.unlink(missing_ok=True)
