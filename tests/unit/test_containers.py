from jump_start.src.infrastructure import InfraCont
import docker
import logging
import atexit

TEST_CONTAINER_NAME = 'alpine:latest'

def cleanup():
	client = get_docker_client()
	[x.remove(force=True) for x in client.containers.list()]

#atexit.register(cleanup)


def get_docker_client():
	return docker.from_env()


def test_infracont():
	client = get_docker_client()
	infra_cont = InfraCont(logging, TEST_CONTAINER_NAME, client)

	infra_cont.pull()
	infra_cont.start()
	assert len(client.containers.list()) == 1
	infra_cont.stop()