import json
import optparse
import sys
import urllib2

def main():
    parser = optparse.OptionParser(usage='%prog -u URL [options]',
                                   version='%prog 0.1.0')
    parser.add_option('-u', '--url', help='URL to access GAEUnit', dest='url')

    (options, args) = parser.parse_args(sys.argv)

    # Die if we aren't given the URL.
    # TODO: allow for setting URL in an .rc file
    # TODO: validate URL
    if not options.url:
        parser.print_usage()
        exit()

    tests = get_tests(options.url)
    print str(tests)


# Get a list of test names given the GAEUnit access point
def get_tests(url):
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
    # We simply need a list of <module>.<class>.<method>.

    tests = []

    for module, classes in dict.iteritems():
      for klass, methods in classes.iteritems():
        for method in methods:
          tests.append("%s.%s.%s" % (module, klass, method))

    return tests