import json
import optparse
import re
import sys
import time
import unittest.runner
import urllib2
import yaml

import gaeunit_cli_support.helpers as helpers

def main():
    parser = optparse.OptionParser(usage='%prog -u URL [options]',
                                   version='%prog 0.1.0',
                                   add_help_option=False)

    parser.add_option('--help', action='store_true', default=False, dest='help')

    parser.add_option('-h', '--host',
                      help='The host (port included) which is running the GAE'
                           'instance',
                      default='http://localhost:8080', dest='host')

    parser.add_option('-p', '--path', help="Relative path of GAEUnit endpoint",
                      default=get_default_path(), dest='path')

    (options, args) = parser.parse_args(sys.argv)

    if options.help:
        print parser.format_help().strip()
        exit()

    # Go!
    run_tests(get_url(options))


def get_default_path():
    """Determine the default GAEUnit path option."""

    # Try to read from app.yaml; if we can't find it, return the GAEUnit
    # default '/test'
    try:
        gae_config_file = open('/Users/jon/Projects/stremorshort/app.yaml', 'r')
    except IOError as e: pass
    else:
        loaded = yaml.load(gae_config_file.read())
        gae_config_file.close()

        for handler in loaded['handlers']:
            if 'script' in handler and handler['script'].startswith('gaeunit'):
                return re.sub(r'[^\w/]', '', handler['url'])

    return '/test'


def get_url(options):
    """Determine the GAEUnit URL given optparse's output."""

    # TODO: validate URL
    if options.host.startswith('http'):
        host = options.host
    else:
        host = 'http://%s' % options.host

    if options.path.startswith('/'):
        path = options.path
    else:
        path = '/%s' % options.path

    return host + path


def run_tests(url, stream=None):
    """Run a list of tests"""

    u = urllib2.urlopen('%s?format=plain' % url)
    print u.read()


if __name__ == '__main__':
    main()
