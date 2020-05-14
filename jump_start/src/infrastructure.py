from jump_start.src.exceptions import ConfigException
import jump_start.src.data as data
from jinja2 import Environment, BaseLoader
import docker
import os
import yaml
import json

class InfraCont():
    image = None
    container = None
    volumes = None
    config = None
    ports = {}

    def __init__(self, output, cont_name, client):
        self.cont_name, self.tag = cont_name.split(':')
        # docker client
        self.client = client
        self.output = output
        self.mnt_vol = '/home/'+ os.getenv('USER') + '/.jump-start/' + type(self).__name__.lower()

    def create_volume(self):
        if not os.path.isdir(self.mnt_vol):
            os.mkdir(self.mnt_vol)
        self.volumes = {self.mnt_vol: {'bind': list(self.config['ContainerConfig']['Volumes'].keys())[0], 'mode':'Z'}}

    def generate_config(self):
        pass

    def check_config(self):
        pass

    def run(self):
        self.pull()
        self.create_volume()
        self.generate_config()
        try:
            self.check_config()
        except docker.errors.ContainerError as error:
            raise ConfigException(error)
        self.start()

    def pull(self):
        self.image = self.client.images.pull(self.cont_name, tag=self.tag)
        self.config = self.client.api.inspect_image(self.image.id)
        self.output.debug('container config: {0}'.format(self.config))
        for port in self.config['ContainerConfig']['ExposedPorts'].keys():
            self.ports[port] = int(port.split('/')[0])

    def start(self):
        if not self.container:
            self.output.debug('starting container')
            self.container = self.client.containers.run(self.cont_name, detach=True, ports=self.ports, volumes=self.volumes)

    def stop(self):
        if self.container:
            self.container.remove(force=True)


class DNSMasq(InfraCont):

    cont_name = 'quay.io/bandit145/dnsmasq'

    def __init__(self, output, client, dhcp_config, dns_config, pxe_config):
        self.dhcp_config = dhcp_config
        self.dns_config = dns_config
        self.pxe_config = pxe_config
        super().__init__(output, DNSMasq.cont_name, client)

    def generate_config(self):
        config_file = ''
        #global options
        config_file += 'domain={0}\n'.format(dns_config['domain'])
        config_file += 'no-hosts\n'
        config_file += 'enable-tftp\n'
        config_file += 'tftp-root=/etc/dnsmasq/tftp/\n'
        #dhcp settings
        for key, value in dhcp_config:
            config_file += '{0}={1}\n'.format(key, value)
        #dns settings
        for key, vlaue in dns_config:
            config_file += '{0}={1}\n'.format(key, value)
        #pxe settings
        config_file += 'dhcp-boot={0}'.format(pxe_config['boot-file'])
        if not os.path.exits(self.mnt_vol + '/tftp/'):
            os.symlink(pxe_config['tftp_dir'], self.mnt_vol + '/tftp/', target_is_directory=True)
        with open(self.mnt_vol + 'dnsmasq.conf') as file:
            file.write(config_file)

    def check_config(self):
        self.output.debug('checking dhcp confg')
        self.output.debug('DHCP volumes {0}'.format(str(self.volumes)))
        output = self.client.containers.run(self.cont_name, '/usr/sbin/dnsmasq -d /etc/dnsmasq/dnsmasq.conf --test')
        self.output.debug('DHCP config check output:\n{0}'.format(output))


class Http(InfraCont):
    cont_name = 'quay.io/bandit145/apache'

    def __init__(self, output, http_config):
        self.http_config = http_config
        super().__init__(output, Http.cont_name, client)
    # TODO: add util configuration classes/functions to get certain OS/s, self configure edition
    def generate_config(self):
        pass
