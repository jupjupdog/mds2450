 # -*- coding: utf-8 -*-

from time import localtime

base_time=[200,500,800,1100,1400,1700,2000,2300]
aaa = localtime()
#print time.time()
date_get= "%04d%02d%02d" % (aaa.tm_year, aaa.tm_mon, aaa.tm_mday)
near_time="%02d%02d" % (aaa.tm_hour, aaa.tm_min)
get_time=int(near_time)
exec_time=0200
print get_time
for time in base_time:
	print time
	if get_time < time:
		exec_time = tmp
		break
	else:
		tmp = time
print exec_time
near_time = "%04d" % exec_time
print near_time

