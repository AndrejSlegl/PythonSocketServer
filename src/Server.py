'''
Created on 18. feb. 2020

@author: Andrej
'''

import asyncio
import websockets
from SocketCall import SocketCall
from urllib.parse import urlparse, parse_qs

calls = dict()

def onCallTimeout(call):
    if call.hasSockets() == False:
        if calls.pop(call.callId, None) != None:
            print('Removed call: ' + call.callId)

def removeSocket(call, socketConnection):
    socketConnection.sendTask.cancel()
    if call.removeSocket(socketConnection) and call.hasSockets() == False:
        call.removeTimer = asyncio.get_event_loop().call_later(10, onCallTimeout, call)

async def pingConnection(call, socketConnection):
    while True:
        try:
            await asyncio.sleep(10)
            pongWaiter = await socketConnection.socket.ping()
            await asyncio.wait_for(pongWaiter, timeout=10)
        except Exception as err:
            print(f'Ping error: {err}')
            removeSocket(call, socketConnection)
            break

async def newConnection(websocket, path):
    url = urlparse(path)
    callId = url.path
    query = parse_qs(url.query)
    userArray = query.get('user', [])
    lastIdArray = query.get('lastId', [])
    userId = None
    lastId = 0
    
    if len(userArray) > 0 and len(userArray[0]) > 0:
        userId = userArray[0]
    else:
        return
    
    if len(lastIdArray) > 0 and len(lastIdArray[0]) > 0:
        lastId = int(lastIdArray[0])
    
    print(f'New Connection callId: {callId} userId: {userId} lastId: {lastId}')
    
    call = calls.get(callId, None)
    if call == None:
        call = SocketCall(callId)
        calls[callId] = call
        print('Created new call: ' + callId)
    
    call.removeTimer.cancel()
    socketConnection = call.addSocket(websocket, userId)
    call.sendCachedMessages(socketConnection, lastId)
    pingTask = asyncio.create_task(pingConnection(call, socketConnection))
    
    try:
        async for message in websocket:
            print('New message from callId: ' + callId + ' userId: ' + userId + ':\n' + message)
            call.processMessage(socketConnection, message)
            
    except Exception as err:
        print('Error callId: ' + callId + ' userId: ' + userId + '\n' + str(err))
        pingTask.cancel()
        removeSocket(call, socketConnection)
        
asyncio.get_event_loop().run_until_complete(
    websockets.serve(newConnection, '192.168.1.101', 5000))
asyncio.get_event_loop().run_forever()