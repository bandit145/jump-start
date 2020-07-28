from jump_start.src.infrastructure import InfraCont
import jump_start.src.utils as utils
import docker
import logging
import atexit
import os
import shutil


def cleanup():
    client = get_docker_client()
    [x.remove(force=True) for x in client.containers.list()]
    if os.path.exists('/home/' + os.getenv('USER') + '/.jump-start'):
        shutil.rmtree('/home/' + os.getenv('USER') + '/.jump-start')


if not os.getenv('NO_CLEANUP'):
    atexit.register(cleanup)


def get_docker_client():
    return docker.from_env()


def test_jump_start_dir():
    utils.prep_local()
    assert os.path.exists('/home/' + os.getenv('USER') + '/.jump-start')


def test_infracont():
    client = get_docker_client()
    infra_cont = InfraCont(logging, 'quay.io/bandit145/dnsmasq:latest', client)
    infra_cont.pull()
    assert infra_cont.ports == {'67/udp': 67, '53/udp': 53, '69/udp': 69}
    infra_cont.create_volume()
    with open(infra_cont.mnt_vol + '/dnsmasq.conf', 'w') as dnsmasq_conf_file:
        dnsmasq_conf_file.write('')
    assert infra_cont.volumes == {'/home/phil/.jump-start/infracont': {'bind': '/etc/dnsmasq/', 'mode': 'Z'}}
    with open(infra_cont.mnt_vol + '/hello', 'w') as cont_file:
        cont_file.write('hi')
    assert os.path.exists(infra_cont.mnt_vol)
    infra_cont.start()
    assert 'hi' == infra_cont.container.exec_run('cat /etc/dnsmasq/hello')[1].decode()
    assert len(client.containers.list()) == 1
    infra_cont.stop()
