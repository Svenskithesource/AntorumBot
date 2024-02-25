from setuptools import setup, find_packages

setup(
    name='antorum',
    version='0.1.0',
    packages=find_packages(include=['antorum', 'antorum.*']),
    install_requires=open('requirements.txt').read().splitlines()
)
