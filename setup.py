from distutils.core import setup

setup(
    name='GAEUnit CLI'
    version='0.1.0'
    author='Hans Engel'
    author_email='engel@engel.uk.to'
    packages=['gaeunit_cli']
    scripts=['bin/gaeunit']
    url='https://github.com/hans/gaeunit-cli'
    license='LICENSE.md'
    description='Run GAEUnit tests from the command line')