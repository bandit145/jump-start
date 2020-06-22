import os
import subprocess


class OperatingSystem:

    def __init__(self):
        pass

class CentOS(OperatingSystem):

    def __init__(self, version):
        self.version = version

    def download_repo(self, path, rsync_endpoint):
        centos_repo = '{0}/{1}'.format(path, type(self).__name__.lower())
        if not os.path.exists(centos_repo):
            os.mkdir(centos_repo)
        if not os.path.exists('{0}/{1}'.format(centos_repo, self.version)):
            os.mkdir('{0}/{1}'.format(centos_repo, self.version))
        proc = subprocess.run('rsync -r --info=progress2 {0} {1}/{2}'.format(rsync_endpoint, centos_repo, self.version).split(' '))