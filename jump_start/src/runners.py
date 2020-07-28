import subprocess

def ansible(playbook, inv_file, env, output):
    ansible_cmd = 'ansible-playbook all -i {0}'.format(inv_file)
    try:
        subprocess.run(ansible_cmd.split(' '), env=env, check=True)
    except subprocess.CalledProcessError:
        output.error('Ansible failed to run')