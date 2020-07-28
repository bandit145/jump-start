#!/usr/bin/env python

from distutils.core import setup


def get_req():
    with open('requirements.txt', 'r') as reqs:
        return reqs.read().split()


setup(name='jump-start',
      version='1.0',
      description='utility to boot and configure bare metal servers',
      author='Philip Bove',
      author_email='phil@bove.online',
      packages=['jump_start'],
      scripts=['bin/jump-start'],
      install_requres = get_req()
     )