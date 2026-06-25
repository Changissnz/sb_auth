from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='sb_auth',
    version='0.0.4',
    description='An implementation of a WebSocket authentication scheme, unsecured ws://',
    long_description=readme,
    author='Richard Pham',
    author_email='phamrichard45@gmail.com',
    url='https://github.com/Changissnz/sb_auth', 
    #license=LICENSE,
    packages=find_packages(exclude=('tests','docs'))
)