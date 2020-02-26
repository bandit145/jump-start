from jump_start.src.exceptions import ConfigException
import jump_start.src.data as data
from jinja2 import Environment, BaseLoader
import dns.zone
import dns.exception
import dns.name
import dns.rdatatype
import dns.rdataclass
import dns.zone
import docker
import dns
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

    def generate_config(self): pass

    def check_config(self): pass

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


class DHCPContainer(InfraCont):

    def __init__(self, output, cont_name, client, dhcp_config):
        self.dhcp_config = dhcp_config
        super().__init__(output, cont_name, client)

    def generate_config(self):
        with open(self.mnt_vol + '/kea-dhcp4.conf', 'w') as cont_file:
            json.dump(self.dhcp_config, cont_file)

    def check_config(self):
        self.output.debug('checking dhcp confg')
        self.output.debug('DHCP volumes ' + str(self.volumes))
        output = self.client.containers.run(self.cont_name, '/usr/sbin/kea-dhcp4 -t ' + self.volumes[self.mnt_vol]['bind'] + '/kea-dhcp4.conf', volumes=self.volumes, stderr=True, remove=True, detach=True)
        self.output.debug(output)



class DNSContainer(InfraCont):

    def __init__(self, output, cont_name, client, dns_zone, dns_config=None):
        self.dns_zone = dns_zone
        self.dns_config = dns_config
        
        if dns_config:
            self.dns_config = dns_config
        super().__init__(output, cont_name, client)

    def generate_config(self):
        template = Environment(loader=BaseLoader).from_string(data.named_config)
        with open(self.mnt_vol + '/named.conf', 'w') as named_conf:
            named_conf.write(template.render(isc_config=self.dns_config))
        os.chmod(self.mnt_vol + '/named.conf', 0o777)

        zone = dns.zone.Zone(dns.name.from_text(self.dns_zone['name']))
        # create soa
        soa_dataset = zone.find_rdataset(self.dns_zone['name'], dns.rdatatype.SOA, create=True)
        soa_rdata = dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, self.dns_zone['master_name'] + ' ' + self.dns_zone['responsible_name'] + ' 0' + ' ' + str(self.dns_zone['refresh']) + ' ' + str(self.dns_zone['retry']) + ' ' + str(self.dns_zone['expire']) + ' 0')
        soa_dataset.add(soa_rdata, self.dns_zone['ttl'])
        for record in self.dns_zone['records']:
            rdtype = dns.rdatatype.from_text(record['type'].upper())
            record_data = dns.rdata.from_text(dns.rdataclass.IN, rdtype, ' '.join(record['data']))
            new_rec = zone.get_rdataset(record['name'], rdtype, create=True)
            if 'ttl' in record.keys():
                new_rec.add(record_data, record['ttl'])
            else:
                new_rec.add(record_data, self.dns_zone['ttl'])
        with open(self.mnt_vol + '/' + self.dns_zone['name'] + '.db', 'w') as zone_conf:
            zone.to_file(zone_conf)

