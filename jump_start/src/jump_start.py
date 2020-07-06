import argparse
import jump_start.src.utils as utils
import jump_start.src.operating_systems as operating_systems
from jump_start.src.infrastructure import DNSMasq, Http
import jump_start.src.config as jump_config
import jump_start.src.runners as runners
import logging
import time
import docker
import os
import sys
import yaml
import atexit


def get_args():
    parser = argparse.ArgumentParser(description='for bootstraping and deploying physical nodes on the same local network')
    parser.add_argument('-p,', '--phases', help='phases of jump_start to run', default='cache,network,config')
    parser.add_argument('-c', '--config', help='config file path', default='jump_start.yml')
    parser.add_argument('--cache-path', help='cache path for os mirros', default='/home/{0}/.jump-start/.cache/'.format(os.getenv('USER')))
    parser.add_argument('--log-level', help='logging level', default='info', choices=['info', 'debug'])
    parser.add_argument('--listen-port', help='port to listen on for callbacks', default=8080)
    parser.add_argument('--playbook', help='playbook name', default='playbook.yml')
    parser.add_argument('-i', '--interface', help='inerface name to listen on', required=True)
    parser.add_argument('-t', '--timeout', help='timeout of waiting for callbacks', default=1800)
    return parser.parse_args()


def read_config(path, output):
    # TODO: implement Output module
    try:
        with open(path, 'r') as config_file:
            config = yaml.load(config_file, )
        succeed, msg = jump_config.validate_config(config, jump_config.config_schema)
        if not succeed:
            output.error(msg)
        return config
    except yaml.YamlError as error:
        # todo: implement Output module
        output.print('yaml error', error)
        sys.exit(1)


def get_os_obj(os_name, os_config, output):
    if not hasattr(operating_systems, os_name):
        output.print(os_name, 'does not exist', file=sys.stderr)
        sys.exit(1)
    return getattr(operating_systems, os_name)(**os_config)


# shut off all containers
def clean_environment(client):
    [x.remove(force=True) for x in client.containers.list()]


def wait_for_callbacks(hosts, port, timeout):
    callback_listener = utils.Listener(('', port), handler_class=utils.ListenerRequestHandler)
    start_time = time.time()
    cur_time = start_time
    while cur_time - start_time < timeout or len(callback_listener.hosts) != len(hosts):
        callback_listener.handle_request()
        cur_time = time.time()
    return callback_listener.hosts


def main():
    inv_path = '/home/{0}/.jump-start/inv'.format(os.env('USER'))
    docker_client = docker.from_env()
    # register docker cleanup for exit
    atexit.register(clean_environment, (docker_client,))
    utils.prep_local()
    args = get_args()
    phases = args.phases.split(',')
    logging.basicConfig({'level': getattr(logging, args.log_level).upper()})
    output = utils.output(logging)
    config = read_config(args.config, output)
    # configure os and cache things
    if 'cache' in phases:
        os_obj = get_os_obj(config['os'], config['os_config'], output)
        output.print('Downloading OS...')
        os_obj.download_repo(args.cache_path, config['rsync_mirror'])
    # deploy containers
    if 'network' in phases:
        output.print('Creating containers...')
        dnsmasq = DNSMasq(output, docker_client, {'dhcp_subet': config['subnet']})
        httpd = Http(output, docker_client)
        dnsmasq.run()
        httpd.run()
        # wait for responsese
        output.print('Waiting for responses from hosts...')
        hosts = [x['hostname'] for x in config['hosts']]
        callback_data = wait_for_callbacks(hosts, args.port, args.timeout)
        inventory = ''
        for host in callback_data:
            inventory += '{0} hostname={1}\n'.format(host['address'], host['hostname'])
        with open(inv_path, 'w') as inv_file:
            inv_file.write(inventory)
    if 'config' in phases:
        # run ansible config
        output.print('Running playbook...')
        if 'env' in config.keys():
            env = config['env']
        else:
            env = None
        runners.ansible(args.playbook, inv_path, env=env, output)
    output.print('Run completed...')
    sys.exit(0)
