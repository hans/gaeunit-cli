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

    url = get_url(options)

    # Get a list of test call names from the server
    tests = get_tests(url)

    # Go!
    run_tests(url, tests)


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


def get_tests(url):
    """Get a list of test names given the GAEUnit access point"""

    u = urllib2.urlopen('%s/list' % url)
    dict = json.loads(u.read())

    # GAEUnit outputs a data structure like this:
    #
    # {
    #   "module": {
    #     "SomeTestClass": [
    #       "test_abc",
    #       "test_xyz"
    #     ]
    #   }
    # }
    #
    # We simply need a list of <module>.<class>.<method> strings.

    tests = []

    for module, classes in dict.iteritems():
      for klass, methods in classes.iteritems():
        for method in methods:
          tests.append("%s.%s.%s" % (module, klass, method))

    return tests


def run_tests(url, tests, stream=None):
    """Run a list of tests"""

    if not stream:
        stream = helpers.DummyStdout()

    # Use a standard unittest output mechanism
    result = unittest.runner.TextTestResult(stream=stream,
                                            descriptions=True,
                                            verbosity=1)

    # Pass this dummy object (standing in for unittest.TestCase) to the test
    # result object.
    dummy = helpers.DummyTest()

    # Start timing
    start_time = time.time()

    # TODO: mod GAEUnit to run multiple tests w/ single request
    # see unittest.loadTestsFromNames
    for test in tests:
        # Trigger the test run and receive results
        u = urllib2.urlopen('%s/run?name=%s' % (url, test))
        data = json.loads(u.read())

        # Update the dummy test's description to describe the current test
        dummy.testName = test

        if len(data['failures']) > 0 or len(data['errors']) > 0:
            if len(data['failures']) > 0:
                # Use the method's docstring as the test description
                failure = data['failures'][0]
                dummy.shortDescription_ = failure['desc']

                # Fake an exception tuple
                desc = helpers.get_error_message(failure['desc'])
                exc = (AssertionError, desc, None)

                result.addFailure(dummy, exc)
            elif len(data['errors']) > 0:
                error = data['errors'][0]
                tb = helpers.DummyTraceback(error['detail'])

                # Fake an exception tuple
                desc = helpers.get_error_message(error['detail'])
                exc = (helpers.GAEError, desc, tb)

                result.addError(dummy, exc)
        else:
            result.addSuccess(dummy)

    result.printErrors()

    totalTime = time.time() - start_time
    stream.writeln("Ran %d test%s in %.3fs\n" %
                   (len(tests), len(tests) != 1 and "s" or "", totalTime))

    expectedFails = unexpectedSuccesses = skipped = 0
    try:
        results = map(len, (result.expectedFailures,
                          result.unexpectedSuccesses,
                          result.skipped))
    except AttributeError:
        pass
    else:
        expectedFails, unexpectedSuccesses, skipped = results

    infos = []
    if not result.wasSuccessful():
        stream.write("FAILED")
        failed, errored = map(len, (result.failures, result.errors))
        if failed:
            infos.append("failures=%d" % failed)
        if errored:
            infos.append("errors=%d" % errored)
    else:
        stream.write("OK")
    if skipped:
        infos.append("skipped=%d" % skipped)
    if expectedFails:
        infos.append("expected failures=%d" % expectedFails)
    if unexpectedSuccesses:
        infos.append("unexpected successes=%d" % unexpectedSuccesses)

    if infos:
        stream.writeln(" (%s)" % (", ".join(infos),))
    else:
        stream.writeln()


if __name__ == '__main__':
    main()