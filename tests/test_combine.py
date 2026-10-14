from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

from combine import combine_files, prepare_files


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
    def test_cleanup_after_success_failure_and_launch_error(self):
        for status in (0, 1, None):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                targets = [root / f'file{n}.mp4' for n in range(1, 4)]
                for target in targets:
                    target.write_bytes(b'video')
                unrelated = root / 'other.mp4'
                unrelated.write_bytes(b'keep')

                def run_command(*args, **kwargs):
                    self.assertTrue(all(target.exists() for target in targets))
                    if status is None:
                        raise OSError('Cannot launch shell')
                    return subprocess.CompletedProcess(args[0], status, stdout='output')

                with patch('combine.prepare_files'), patch('combine.Path', return_value=root), \
                        patch('combine.subprocess.run', side_effect=run_command):
                    if status is None:
                        with self.assertRaises(OSError):
                            combine_files(['a', 'b'])
                    else:
                        self.assertEqual(combine_files(['a', 'b']), ('output', status))
                self.assertTrue(all(not target.exists() for target in targets))
                self.assertEqual(unrelated.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
