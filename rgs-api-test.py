#!/usr/bin/env python
""" WaterML2.0 part 2 API test script

This script tests prototype RESTful APIs for the WaterML2.0 part 2
Interoperability Experiment
(http://external.opengis.org/twiki_public/HydrologyDWG/WaterML2Part2)

It requires two command line parameters:
    * URL : the base URL of the API to test (e.g.
      http://waterml2.csiro.au/rgs-api/v1)
    * MP_ID : an identifier for a monitoring point to test (e.g. 419009)

Optional flags:
    * --auth: supplies a user/pass combo (slash separator)
    * --no-header: indicates the API does not return header in JSON (e.g.
     count/next/prev etc.)
    * --verbose: display verbose output (shows JSON responses)

Example:
    python rgs-api-test.py http://waterml2.csiro.au/rgs-api/v1/ 419009 -a rgs/test

Author: Peter Taylor
Copyright CSIRO 2014
"""

import requests
import argparse
import unittest
import jsonschema
import json

parser = argparse.ArgumentParser(description='Run the RGS tests against a'
        'specific API URL')
parser.add_argument('URL', type=str,
        help='The base URL of the API. e.g. http://waterml2.csiro.au/rgs-api/v1')

parser.add_argument('MP_ID', type=str,
        help='The monitoring point ID to use for testing purposes')

parser.add_argument('-a', '--auth', dest='auth', action='store',
            default='', help='provide user,pass (comma between)')
    
parser.add_argument('-n', '--no-header', action='store_const', const=True, 
            default=False, help='Use to indicate the API does NOT use a result header')

parser.add_argument('-v', '--verbose', action='store_const', const=True, 
            default=False, help='Turn on verbose output -- JSON responses will'
            'be shown')

class HTTPRequester():
    """ Light wrapper over HTTP requests module
    """
    def __init__(self, auth):
        self.auth = auth

    def send_request(self, url, params):
        params['format'] = 'json'
        r = requests.get(url, 
                auth=self.auth, params=params)

        response_type = r.headers['content-type']
        if response_type != 'application/json':
            print ('WARNING: the response type has not been set to JSON'
                '(received ' + response_type + ')')
        return r

    def check_url_exists(self, url):
        r = requests.get(url, 
                auth=self.auth)
        if not r.ok:
            print 'WARNING: URL not resolvable (%s)' % (url)
        try:
            r.json()
        except:
            print ('WARNING: Could not retrieve JSON content from conversion '
            'group URL (%s)' % (url))

