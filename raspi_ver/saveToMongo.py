#-*- coding: utf-8 -*-

import json
import pymongo
with open('mise_incheon.json') as data_file:
	data = json.load(data_file)

#data_len=len(data['list'])

connection = pymongo.MongoClient("localhost",27017)
db = connection.mise
collection =db.incheon
for sido in data['list']:
	new_dic={}
	new_dic['city']=sido['cityName']
	new_dic['time']=sido['dataTime']
	new_dic['pm10']=sido['pm10Value']
	new_dic['pm25']=sido['pm25Value']
	collection.insert(new_dic)


with open('mise_seoul.json') as data_file2:
    data2 = json.load(data_file2)

db = connection.mise
collection =db.seoul

for sido in data2['list']:
	new_dic2={}
	new_dic2['city']=sido['cityName']
	new_dic2['time']=sido['dataTime']
	new_dic2['pm10']=sido['pm10Value']
	new_dic2['pm25']=sido['pm25Value']
	collection.insert(new_dic2)


#with open('newdata.json','w') as outfile:
#	json.dump(new_list,outfile)

