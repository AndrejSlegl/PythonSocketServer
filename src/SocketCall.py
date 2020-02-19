'''
Created on 18. feb. 2020

@author: Andrej
'''

import asyncio
import json
from threading import Timer

class SocketMessage(object):
    def __init__(self, msgId, userId, message):
        self.msgId = msgId
        self.userId = userId
        
        obj = json.loads(message)
        obj['id'] = msgId
        self.message = json.dumps(obj)


class SocketConnection(object):
    def __init__(self, socket, userId):
        self.socket = socket
        self.userId = userId
        self.messageQueue = asyncio.Queue()
        self.sendTask = asyncio.create_task(self.sendWorker())
    
    async def sendWorker(self):
        while True:
            try:
                message = await self.messageQueue.get()
                await self.socket.send(message)
                self.messageQueue.task_done()
            except Exception as err:
                print('Send exception: ' + err)
                break
    
    def send(self, msg: SocketMessage):
        self.messageQueue.put_nowait(msg.message)


class SocketCall(object):
    def __init__(self, callId):
        self.callId = callId
        self.sockets = []
        self.messages = []
        self.removeTimer = Timer(0, None)
    
    def addSocket(self, socket, userId):
        conn = SocketConnection(socket, userId)
        self.sockets.append(conn)
        return conn
        
    def removeSocket(self, socketConnection):
        if self.sockets.count(socketConnection) > 0:
            self.sockets.remove(socketConnection)
            return True
        else:
            return False
        
    def hasSockets(self):
        return len(self.sockets) > 0
        
    def processMessage(self, socketConnection, message):
        msgId = len(self.messages) + 1
        msg = SocketMessage(msgId, socketConnection.userId, message)
        self.messages.append(msg)
        
        for s in self.sockets:
            if s != socketConnection:
                s.send(msg)
                
    def sendCachedMessages(self, socketConnection: SocketConnection, lastId: int):
        msgCount = len(self.messages)
        i = lastId
        while i < msgCount:
            msg = self.messages[i]
            i += 1
            if msg.userId != socketConnection.userId:
                socketConnection.send(msg)
        