class RGSAPITester():
    ''' Class for running tests against WaterML2.0 part 2 RESTful APIS. 
    JSON content checks are very simple and only look for specific required
    fields. To be extended to use JSON schema for more comprehensive checks. 
    '''
    def __init__(self):
        self.URL = args.URL
        self.MP_ID = args.MP_ID
        self.no_header = args.no_header
        self.verbose = args.verbose

        # Definitions of base REST resources for URL endpoints
        self.CONVERSION = '/conversion'
        self.CONVERSION_GROUP = '/conversion-group'

        # USGS spelling fix - will be removed
        if self.URL.find('usgs') != -1:
            print 'USGS URL, fixing gauging spelling'
            self.GAUGING = '/guaging'
        else:
            self.GAUGING = '/gauging'
        self.MONITORING_POINT = '/monitoring-point'

        # Very basic schema to test existance of essentional properties
        # This will be replaced with a JSON schema validator
        self.MP_REQUIRED = ['id', 'name', 'shape','conversiongroup_set']
        self.CONV_REQUIRED = ['id', 'name', 'shape','conversiongroup_set']
        self.CONV_PERIOD_REQUIRED = ['periodStart', 'periodEnd', 'applicableConversion']
        #self.CONV_GROUP_REQUIRED = ['id', 'monitoringPoint', 'paramFrom','paramTo', \
        self.CONV_GROUP_REQUIRED = ['id', 'monitoringPoint',  
                                'conversionPeriods']
        self.GAUGING_REQUIRED = ['id', 'observedPropertyFrom', 'observedPropertyTo', 'fromValue', \
                'toValue', 'featureOfInterest', 'phenomenonTime']

        self.SCHEMA = { 'MP':self.MP_REQUIRED, 'CONV': self.CONV_REQUIRED, 
                    'CONV_PERIOD': self.CONV_PERIOD_REQUIRED, 'CONV_GROUP': self.CONV_GROUP_REQUIRED, 
                    'GAUGING': self.GAUGING_REQUIRED }

        if args.auth: 
            auth = tuple(args.auth.split('/'))
        else:
            auth = ('','')

        self.requester = HTTPRequester(auth)

    def validate_object(self, test_name, content, no_header = False):
        ''' Checks JSON in content parameter for required fields. Obviously 
        a full schema would be more appropriate but this gives a decent sanity
        check.
        The function should be passed the whole JSON response, including any 
        headers as this handles 'no-header' flag checks.
        '''
        
        if self.verbose: print json.dumps(content, indent=2)
        if self.no_header or no_header:
            json_content = content
        else:
            if content.has_key('results'):
                json_content = content['results']
            elif content.has_key('result'):
                json_content = content['result']
            else:
                print "No results could be found in header!"
                return False, ""

            if len(json_content) == 0:
                print "No results returned!" 
            else: # just check first object returned
                json_content = json_content[0]

        required_fields = self.SCHEMA[test_name]
        errors = 0
        for field in required_fields:
            if not json_content.has_key(field):
                print 'JSON object does not contain required %s field!' % \
                        (field)
                errors += 1
        if not errors:
            print "Successfully passed %s test!" % (test_name)
            return True, json_content
        else:
            print "%d error(s) found in %s objects" % (errors, test_name)
            return False, json_content

    def test_monitoring_point(self):
        print 'Testing retrieval of monitoring point (%s at %s)' % (self.MP_ID, self.URL)
        
        url = self.URL + self.MONITORING_POINT 
        params = dict()
        # Two MP names supported for interim (APIs tend to ignore
        # unknown ones)
        params['monitoring-point'] = self.MP_ID
        params['monitoringPoint'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        print 'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)
        if r.ok:
            print 'Received monitoring point encoding, checking structure...'
            result = r.json()
            success, mp = self.validate_object('MP',result)
            if success:
                print 'Checking conversion group link...'
                groups = mp['conversiongroup_set']
                if self.verbose: print json.dumps(result, indent=2)
                if len(groups) > 0:
                    self.requester.check_url_exists(groups[0])
        else:
            print 'Failed on MP retrieval'

    def test_gaugings(self):
        print 'Testing gaugings end point at %s for MP:%s' % (self.URL +
                    self.GAUGING, self.MP_ID)

        url = self.URL + self.GAUGING 
        params = dict()
        params['monitoringPoint'] = self.MP_ID
        params['monitoring-point'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        print 'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)
        if r.ok:
            print 'Received gaugings, checking structure...'
            result = r.json()
            self.validate_object('GAUGING',result)
        else:
            print 'Failed on gauging retrieval (%s)' % (r.reason)
        
    def test_conversion_group(self):
        print 'Testing conversion group end point at %s for MP:%s' % (self.URL +
                    self.GAUGING, self.MP_ID)

        url = self.URL + self.CONVERSION_GROUP 
        params = dict()
        params['monitoringPoint'] = self.MP_ID
        params['monitoring-point'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        print 'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)
        if r.ok:
            print 'Received conversion group, checking structure...'
            result = r.json()
            passed, valid_conv_group = self.validate_object('CONV_GROUP',result)
            # if passed, go on to do further content-based checking 
            if passed:
                print 'Checking nested conversion period object structure...'
                passed, valid_period = self.validate_object('CONV_PERIOD', 
                                valid_conv_group['conversionPeriods'][0], True)
        else:
            print 'Failed on conversion group retrieval (%s)' % (r.reason)
        
if __name__ == '__main__':
    args = parser.parse_args()
    tester = RGSAPITester()
    print "Running monitoring point test..."
    tester.test_monitoring_point()
    print "Running gauging test..."
    tester.test_gaugings()
    print "Running conversion group test..."
    tester.test_conversion_group()

    # Was previously using unit test framework but didn't match the HTTP client
    # - better for lower level unit tests
    #suite = unittest.TestLoader().loadTestsFromTestCase(BasicAvailabilityTest)
    #unittest.TextTestRunner(verbosity=1).run(suite)

