from jump_start.src.exceptions import ConfigException
from docker.errors import ContainerError
from jinja2 import Environment
import subprocess
import ipaddress
import os


class InfraCont():
    image = None
    container = None
    volumes = None
    config = None
    ports = {}
    labels = {'app':'jump-start'}

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

    def inspect(self):
        self.image = self.client.images.get(self.cont_name)
        self.config = self.client.api.inspect_image(self.image.id)
        self.output.debug('container config: {0}'.format(self.config))
        for port in self.config['ContainerConfig']['ExposedPorts'].keys():
            self.ports[port] = int(port.split('/')[0])

    def run(self, pull=True):
        if pull:
            self.pull()
        self.inspect()
        self.create_volume()
        self.generate_config()
        try:
            self.check_config()
        except ContainerError as error:
            raise ConfigException(error)
        self.start()

    def pull(self):
        self.image = self.client.images.pull(self.cont_name, tag=self.tag)

    def start(self):
        if not self.container:
            self.output.debug('starting container ' + self.cont_name)
            self.container = self.client.containers.run(self.cont_name, detach=True, ports=self.ports, volumes=self.volumes, labels=self.labels, publish_all_ports=True)

    def stop(self):
        if self.container:
            self.container.remove(force=True)


class DNSMasq(InfraCont):

    cont_name = 'quay.io/bandit145/dnsmasq:latest'

    def __init__(self, output, client, config, interface):
        self.dhcp_subnet = config['subnet']
        self.hosts = config['hosts']
        self.jmp_config = config
        self.interface = interface
        self.env = Environment()
        super().__init__(output, DNSMasq.cont_name, client)

    def generate_pxelinux(self, boot_append):
        return '''default vesamenu.c32
        timout 30
        label os_install
            menu label ^install system
            kernel vmlinuz
            append initrd=initrd.img {0}
        '''.format(boot_append)

    def find_interface_address(self):
        proc = subprocess.run('ip a show dev {0} | grep / | awk \'NR>1{{print $2}}\''.format(self.interface), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        if proc.returncode != 0:
            raise ConfigException
        for item in str(proc.stdout).split('\n'):
            if 'fe80' not in item:
                return item.split('/')[0]

    def generate_install_files(self):
        for host in self.hosts:
            if 'boot_append' in self.jmp_config.keys():
                boot_append  = self.jmp_config['boot_append']
            else:
                boot_append = host['boot_append']
            host_tftp_path = '{0}/tftp/{1}'.format(self.mnt_vol, host['mac'].replace(':', '-'))
            if not os.path.exists(host_tftp_path):
                os.mkdir(host_tftp_path)
            with open('{0}/pxelinux.0'.format(host_tftp_path), 'w') as file:
                file.write(self.generate_pxelinux(self.env.from_string(boot_append).render(ip=self.find_interface_address() ,**host)))

    def generate_config(self):
        config_file = ''
        # global options
        # config_file += 'domain={0}\n'.format(self.dns_config['domain'])
        config_file += 'no-hosts\n'
        config_file += 'enable-tftp\n'
        config_file += 'dhcp-boot=pxelinux.0\n'
        config_file += 'tftp-root=/etc/dnsmasq/tftp/\n'
        # pxe boot file
        config_file += 'dhcp-boot=pxelinux.0\n'
        config_file += 'tftp-unique-root=mac\n'
        # dns settings
        if not os.path.exists(self.mnt_vol + '/tftp/'):
            os.mkdir(self.mnt_vol + '/tftp/')
        with open(self.mnt_vol + '/dnsmasq.conf', 'w') as file:
            file.write(config_file)
        self.generate_install_files()

    def check_config(self):
        self.output.debug('checking dhcp confg')
        self.output.debug('DHCP volumes {0}'.format(str(self.volumes)))
        output = self.client.containers.run(self.cont_name, '/usr/sbin/dnsmasq -d --conf-file=/etc/dnsmasq/dnsmasq.conf --test', auto_remove=True, labels=self.labels)
        self.output.debug('DHCP config check output:\n{0}'.format(output))


class Http(InfraCont):
    cont_name = 'quay.io/bandit145/apache:latest'

    def __init__(self, output, client):
        super().__init__(output, Http.cont_name, client)
