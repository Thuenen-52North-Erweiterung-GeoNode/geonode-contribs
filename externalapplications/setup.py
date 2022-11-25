import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='externalapplications',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='GPL',
    description='GeoNode External Applications',
    long_description=README,
    long_description_content_type='text/markdown',
    url='http://52north.org',
    author='52North Developers',
    author_email='info@52north.org',
    install_requires=[
    ],
)
