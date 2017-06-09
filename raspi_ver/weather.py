
# -*- coding:utf-8 -*-

from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus,unquote
decode_key=unquote('qNTKGUYOFgEj3m6dUMXBJ1ZLEPBbBX%2BQXY3d%2B77vxZgMC4RJ6TCp%2BtUw12hW%2FLgWj%2BxU10watODF73O%2Bx1essg%3D%3D')

url = 'http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastSpaceData'
queryParams = '?' + urlencode({quote_plus('_type'):'json', quote_plus('ServiceKey') : decode_key, quote_plus('nx') :'56' ,quote_plus('ny'):'124',quote_plus('base_date'):'20170608',quote_plus('base_time'): '0800' })

request = Request(url + queryParams)
request.get_method = lambda: 'GET'
response_body = urlopen(request).read()

f= open("weather.json",'w')
f.write(response_body)

print response_body
