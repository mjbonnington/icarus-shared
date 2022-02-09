# -*- coding: utf-8 -*-

name = 'ic_shared'

version = '1.1.8'

description = 'Icarus Shared Libraries'

authors = ['mjbonnington']

requires = [
    'plyer', 
]

build_requires = [
    'rezlib', 
]

build_command = 'python -m build {install}'


def commands():
    env.PYTHONPATH.append('{root}')
