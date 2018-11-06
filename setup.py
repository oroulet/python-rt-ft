from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='aiti-optoforce-sensor',
    version='0.1',
    description='Python driver for Optforce and ATI force sensors',
    long_description=long_description,
    url='https://github.com/SintefManufacturing/python-rt-ft',
    author='Morten Lind et al',
    packages=['force_sensor'],
    zip_safe=True,
)
