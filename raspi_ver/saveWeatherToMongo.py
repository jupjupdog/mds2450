#-*- coding: utf-8 -*-

import json
import pymongo
with open('weather.json') as data_file:
	data = json.load(data_file)

#data_len=len(data['list'])

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
	#if sido[]['category']=='POP':
	#	print 'here'
	#new_dic['POP']=sido['POP']
	#new_dic['T3H']=sido['T3H']
	#new_dic['R06']=sido['RO6']
	#new_dic['REH']=sido['REH']

print new_dic
collection.insert(new_dic)




#with open('newdata.json','w') as outfile:
#	json.dump(new_list,outfile)

