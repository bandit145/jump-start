import os
import subprocess
import shutil
from jump_start.src.exceptions import RequirementMissing, abstractmethod
from abc import ABC


class OperatingSystem(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def download_repo(self, path, rsync_endpoint):
        pass


class CentOS(OperatingSystem):

    def __init__(self, **kwargs):
        self.version = kwargs['version']

    def download_repo(self, path, rsync_endpoint):
        if not shutil.which('rsync'):
            raise RequirementMissing
        centos_repo = '{0}/{1}'.format(path, type(self).__name__.lower())
        if not os.path.exists(centos_repo):
            os.mkdir(centos_repo)
        if not os.path.exists('{0}/{1}'.format(centos_repo, self.version)):
            os.mkdir('{0}/{1}'.format(centos_repo, self.version))
        subprocess.run('rsync -r --info=progress2 {0} {1}/{2}'.format(rsync_endpoint, centos_repo, self.version).split(' '), check=True)
