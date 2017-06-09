import pymongo
import json
from socket import *

from select import *

import sys


from pymongo import MongoClient

HOST = ''

PORT = 10000

BUFSIZE = 1024

ADDR = (HOST,PORT)

serverSocket = socket(AF_INET, SOCK_STREAM)

client = MongoClient()

db_weather = client.weather

collection = db_weather.now

json_val= json.dumps(collection.find_one({},{'_id':0}))

serverSocket.bind(ADDR)
print('bind')

serverSocket.listen(100)
print('listen')

clientSocket, addr_info = serverSocket.accept() 

print('accept')

clientSocket.close()
serverSocket.close()

print('close')


print json_val
