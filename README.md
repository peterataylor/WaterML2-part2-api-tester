# Overview

This script tests prototype RESTful APIs for the WaterML2.0 part 2 Interoperability Experiment (http://external.opengis.org/twiki_public/HydrologyDWG/WaterML2Part2). WaterML2.0 part 2 is a format for exchanging hydrological rating tables and gaugings (observations). See http://opengeospatial.org/standards/waterml for info on WaterML2.0. 

The script issues HTTP requests and attempts to parse JSON responses. The structure checking on the JSON is very basic; it checks for existence of some key required fields. This will be extended to make use of JSON schema. 

# Installation and Requirements

See [requirements.txt](https://github.com/peterataylor/WaterML2-part2-api-tester/blob/master/requirements.txt) for required python libraries. These can be loaded using [Python pip](https://pypi.python.org/pypi/pip):

``` pip install -r requirements.txt ```

# Usage

The script requires two command line parameters:
* URL : the base URL of the API to test (e.g. http://waterml2.csiro.au/rgs-api/v1)
* MP_ID : an identifier for a monitoring point to test (e.g. 419009)

Optional flags:
* --auth (-a): supplies a user/pass combo (slash separator)
* --no-header (-n): indicates the API does not return header in JSON (e.g.
     count/next/prev etc.)
* --verbose (-v): display verbose output (shows JSON responses)

## Examples

```
python rgs-api-test.py http://waterml2.csiro.au/rgs-api/v1/ 419009 -a rgs/test

python rgs-api-test.py http://staging.waterdata.usgs.gov/nwisweb/cgi-src 06025500

python rgs-api-test.py http://203.12.195.133/cgi/waterml2 225201A

```

## Example output

```
>>> python rgs-api-test.py http://staging.waterdata.usgs.gov/nwisweb/cgi-src 06025500
USGS URL, fixing gauging spelling
Running monitoring point test...
Testing retrieval of monitoring point (06025500 at http://staging.waterdata.usgs.gov/nwisweb/cgi-src)
WARNING: the response type has not been set to JSON(received text/html; charset=iso-8859-1)
Received 404 response from http://staging.waterdata.usgs.gov/nwisweb/cgi-src/monitoring-point?monitoring-point=06025500&monitoringPoint=06025500&format=json (text/html; charset=iso-8859-1)
Failed on MP retrieval
Running gauging test...
Testing gaugings end point at http://staging.waterdata.usgs.gov/nwisweb/cgi-src/guaging for MP:06025500
WARNING: the response type has not been set to JSON(received text/plain; charset=utf-8)
Received 200 response from http://staging.waterdata.usgs.gov/nwisweb/cgi-src/guaging?monitoring-point=06025500&monitoringPoint=06025500&format=json (text/plain; charset=utf-8)
Received gaugings, checking structure...
JSON object does not contain required featureOfInterest field!
1 error(s) found in GAUGING objects
Running conversion group test...
Testing conversion group end point at http://staging.waterdata.usgs.gov/nwisweb/cgi-src/guaging for MP:06025500
WARNING: the response type has not been set to JSON(received text/plain; charset=utf-8)
Received 200 response from http://staging.waterdata.usgs.gov/nwisweb/cgi-src/conversion-group?monitoring-point=06025500&monitoringPoint=06025500&format=json (text/plain; charset=utf-8)
Received conversion group, checking structure...
Successfully passed CONV_GROUP test!
Checking nested conversion period object structure...
Successfully passed CONV_PERIOD test!
```
