from jump_start.src.exceptions import ConfigException
from docker.errors import ContainerError
import os


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
        self.mnt_vol = '/home/' + os.getenv('USER') + '/.jump-start/' + type(self).__name__.lower()

    def create_volume(self):
        if not os.path.isdir(self.mnt_vol):
            os.mkdir(self.mnt_vol)
        self.volumes = {self.mnt_vol: {'bind': list(self.config['ContainerConfig']['Volumes'].keys())[0], 'mode': 'Z'}}

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
        except ContainerError as error:
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

    def __init__(self, output, client, dhcp_config):
        self.dhcp_config = dhcp_config
        super().__init__(output, DNSMasq.cont_name, client)

    def generate_pxelinux(self, boot_append):
        return '''default vesamenu.c32
        timout 30
        label os_install
            menu label ^install system
            kernel vmlinuz
            append initrd=initrd.img {0}
        '''.format(boot_append)

    def generate_config(self, boot_append):
        config_file = ''
        # global options
        # config_file += 'domain={0}\n'.format(self.dns_config['domain'])
        config_file += 'no-hosts\n'
        config_file += 'enable-tftp\n'
        config_file += 'dhcp-boot=pxelinux.0\n'
        config_file += 'tftp-root=/etc/dnsmasq/tftp/\n'
        # pxe boot file
        config_file += 'dhcp-boot=/tftp/pxelinux.0'
        # dhcp settings
        for item in self.dhcp_config['dhcp-range']:
            config_file += 'dhcp-range={0}\n'.format(item)
        for item in self.dhcp_config['dhcp-option']:
            config_file += 'dhcp-option={0}\n'.format(item)
        # dns settings
        if not os.path.exits(self.mnt_vol + '/tftp/'):
            os.mkdir(self.mnt_vol + '/tftp/')
        with open(self.mnt_vol + 'dnsmasq.conf') as file:
            file.write(config_file)
        with open(self.mnt_vol + '/tftp/pxelinux.0') as pxelinux:
            pxelinux.write(self.generate_config(boot_append))

    def check_config(self):
        self.output.debug('checking dhcp confg')
        self.output.debug('DHCP volumes {0}'.format(str(self.volumes)))
        output = self.client.containers.run(self.cont_name, '/usr/sbin/dnsmasq -d /etc/dnsmasq/dnsmasq.conf --test')
        self.output.debug('DHCP config check output:\n{0}'.format(output))


class Http(InfraCont):
    cont_name = 'quay.io/bandit145/apache'

    def __init__(self, output, client):
        super().__init__(output, Http.cont_name, client)
