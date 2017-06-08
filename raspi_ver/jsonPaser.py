#-*- coding: utf-8 -*-

import json
import pymongo
with open('mise.json') as data_file:
	data = json.load(data_file)

#data_len=len(data['list'])

connection = pymongo.MongoClient("localhost",27017)
db = connection.mise
collection =db.incheon
new_list=list()
for sido in data['list']:
	new_dic={}
	new_dic['city']=sido['cityName']
	new_dic['time']=sido['dataTime']
	new_dic['pm10']=sido['pm10Value']
	new_dic['pm25']=sido['pm25Value']
	collection.insert(new_dic)
	new_list.append(new_dic)

with open('newdata.json','w') as outfile:
	json.dump(new_list,outfile)

