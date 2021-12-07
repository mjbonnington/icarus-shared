# -*- coding: utf-8 -*-

name = 'ic_shared'

version = '1.1.4'

description = 'Icarus Shared Libraries'

variants = [['python-2.7+']]

requires = [
#    'plyer'
]

authors = ['mjbonnington']

build_command = 'python {root}/build.py {install}'


def commands():
    env.PYTHONPATH.append('{root}')
