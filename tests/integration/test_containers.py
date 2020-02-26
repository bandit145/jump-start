from jump_start.src.infrastructure import InfraCont, DHCPContainer, DNSContainer
import jump_start.src.utils as utils 
import docker
import logging
import atexit
import os
import shutil

TEST_CONTAINER_NAME = 'quay.io/bandit145/test-alpine:latest'
TEST_DHCP_CONTAINER = 'quay.io/bandit145/isc-kea4:latest'
TEST_DNS_CONTAINER = 'quay.io/bandit145/isc-bind:latest'

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


def test_dhcpcont():
	config = {
		'Dhcp4':{
			'interfaces-config': {
				'interfaces': []
			},
			'control-socket': {
				'socket-type': 'unix',
				'socket-name': '/run/kea/kea-dhcp4-ctrl.sock'
			},
			'lease-database': {
				'type': 'memfile',
				'lfc-interval': 3600
			},
			'subnet4': [
				{
					'subnet': '192.0.2.0/24',
					"pools": [ { "pool": "192.0.2.1 - 192.0.2.200" } ]
				}
			]
		}
	}
	client = get_docker_client()
	dhcp_cont = DHCPContainer(logging, TEST_DHCP_CONTAINER, client, config)
	dhcp_cont.run()
	assert 'kea-dhcp4' in dhcp_cont.container.exec_run('ps')[1].decode()
	dhcp_cont.stop()


def test_dnscont():
	zone = {
		'name': 'testzone.test',
		'master_name': 'ns1.testzone.test',
		'responsible_name': 'thing@thing',
		'refresh': 0,
		'retry': 0,
		'expire': 0,
		'ttl': 1,

		'records': [
			{'type': 'a', 'data': ['192.168.1.1'], 'name': 'test'}
		]

	}
	config = {
		'zones': [
			{
				'name': 'testzone.test',
				'type': 'master'
			}
		]

	}
	client = get_docker_client()
	dns_cont = DNSContainer(logging, TEST_DNS_CONTAINER, client, zone, config)
	dns_cont.run()
	assert 'bind' in dns_cont.container.exec_run('ps')[1].decode()
	dns_cont.stop()
