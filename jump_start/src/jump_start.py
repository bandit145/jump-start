import argparse
import jump_start.src.utils as utils
import jump_start.src.operating_systems as operating_systems
from jump_start.src.infrastructure import DNSMasq, Http
import jump_start.src.config as jump_config
import jump_start.src.runners as runners
import logging
import time
from docker.errors import APIError
import docker
import os
import sys
import yaml
import atexit


def get_args():
    parser = argparse.ArgumentParser(description='for bootstraping and deploying physical nodes on the same local network')
    parser.add_argument('--pull', help='pull containers', action='store_true')
    parser.add_argument('-p,', '--phases', help='phases of jump_start to run', default='cache,network,config')
    parser.add_argument('-c', '--config', help='config file path', default='jump_start.yml')
    parser.add_argument('--cache-path', help='cache path for os mirros', default='/home/{0}/.jump-start/web/cache/'.format(os.getenv('USER')))
    parser.add_argument('--log-level', help='logging level', default='info', choices=['info', 'debug'])
    parser.add_argument('--listen-port', help='port to listen on for callbacks', default=8080)
    parser.add_argument('--playbook', help='playbook name', default='playbook.yml')
    parser.add_argument('-i', '--interface', help='interface name to listen on', required=True)
    parser.add_argument('-t', '--timeout', help='timeout of waiting for callbacks', default=1800)
    return parser.parse_args()


def read_config(path, output):
    try:
        with open(path, 'r') as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        succeed, msg = jump_config.validate_config(config, jump_config.config_schema)
        if not succeed:
            output.error(msg)
        return config
    except yaml.YAMLError as error:
        output.error('yaml error', error)
    except FileNotFoundError:
        output.error('Could not find config {0}'.format(path))


def get_os_obj(os_name, os_config, output):
    if not hasattr(operating_systems, os_name):
        output.print(os_name, 'does not exist', file=sys.stderr)
        sys.exit(1)
    return getattr(operating_systems, os_name)(**os_config)


# shut off all containers
def clean_environment(client):
    [x.remove(force=True) for x in client.containers.list('app=jump-start')]


# TODO: This needs to be run in a seperate non blocking process so timeout will work. Use multiprocess.
def wait_for_callbacks(hosts, port, timeout):
    callback_listener = utils.Listener(('', port), utils.ListenerRequestHandler)
    start_time = time.time()
    cur_time = start_time
    while cur_time - start_time < float(timeout) and len(callback_listener.hosts) != len(hosts):
        callback_listener.handle_request()
        cur_time = time.time()
    return callback_listener.hosts


def main():
    inv_path = '/home/{0}/.jump-start/inv'.format(os.getenv('USER'))
    docker_client = docker.from_env()
    # register docker cleanup for exit
    atexit.register(clean_environment, docker_client)
    utils.prep_local()
    args = get_args()
    phases = args.phases.split(',')
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    output = utils.Output(logging)
    config = read_config(args.config, output)
    os_obj = get_os_obj(config['os'], config['os_config'], output)
    # configure os and cache things
    if 'cache' in phases:
        output.print('Downloading OS...')
        os_obj.download_repo(args.cache_path, config['os_config']['rsync_mirror'])
    # deploy containers
    if 'network' in phases:
        output.print('Creating containers...')
        dnsmasq = DNSMasq(output, docker_client, config, args.interface)
        httpd = Http(output, docker_client)
        try:
            # TODO: what the fuck is going on here with port is in use
            # If I comment one of these it works fine but both of these  when the second is started I get a port conflict on the original
            # container.
            #dnsmasq.run(pull=args.pull)
            httpd.run(pull=args.pull)
        except APIError as error:
            output.error(error)
        os_obj.generate_install_files(args.cache_path, config)
        # wait for responsese
        output.print('Waiting for responses from hosts...')
        hosts = [x['hostname'] for x in config['hosts']]
        callback_data = wait_for_callbacks(hosts, args.listen_port, args.timeout)
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
        runners.ansible(args.playbook, inv_path, env, output)
    output.print('Run completed...')
    sys.exit(0)
