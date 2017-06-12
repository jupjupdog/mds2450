# -*- coding: utf-8 -*-


import socket
from socket import *

from select import *

import sys

from time import ctime



if __name__ == '__main__':
	HOST = '127.0.0.1'
	PORT = 56789
	BUFSIZE = 1024
	message = sys.argv[1]
	ADDR = (HOST,PORT)
	clientSocket = socket(AF_INET, SOCK_STREAM)
	clientSocket.bind(('127.0.0.1',0))
	try:
		clientSocket.connect(ADDR)
	
		sbuff = unicode(message, 'utf-8')
		clientSocket.send(message)
		print('송신 {0}'.format(message))

		rbuff = clientSocket.recv(1024)
		received= str(rbuff)
		print('수신 : {0}'.format(received))
	finally:
		clientSocket.close()
