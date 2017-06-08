#-*- coding: utf-8 -*-

import json
with open('mise.json') as data_file:
	data = json.load(data_file)

#data_len=len(data['list'])

new_list=list()
for sido in data['list']:
	new_dic={}
	new_dic['city']=sido['cityName']
	new_dic['time']=sido['dataTime']
	new_dic['pm10']=sido['pm10Value']
	new_dic['pm25']=sido['pm25Value']
	new_list.append(new_dic)
with open('newdata.json','w') as outfile:
	json.dump(new_list,outfile)

