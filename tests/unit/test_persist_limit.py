from __future__ import absolute_import
import pytest
import os
import tempfile
import mozfile
import time

from mozregression.persist_limit import PersistLimit


class TempCreator(object):
    def __init__(self):
        self.tempdir = tempfile.mkdtemp()

    def list(self):
        return os.listdir(self.tempdir)

    def create_file(self, name, size, delay):
        fname = os.path.join(self.tempdir, name)
        with open(fname, 'wb') as f:
            f.write('a' * size)
        # equivalent to touch, but we apply a delay for the test
        atime = time.time() + delay
        os.utime(fname, (atime, atime))


@pytest.yield_fixture
def temp():
    tmp = TempCreator()
    yield tmp
    mozfile.remove(tmp.tempdir)


@pytest.mark.parametrize("size_limit,file_limit,files", [
    # limit_file is always respected
    (10, 5, "bcdef"),
    (10, 3, "def"),
    # if size_limit or file_limit is 0, nothing is removed
    (0, 5, "abcdef"),
    (5, 0, "abcdef"),
    # limit_size works
    (35, 1, "def"),
])
def test_persist_limit(temp, size_limit, file_limit, files):
    temp.create_file("a", 10, -6)
    temp.create_file("b", 10, -5)
    temp.create_file("c", 10, -4)
    temp.create_file("d", 10, -3)
    temp.create_file("e", 10, -2)
    temp.create_file("f", 10, -1)

    persist_limit = PersistLimit(size_limit, file_limit)
    persist_limit.register_dir_content(temp.tempdir)
    persist_limit.remove_old_files()

    assert ''.join(sorted(temp.list())) == ''.join(sorted(files))
