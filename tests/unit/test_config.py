import jump_start.src.config as config
import yaml


CONFIG_DIR = 'tests/unit/test_configs/'


def load_conf(file_name):
    with open(CONFIG_DIR +  file_name, 'r') as config_file:
        conf = yaml.load(config_file, Loader=yaml.FullLoader)
    return conf


def test_good_config():
    good_conf = load_conf('test_config_good.yml')
    assert (True, None) == config.validate_config(good_conf, config.config_schema)


def test_good_config_override():
    good_conf = load_conf('test_config_good_override.yml')
    assert (True, None) == config.validate_config(good_conf, config.config_schema)


def test_bad_config_override():
    bad_conf = load_conf('test_config_bad_override.yml')
    assert (False, 'install_file_template not overridden') == config.validate_config(bad_conf, config.config_schema)