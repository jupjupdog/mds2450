# -*- coding: utf-8 -*-



from socket import *

from select import *

import sys

from time import ctime



HOST = '127.0.0.1'

PORT = 10000

BUFSIZE = 1024

ADDR = (HOST,PORT)



clientSocket = socket(AF_INET, SOCK_STREAM)
try:
	clientSocket.connect(ADDR)
except  Exception as e:
	print('%s:%s'%ADDR)
	sys.exit()
	print('connect is success')
