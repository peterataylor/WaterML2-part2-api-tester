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

