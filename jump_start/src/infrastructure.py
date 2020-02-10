from abc import ABC, abstractmethod, abstractproperty
import dns.zone
import dns
import os
import yaml
import json

# abstract base classes

class Repo(ABC):

	def __init__(self, repo_path):
		self.repo_path = repo_path

	@abstractmethod
	def sync_repo(self): pass


class InfraCont(ABC):
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

	@abstractmethod
	def generate_config(self): pass

	@abstractmethod
	def check_config(self): pass

	def run(self):
		self.pull()
		self.create_volume()
		self.generate_config()
		self.check_config()
		self.start()

	def pull(self):
		self.image = self.client.images.pull(self.cont_name, tag=self.tag)
		self.config = self.client.api.inspect_image(self.image.id)
		self.output.debug('container config: {0}'.format(self.config))
		for port in self.config['ContainerConfig']['ExposedPorts'].keys():
			self.ports[port] = int(port.split('/')[0])

	def start(self):
		if not self.container:
			self.container = self.client.containers.run(self.cont_name, detach=True, ports=self.ports, volumes=self.volumes)

	def stop(self):
		if self.container:
			self.container.remove(force=True)


class DHCPContainer(InfraCont):

	def __init__(self, output, cont_name, client):
		self.config = config
		super().__init__(output, cont_name, client)

	def generate_config(self):
		with open(self.mnt_vol + 'kea-dhcp4.conf', 'w') as cont_file:
			json.dump(self.config, cont_file)

	def check_config():
		output = self.client.containers.run(self.cont_name, '/usr/sbin/kea-dhcp4 -t -c ' + self.mnt_vol + '/kea-dhcp4.conf', volumes=self.volumes, stderr=True)
		self.output.debug(output)



class DNSContainer(InfraCont):

	dns_config = {
		'server':{},
		'zone':{}
	}

	def __init__(self, output, cont_name, client, dns_zone, dns_config=None):
		self.dns_zone = dns_zone
		
		if dns_config:
			self.dns_config = dns_config
		super().__init__(output, cont_name, client)

	def generate_config(self):
		with open(self.mnt_vol + '/nsd.conf', 'r') as nsd_conf:
			file.write(yaml.dump(self.dns_config))

