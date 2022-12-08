#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='github-text-crawler',
    version='0.1.0',
    author='Zian Ke',
    author_email='kezian@umich.edu',
    url='https://github.com/zianke/github-text-crawler',
    description='Extract documentation and commit logs from GitHub repository.',
    license='MIT',
    packages=['github-text-crawler'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['certifi==2022.12.7',
                      'chardet==3.0.4',
                      'click==6.7',
                      'idna==2.7',
                      'requests==2.19.1',
                      'urllib3==1.23'],
)
