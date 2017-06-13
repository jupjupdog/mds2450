# -*- coding: utf-8 -*-
#!/usr/bin/env python

from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus,unquote
import pymongo
import json
from socket import *
import SocketServer
from select import *
from time import ctime
import sys
from pymongo import MongoClient
from time import localtime
import time
client = MongoClient()
db_weather = client.weather
coll_now = db_weather.now
coll_xy = db_weather.xy
db_mise = client.mise
coll_inchoen = db_mise.incheon
coll_seoul = db_mise.seoul

def findXY(city,district):
	xy=coll_xy.find({'1level':city,'2level':district},{"_id":0,"1level":0,"2level":0})
	return xy

def getWeather(xy):
	decode_key=unquote('qNTKGUYOFgEj3m6dUMXBJ1ZLEPBbBX%2BQXY3d%2B77vxZgMC4RJ6TCp%2BtUw12hW%2FLgWj%2BxU10watODF73O%2Bx1essg%3D%3D')
	url = 'http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastSpaceData'
	base_time=[200,500,800,1100,1400,1700,2000,2300]
	
	aaa = localtime()
	#print time.time()	
	date_get= "%04d%02d%02d" % (aaa.tm_year, aaa.tm_mon, aaa.tm_mday)

	near_time="%02d%02d" % (aaa.tm_hour, aaa.tm_min)
	
	get_time=int(near_time)
	exec_time=200
	tmp=0
	for time in base_time:
		if get_time < time:
			exec_time = tmp
			break
		else:
			tmp=time
	near_time = "%04d" % exec_time
	x = str(xy['x'])
	y = str(xy['y'])
	queryParams = '?' + urlencode({quote_plus('_type'):'json', quote_plus('ServiceKey') : decode_key, quote_plus('nx') :x ,quote_plus('ny'):y,quote_plus('base_date'):date_get,quote_plus('base_time'): near_time })

	print queryParams
	request = Request(url + queryParams)
	
	request.get_method = lambda: 'GET'
	response_body = urlopen(request).read()

	f= open("weather.json",'w')
	f.write(response_body)
	f.close()
	with open('weather.json') as data_file:
	    data = json.load(data_file)
	connection = pymongo.MongoClient("localhost",27017)
	db = connection.weather
	collection =db.now

	new_dic={}

	for sido in data['response']['body']['items']['item']:
		new_cata=sido['category']
		value=sido['fcstValue']
		if new_cata=='POP':
			new_dic['nx']=sido['nx']
			new_dic['ny']=sido['ny']
			new_dic['baseTime']=sido['baseTime']
			new_dic['baseDate']=sido['baseDate']
			new_dic['fcastTime']=sido['fcstTime']
		new_dic[new_cata]=value

	print new_dic
	collection.insert(new_dic)


class MyTCPHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		print("clinet access :{0}".format(self.client_address[0]))
		sock = self.request
		rbuff = sock.recv(1024)
		print type(rbuff)
		received = rbuff.decode('utf-8').encode('utf-8')
		
		loc= received.find('\n')
		if loc>0:
			received.strip('\n')
		rere = received.splitlines()
		
		city_dist= rere[0].split(',')
		print city_dist
		xy_obj = findXY(city_dist[0],city_dist[1])
		

		getWeather(xy_obj[0])
		print xy_obj[0]['x']

		inf_weather = coll_now.find({'nx':xy_obj[0]['x'],'ny':xy_obj[0]['y']},{'_id':0,'nx':0,'ny':0,'fcastTime':0,'baseDate':0,'baseTime':0}).sort([('baseDate',-1),('baseTime',-1)]).limit(1)

		mise=coll_seoul.find({'city':"마포구"},{'_id':0,'city':0}).sort([('time',-1)]).limit(1)
		if city_dist[0] =='서울특별시':
			mise=coll_seoul.find({'city':city_dist[1]},{'_id':0,'city':0}).sort([('time',-1)]).limit(1)
			#print type(mise)	
		elif city_dist[1] == '인천광역시':
			mise=coll_incheon.find({'city':city_dist[1]},{'_id':0,'city':0}).sort([('time',-1)]).limit(1)
		
		send_dic = inf_weather[0]
		print type(send_dic)
		send_dic.update(mise[0])
		add_rn = str(send_dic)+'\n'
		sock.send(add_rn.encode('utf-8'))
		sock.close()


if __name__ == '__main__':
	HOST = '127.0.0.1'
	PORT = 56789
	BUFSIZE = 1024
	ADDR = (HOST,PORT)
	server = SocketServer.TCPServer((HOST,PORT), MyTCPHandler)

	print('start server ...')
	print time.time()
	server.serve_forever()

#client = MongoClient()
#db_weather = client.weather
#collection_now = db_weather.now
#collection_xy = db_weather.xy
#db_mise = client.mise

#serverSocket.bind(ADDR)
