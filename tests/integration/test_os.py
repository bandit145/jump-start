from jump_start.src.operating_systems import CentOS
import shutil
import os
import atexit


def cleanup():
    shutil.rmtree('/tmp/os_test/')


if not os.getenv('NO_CLEANUP'):
    atexit.register(cleanup)


def test_centos():
    centos = CentOS(8)
    os.mkdir('/tmp/os_test/')
    centos.download_repo('/tmp/os_test/', 'tests/integration/rsync_copy/')
    assert 'test.txt' in os.listdir(path='/tmp/os_test/centos/8/')
