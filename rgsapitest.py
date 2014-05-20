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
    ##def __init__(self):
        #self.auth = auth

    def send_request(self, url, params):
        params['format'] = 'json'
        #r = requests.get(url, 
        #        auth=self.auth, params=params)
        r = requests.get(url, params=params)

        #response_type = r.headers['content-type']
        #if response_type != 'application/json':
            #self.messages.append(('WARNING: the response type has not been set to JSON'
            #        '(received ' + response_type + ')'))
        
        #if 'Access-Control-Allow-Origin' not in r.headers:
        #    self.messages.append(('WARNING: there is no access-control header set. This is '
        #            'needed for cross-service IE demo'))
                
        return r

    def check_url_exists(self, url):
        #r = requests.get(url, 
        #        auth=self.auth)
        params = {'format': 'json'}
        r = requests.get(url, params=params)
        if not r.ok:
            message = 'WARNING: URL not resolvable (%s)' % (url)
            return False, message
        try:
            r.json()
        except:
            message = 'WARNING: Could not retrieve JSON content from URL (%s)' % (url)
            return False, message

        return True, ""

class RGSAPITester():
    ''' Class for running tests against WaterML2.0 part 2 RESTful APIS. 
    JSON content checks are very simple and only look for specific required
    fields. To be extended to use JSON schema for more comprehensive checks. 
    '''
    def __init__(self, url, mp_id, no_header = False, verbose = False):
        self.URL = url 
        self.MP_ID = mp_id
        self.no_header = no_header
        self.verbose = verbose

        # Definitions of base REST resources for URL endpoints
        self.CONVERSION = '/conversion'
        self.CONVERSION_GROUP = '/conversion-group'

        self.MESSAGE_INFO = 0
        self.MESSAGE_WARN = 1 
        self.MESSAGE_ERROR = 2 
        self.MESSAGE_CODE = 3 

        # contains results
        self.messages = []
        self.warnings = []
        self.errors = []

        # USGS spelling fix - will be removed
        #if self.URL.find('usgs') != -1:
        #    self.messages.append('USGS URL, fixing gauging spelling')
        #    self.GAUGING = '/guaging'
        #else:
        self.GAUGING = '/gauging'
        self.MONITORING_POINT = '/monitoring-point'

        # Very basic schema to test existance of essentional properties
        # This will be replaced with a JSON schema validator
        self.MP_REQUIRED = ['id', 'name', 'shape','conversiongroup_set']
        self.CONV_REQUIRED = ['id', 'paramFrom',
                'paramTo','conversionperiod_set', 'monitoringPoint', 'points']
        self.CONV_PERIOD_REQUIRED = ['periodStart', 'periodEnd', 'applicableConversion']
        #self.CONV_GROUP_REQUIRED = ['id', 'monitoringPoint', 'paramFrom','paramTo', \
        self.CONV_GROUP_REQUIRED = ['id', 'monitoringPoint',  
                                'conversionPeriods']
        self.GAUGING_REQUIRED = ['id', 'observedPropertyFrom', 'observedPropertyTo', 'fromValue', \
                'toValue', 'featureOfInterest', 'phenomenonTime']

        self.SCHEMA = { 'MP':self.MP_REQUIRED, 'CONV': self.CONV_REQUIRED, 
                    'CONV_PERIOD': self.CONV_PERIOD_REQUIRED, 'CONV_GROUP': self.CONV_GROUP_REQUIRED, 
                    'GAUGING': self.GAUGING_REQUIRED }

        ''' Removing authentication for now - not really needed
        if args.auth: 
            auth = tuple(args.auth.split('/'))
        else:
            auth = ('','')
        '''

        self.requester = HTTPRequester()


    def validate_object(self, test_name, content, no_header = False):
        ''' Checks JSON in content parameter for required fields. Obviously 
        a full schema would be more appropriate but this gives a decent sanity
        check.
        The function should be passed the whole JSON response, including any 
        headers as this handles 'no-header' flag checks.
        '''
        
        if self.verbose: self.messages.append({ "level": self.MESSAGE_CODE, "msg":
            json.dumps(content, indent=2)})
        if self.no_header or no_header:
            json_content = content
        else:
            if content.has_key('results'):
                json_content = content['results']
            elif content.has_key('result'):
                json_content = content['result']
                self.messages.append({"level": self.MESSAGE_ERROR,
                    "msg":"Result property should be named results (plural). "
                    "Forgiving this error..."})
            else:
                self.messages.append({ "level": self.MESSAGE_ERROR, "msg":"No \
                    results could be found in header!"})
                return False, ""

            if len(json_content) == 0:
                self.messages.append({ "level": self.MESSAGE_ERROR, "msg":"No \
                    results returned!"})
            else: # just check first object returned
                json_content = json_content[0]

        required_fields = self.SCHEMA[test_name]
        errors = 0
        for field in required_fields:
            if not json_content.has_key(field):
                self.messages.append({ "level": self.MESSAGE_ERROR, 
                    "msg":'JSON object does not contain required %s field!' %  (field)})
                errors += 1
        if not errors:
            self.messages.append({ "level": self.MESSAGE_INFO,
                "msg":"Successfully passed %s test!" % (test_name)})
            return True, json_content
        else:
            self.messages.append({ "level": self.MESSAGE_ERROR, 
                "msg":"%d error(s) found in %s objects" % (errors, test_name)})
            return False, json_content

    def test_monitoring_point(self):
        self.messages = []
        self.messages.append({ "level": self.MESSAGE_INFO, 
            "msg":'Testing retrieval of monitoring point (%s at %s)' %
            (self.MP_ID, self.URL)})
        
        url = self.URL + self.MONITORING_POINT 
        params = dict()
        # Two MP names supported for interim (APIs tend to ignore
        # unknown ones)
        params['monitoring-point'] = self.MP_ID
        params['monitoringPoint'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        self.messages.append({ "level": self.MESSAGE_INFO,
                "msg":'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)})
        if r.ok:
            self.messages.append({ "level": self.MESSAGE_INFO, 
                "msg":'Received monitoring point encoding, checking structure...'})
            try:
                result = r.json()
            except:
                self.messages.append({"level":self.MESSAGE_ERROR,
                    "msg":"No valid JSON response from %s" % r.url})
                return self.messages
            success, mp = self.validate_object('MP',result)
            if success:
                groups = mp['conversiongroup_set']
                self.messages.append({ "level": self.MESSAGE_INFO,
                    "msg":'Checking conversion group link (%s)' % str(groups)})
                #if self.verbose: self.messages.append({ "level":
                #    self.MESSAGE_CODE, "msg":json.dumps(result, indent=2)})
                if len(groups) > 0:
                    passes, message = self.requester.check_url_exists(groups[0])
                    if not passes:
                        self.messages.append({"level":self.MESSAGE_ERROR,
                            "msg":"Conversion group link from MP not "
                            "resolvable (%s)" % message})
                    else:
                        self.messages.append({"level":self.MESSAGE_INFO,
                            "msg":"Conversion group link OK"})
                else:
                    self.messages.append({"level":self.MESSAGE_ERROR,
                        "msg":"No conversion group link from MP"})
        else:
            self.messages.append({ "level": self.MESSAGE_ERROR, 
                "msg":'Failed on MP retrieval: error returned from:'
                ' %s' % r.url})

        return self.messages

    def test_gaugings(self):
        self.messages = []
        self.messages.append({ "level": self.MESSAGE_INFO, 
                "msg":'Testing gaugings end point at %s for MP:%s' % (self.URL +
                self.GAUGING, self.MP_ID)})

        url = self.URL + self.GAUGING 
        params = dict()
        params['monitoringPoint'] = self.MP_ID
        params['monitoring-point'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        self.messages.append({ "level": self.MESSAGE_INFO, 
            "msg":'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)})
        if r.ok:
            self.messages.append({ "level": self.MESSAGE_INFO, "msg":'Received'
                ' gaugings, checking structure...'})

            try:
                result = r.json()
            except:
                self.messages.append({ "level": self.MESSAGE_ERROR,
                    "msg":'Error parsing JSON response from request:' + r.url})
                return self.messages

            self.validate_object('GAUGING',result)
        else:
            self.messages.append({ "level": self.MESSAGE_ERROR, "msg":'Failed ' 
                'on gauging retrieval (%s)' % (r.reason)})

        return self.messages
        
    def test_conversion_group(self):
        self.messages=[]
        self.messages.append({ "level": self.MESSAGE_INFO, 
            "msg":'Testing conversion group end point at %s for MP:%s' % (self.URL +
            self.GAUGING, self.MP_ID)})

        url = self.URL + self.CONVERSION_GROUP 
        params = dict()
        params['monitoringPoint'] = self.MP_ID
        params['monitoring-point'] = self.MP_ID
        r = self.requester.send_request(url, params)

        response_type = r.headers['content-type']
        self.messages.append({ "level": self.MESSAGE_INFO, 
                "msg":'Received %d response from %s (%s)' % (r.status_code, r.url,
                response_type)})
        if r.ok:
            self.messages.append({ "level": self.MESSAGE_INFO, 
                    "msg":'Received conversion group, checking '
                    'structure...'})
            try: 
                result = r.json()
            except:
                self.messages.append({ "level": self.MESSAGE_ERROR, 
                    "msg":'Error retrieving JSON from call %s' % r.url})
                return self.messages
            
            passed, valid_conv_group = self.validate_object('CONV_GROUP',result)
            # if passed, go on to do further content-based checking 
            if passed:
                self.messages.append({ "level": self.MESSAGE_INFO, 
                        "msg":'Checking nested conversion period object structure...'})

                if len(valid_conv_group['conversionPeriods']) > 0:
                    passed, valid_period = self.validate_object('CONV_PERIOD', 
                                valid_conv_group['conversionPeriods'][0], True)
                    if passed:
                        conv_url = valid_period["applicableConversion"]
                        self.messages.append({"level":self.MESSAGE_INFO,
                            "msg": "Valid period object. Checking "
                            "conversion at %s" % conv_url})
                        r = self.requester.send_request(conv_url, params)
                        if r.ok:
                            self.messages.append({"level":self.MESSAGE_INFO, 
                                "msg":"Retrieved conversion."})
                            result = r.json()
                            passed, valid_conv = self.validate_object('CONV',
                                    result)
                        else:
                            self.messages.append({"level":self.MESSAGE_ERROR, 
                                "msg":"Error retrieving applicable conversion"})

                else:
                    self.messages.append({ "level": self.MESSAGE_WARN, 
                        "msg":'No conversion periods listed in group'})
        else:
            self.messages.append({ "level": self.MESSAGE_ERROR,
                    "msg":'Failed on conversion group retrieval (%s)' %
                    (r.reason)})
        return self.messages
    
    def print_results(self):
        for msg in self.messages:
            print msg

        
if __name__ == '__main__':
    args = parser.parse_args()
    tester = RGSAPITester(args.URL, args.MP_ID, args.no_header, args.verbose)
    print "Running monitoring point test..."
    tester.test_monitoring_point()
    print "Running gauging test..."
    tester.test_gaugings()
    print "Running conversion group test..."
    tester.test_conversion_group()
    tester.print_results()

    # Was previously using unit test framework but didn't match the HTTP client
    # - better for lower level unit tests
    #suite = unittest.TestLoader().loadTestsFromTestCase(BasicAvailabilityTest)
    #unittest.TextTestRunner(verbosity=1).run(suite)

