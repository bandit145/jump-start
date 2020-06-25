import argparse
import jump_start.src.utils as utils
import jump_start.src.operating_systems as operating_systems
from jump_start.src.infrastructure import DNSMasq, Http
import logging
import time
import docker
import os
import sys
import yaml
import atexit


REQUIRED_CONFIG_KEYS = [
    'os',
    'os_config',
    'rsync_mirror',
    'hosts',
    'subnet',
    'install_file_template',
]


def get_args():
    parser = argparse.ArgumentParser(description='for bootstraping and deploying physical nodes on the same local network')
    parser.add_argument('-p,', '--phases', help='phases of jump_start to run', default='cache,network,config')
    parser.add_argument('-c', '--config', help='config file path', default='jump_start.yml')
    parser.add_argument('--cache-path', help='cache path for os mirros', default='/home/{0}/jump-start/.cache/'.format(os.getenv('USER')))
    parser.add_argument('--log-level', help='logging level', default='info', choices=['info', 'debug'])
    parser.add_argument('--listen-port', help='port to listen on for callbacks', default=8080)
    parser.add_argument('-i', '--interface', help='inerface name to listen on', required=True)
    parser.add_argument('-t', '--timeout', help='timeout of waiting for callbacks', default=1800)
    return parser.parse_args()


def read_config(path):
    # TODO: implement Output module
    try:
        with open(path, 'r') as config_file:
            config = yaml.load(config_file, )
        for item in REQUIRED_CONFIG_KEYS:
            if item not in config.keys():
                print('missing config keys', item)
                sys.exit(1)
        return config
    except yaml.YamlError as error:
        # todo: implement Output module
        print('yaml error', error)
        sys.exit(1)


def get_os_obj(os_name, os_config):
    if not hasattr(operating_systems, os_name):
        print(os_name, 'does not exist', file=sys.stderr)
        sys.exit(1)
    return getattr(operating_systems, os_name)(**os_config)


# remove firewall holes and shut off all containers
def clean_environment(client):
    [x.remove(force=True) for x in client.containers.list()]


def wait_for_callbacks(hosts, port, timeout):
    callback_listener = utils.Listener(('', port), handler_class=utils.ListenerRequestHandle)
    start_time = time.time()
    cur_time = start_time
    while cur_time - start_time < timeout or len(callback_listener.hosts) != len(hosts):
        callback_listener.handle_request()
        cur_time = time.time()
    return callback_listener.hosts


def main():
    docker_client = docker.from_env()
    # register docker cleanup for exit
    atexit.register(clean_environment, (docker_client,))
    utils.prep_local()
    args = get_args()
    logging.basicConfig({'level': getattr(logging, args.log_level).upper()})
    output = utils.output(logging)
    config = read_config(args.config)
    # configure os and cache things
    os_obj = get_os_obj(config['os'], config['os_config'])
    os_obj.download_repo(args.cache_path, config['rsync_mirror'])
    # deploy containers
    dnsmasq = DNSMasq(output, docker_client, {'dhcp_subet': config['subnet']})
    httpd = Http(output, docker_client)
    dnsmasq.run()
    httpd.run()
    # wait for responsese
    hosts = [x['hostname'] for x in config['hosts']]
    callback_data = wait_for_callbacks(hosts, args.port, args.timeout)

    # run ansible config
