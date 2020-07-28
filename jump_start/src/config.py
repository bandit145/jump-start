config_schema = {
    'os': {'required': False, 'override': True, 'type': str},
    'os_config': {'required': False, 'override': True, 'type': dict},
    'env': {'required': False, 'override': False, 'type': dict, 'config': {}},
    'domain': {'required': True, 'override': False, 'type': str},
    'subnet': {'required': True, 'override': False, 'type': str},
    'install_file_template':{'required': False, 'override': True, 'type': str},
    'hosts': {'required': True, 'override': False, 'type': list, 'config': {
            'mac': {'required': False, 'override': False, 'type': str},
            'hostname': {'required': True, 'override': False, 'type': str},
            'install_file_template': {'required': False, 'override': False, 'type': str},
            'os': {'required': False, 'override': False, 'type': dict, 'config': {
                    'name':  {'required': True, 'type': str},
                    'version': {'required': True, 'type': str}
                }
            }
        }
    }
}

def validate_config(config, schema, override_keys=[]):
    if type (config) == list:
        for item in config:
            data =  validate_config(item, schema, override_keys)
            if not data[0]:
                return False, data[1]
    if type(config) == dict:
        for key, value in schema.items():
            if value['required'] and key not in config.keys():
                return False, '{0} missing from config!'.format(key)
            elif key in config.keys() and value['type'] != type(config[key]):
                return False, '{0} incorrect type! should be {1}'.format(key, value['type'])
            elif 'override' in value.keys() and value['override'] and key not in config.keys():
                override_keys.append(key)
            # remove from override_keys list if issue
            elif key in config.keys() and key in override_keys:
                del override_keys[override_keys.index(key)]
            if  value['type'] == list or value['type'] == dict and key in config.keys() and 'config' in value.keys():
                data = validate_config(config[key], value['config'], override_keys)
                if not data[0]:
                    return False, data[1]
    if len(override_keys) != 0:
        return False, '{0} not overridden'.format(','.join(override_keys))
    return True, None
