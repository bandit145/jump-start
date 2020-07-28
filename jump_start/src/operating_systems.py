import os
import subprocess
import shutil
from jump_start.src.exceptions import RequirementMissing, ConfigException
from jinja2 import Environment
from abc import ABC, abstractmethod


class OperatingSystem(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def download_repo(self, path, rsync_endpoint):
        pass

    @abstractmethod
    def generate_install_files(self, path, config):
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

    def generate_install_files(self, path, config):
        env = Environment()
        if not os.path.exists('{0}/install'.format(path)):
            os.mkdir('{0}/install'.format(path))
        for host in config['hosts']:
            if 'install_file_template' in host.keys():
                with open('{0}/install/{1}.ks'.format(path, host['hostname']), 'w') as install_file:
                    with open(host['install_file_template'], 'r') as install_template:
                        install_file.write(env.from_string(install_template.read()).render(**host))
            elif 'install_file_template' in config.keys():
                with open('{0}/install/{1}.ks'.format(path, host['hostname']), 'w') as install_file:
                    with open(config['install_file_template'], 'r') as install_template:
                        install_file.write(env.from_string(install_template.read()).render(**host))
            else:
                raise ConfigException('Missing install_file_template for {0} and not defined globally!'.format(host['hostname']))
