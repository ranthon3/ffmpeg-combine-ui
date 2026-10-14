"""File preparation and the demonstration shell command."""

from pathlib import Path
import shutil
import subprocess


COMMAND = "echo hi; sleep 2; cat /tmp/combined_paths.txt"


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


def combine_files(paths):
    prepare_files(paths)
    try:
        result = subprocess.run(
            COMMAND, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, check=False,
        )
        return result.stdout, result.returncode
    finally:
        for number in range(1, 4):
            (Path('/tmp') / f'file{number}.mp4').unlink(missing_ok=True)
