
# -*- coding:utf-8 -*-

from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus,unquote
decode_key=unquote('qNTKGUYOFgEj3m6dUMXBJ1ZLEPBbBX%2BQXY3d%2B77vxZgMC4RJ6TCp%2BtUw12hW%2FLgWj%2BxU10watODF73O%2Bx1essg%3D%3D')

url = 'http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureSidoLIst'
queryParams = '?' + urlencode({quote_plus('_returnType'):'json', quote_plus('ServiceKey') : decode_key, quote_plus('pageNo') : '1',quote_plus('numOfRows'):'9',quote_plus('ver'):'1.3',quote_plus('searchCondition'):'DAILY',quote_plus('sidoName'):'인천' })

request = Request(url + queryParams)
request.get_method = lambda: 'GET'
response_body = urlopen(request).read()

f= open("weather.json",'w')
f.write(response_body)

print response_body
