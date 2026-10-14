from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

from combine import combine_files, prepare_files, run_command


class PrepareFilesTest(unittest.TestCase):
    def test_two_files_remove_stale_third_and_write_list(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / 'a.mp4', root / 'b.mp4']
            for index, source in enumerate(sources):
                source.write_bytes(bytes([index]))
            for number in range(1, 4):
                (root / f'file{number}.mp4').write_bytes(b'old')
            prepare_files([str(sources[0]), str(sources[1]), ''], root)
            self.assertEqual((root / 'file1.mp4').read_bytes(), b'\x00')
            self.assertEqual((root / 'file2.mp4').read_bytes(), b'\x01')
            self.assertFalse((root / 'file3.mp4').exists())
            self.assertEqual((root / 'mylist.txt').read_text(),
                             "file 'file1.mp4'\nfile 'file2.mp4'\n")
            prepare_files([str(sources[0]), str(sources[1])], root)
            self.assertEqual((root / 'mylist.txt').read_text(),
                             "file 'file1.mp4'\nfile 'file2.mp4'\n")
            self.assertFalse((root / 'file3.mp4').exists())

    def test_three_files_and_missing_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.mp4'
            source.write_bytes(b'video')
            prepare_files([str(source)] * 3, root)
            self.assertEqual((root / 'mylist.txt').read_text(),
                             ''.join(f"file 'file{n}.mp4'\n" for n in range(1, 4)))
            prepare_files([str(source), str(root / 'missing'), ''], root)
            self.assertEqual((root / 'mylist.txt').read_text(), "file 'file1.mp4'\n")
            self.assertFalse((root / 'file2.mp4').exists())


class CombineFilesTest(unittest.TestCase):
    def test_streams_partial_output_before_command_finishes(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'finished'
            received = []

            def on_output(text):
                received.append(text)
                if 'hi' in text:
                    self.assertFalse(marker.exists())

            script = ("import time; from pathlib import Path; "
                      "print('hi', end='', flush=True); time.sleep(0.3); "
                      f"Path({str(marker)!r}).touch(); print('done', end='', flush=True)")
            output, status = run_command([sys.executable, '-c', script], on_output)
            self.assertEqual(output, 'hidone')
            self.assertEqual(''.join(received), output)
            self.assertEqual(status, 0)
            self.assertTrue(marker.exists())

    def test_pipeline_stops_on_failure_and_always_cleans_up(self):
        for failing_step in (None, 0, 1, 2, 3, 'launch'):
            with self.subTest(failing_step=failing_step), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                work = root / 'work'
                work.mkdir()
                source = root / 'first video.mp4'
                source.write_bytes(b'video')
                unrelated = work / 'other.mp4'
                unrelated.write_bytes(b'keep')
                calls = []
                received = []

                def execute(command, on_output):
                    step = len(calls)
                    calls.append(command)
                    if failing_step == 'launch':
                        raise FileNotFoundError('Missing executable')
                    text = f'step {step}'
                    on_output(text)
                    if step == failing_step:
                        return text, 7
                    if step == 0:
                        (work / 'joined.mp4').write_bytes(b'joined')
                    elif step == 1:
                        (work / 'joined720.mp4').write_bytes(b'scaled')
                    elif step == 2:
                        (work / 'joined.mkv').write_bytes(b'encoded')
                    else:
                        Path(command[2]).replace(command[3])
                    return text, 0

                with patch('combine.WORK_DIRECTORY', work), \
                        patch('combine.run_command', side_effect=execute):
                    if failing_step == 'launch':
                        with self.assertRaises(FileNotFoundError):
                            combine_files([str(source), str(source)], received.append)
                    else:
                        output, status = combine_files([str(source), str(source)], received.append)
                        self.assertEqual(status, 0 if failing_step is None else 7)
                        self.assertEqual(output, ''.join(received))
                expected_calls = 4 if failing_step is None else (1 if failing_step == 'launch' else failing_step + 1)
                self.assertEqual(len(calls), expected_calls)
                self.assertEqual(calls[0][0], 'ffmpeg')
                if len(calls) > 1:
                    self.assertEqual(calls[1], [
                        'ffmpeg', '-i', str(work / 'joined.mp4'), '-filter:v',
                        'scale=trunc(oh*a/2)*2:720', '-c:a', 'copy',
                        str(work / 'joined720.mp4'),
                    ])
                if len(calls) > 2:
                    self.assertEqual(calls[2][0:3], [
                        'HandBrakeCLI', '-i', str(work / 'joined720.mp4'),
                    ])
                if failing_step is None:
                    self.assertEqual((root / 'first video_joined.mkv').read_bytes(), b'encoded')
                else:
                    self.assertFalse((root / 'first video_joined.mkv').exists())
                for name in ('file1.mp4', 'file2.mp4', 'file3.mp4', 'joined.mp4', 'joined720.mp4', 'joined.mkv'):
                    self.assertFalse((work / name).exists())
                self.assertEqual(source.read_bytes(), b'video')
                self.assertEqual(unrelated.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
