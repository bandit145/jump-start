from abc import ABC, abstractmethod, abstractproperty

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
	ports = None

	def __init__(self, output, cont_name, client):
		self.cont_name, self.tag = cont_name.split(':')
		# docker client
		self.client = client
		self.output = output

	def configure(self): pass

	def pull(self):
		self.image = self.client.images.pull(self.cont_name, tag=self.tag)
		cont_config = self.client.api.inspect_image(self.image.id)
		self.output.debug('container config: {0}'.format(cont_config))
		self.volumes = cont_config['ContainerConfig']['Volumes']
		self.ports = cont_configp['ContainerConfig']['ExposedPorts']

	def start(self):
		if not self.container:
			self.container = self.client.containers.run(self.cont_name, detach=True)

	def stop(self):
		if self.container:
			self.container.remove(force=True)


class DNSContainer(InfraCont):

	def __init__(self, output, cont_name, client):
		super().__init__(output, cont_name, client)