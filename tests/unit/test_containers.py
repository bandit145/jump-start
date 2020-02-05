from jump_start.src.infrastructure import InfraCont
import jump_start.src.utils as utils 
import docker
import logging
import atexit
import os
import shutil

TEST_CONTAINER_NAME = 'quay.io/bandit145/test-alpine:latest'

def cleanup():
	client = get_docker_client()
	[x.remove(force=True) for x in client.containers.list()]
	if os.path.exists('/home/'+os.getenv('USER')+'/.jump-start'):
		shutil.rmtree('/home/'+os.getenv('USER')+'/.jump-start')

if not os.getenv('NO_CLEANUP'):
	atexit.register(cleanup)


def get_docker_client():
	return docker.from_env()


def test_jump_start_dir():
	utils.prep_local()
	assert os.path.exists('/home/'+os.getenv('USER')+'/.jump-start')


def test_infracont():
	client = get_docker_client()
	infra_cont = InfraCont(logging, TEST_CONTAINER_NAME, client)
	infra_cont.pull()
	assert infra_cont.ports == {'67/udp':67}
	infra_cont.create_volume()
	assert infra_cont.volumes == {'/home/'+os.getenv('USER')+'/.jump-start/infracont': {'bind':'/hi', 'mode':'Z'}}
	with open(infra_cont.mnt_vol + '/hello', 'w') as cont_file:
		cont_file.write('hi')
	assert os.path.exists(infra_cont.mnt_vol)
	infra_cont.start()
	assert 'hi' == infra_cont.container.exec_run('cat /hi/hello')[1].decode()
	assert len(client.containers.list()) == 1
	infra_cont.stop()