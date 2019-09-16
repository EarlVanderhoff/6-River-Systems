#!/usr/bin/env python
import os
import json
import time
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def background_thread():
    """Server generated events"""
    count = 0
    while True:
        socketio.sleep(1)
        # look for all executed files
        lookin = os.path.join("/home/elitheiceman/CYTEC/configs/")
        delineate = "Executed"
        fils = filesAre(lookin, delineate)
        if not fils == "nada":
            for fil in fils:
                # translate contents of file to a server message
                cmdsRaw = readFile(fil)
                # delete file
                deleteFile(fil)
                dict = []
                cmds = cmdsRaw.split(',')
                for cmd in cmds:
                    if len(cmd) < 6:
                        continue
                    cmd = cmd.strip()
                    cmdParts = cmd.split()
                    chassis = cmdParts[0][-1:]
                    dict = loadConfig(chassis)
                # send message
                socketio.emit('submit_response',dict,namespace = '/test',broadcast=True)
                time.sleep(2)
                
                

# return matching files from specified directory
def filesAre(pathname, delineator):
    fils = []
    for file in os.listdir(pathname):
        if "Executed" in file:
            fils.append(devFullPath(file))
    if len(fils) > 0:
        return fils
    return "nada"

# default config path
def devFullPath(fil):
    wrkPath = "/home/elitheiceman/CYTEC/configs/"
    return os.path.join(wrkPath,fil)

# delete file
def deleteFile(filename):
    try:
        os.remove(filename)
        return True
    except:
        return False



# reads file contents
def readFile(filename):
    try:
        f = open(filename, "r")
        contents = f.read()
        f.close
        return contents
    except:
        return "FNF"


# save file
def saveFile(filname, filetext):
    try:
        with open(filname, 'w') as f:
            f.write(filetext)
            f.close()
    except:
        return False


# append file
def appendFile(filnam, filtext):
    try:
        with open(filnam, 'a') as f:
            f.write(filtext)
            f.close()
    except:
        return False


# creates a {name:XXX, number:N} dictionary for each source
# and puts them into an ordered list
def sourcesDict(strString):
   srcList = []
   sources = strString.split('\n')
   for source in sources:
      if not ":" in source: continue
      source = source.replace("'","")
      srcArr = source.split(":")
      tempDict = {"name":srcArr[1], "number":srcArr[0]}
      srcList.append(tempDict)
   tempDict = {"name":"unlatch_ALL", "number":str(len(srcList) + 1)}
   srcList.append(tempDict)
   dictlen = len(srcList)
   for n in range(1, 10-dictlen):
       tempDict = {"name":"unassigned", "number":str(dictlen + n)}
       srcList.append(tempDict)
   return srcList


# creates a {name:XXX, assignment:N} dictionary for each shelf
# and puts them into an ordered list
def shelvesDict(strString, rck):
    shelvesList = []
    tempDict = {"name":"rack","number":rck}
    shelvesList.append(tempDict)
    sources = strString.split('\n')
    for intN in range(9):
        for source in sources:
            if not ':' in source: continue
            source = source.replace("'","")
            srcArr = source.split(':')
            numPart = int(srcArr[0])
            if numPart == intN:
                assign = srcArr[1]
                descript = srcArr[2]
                tempDict = {"name": descript, "number": assign}
                shelvesList.append(tempDict)
    return shelvesList    


# develops the list of dictionaries to configure the user's webpage
# the first one is the rack assignment (1-X, max 8)
# followed by the shelf assignments (1-X, max 9 - includes at least one unlatched option)
# and finally the source names (1-X, max 8)
def loadConfig(rackNo):
   # source dictionary
   sourcesFil = devFullPath("sources.txt")
   srcDicts = sourcesDict(readFile(sourcesFil))
   # shelf list of dictionaries
   shelfFile = devFullPath('rack_' + rackNo + '.txt')
   shelfString = readFile(shelfFile)
   theseDicts = shelvesDict(shelfString, rackNo)
   for thisdict in srcDicts:
       theseDicts.append(thisdict)
   return theseDicts 


# reads the rack number from the web submitted dataset
def getRack(dicts):
    rack = '1'
    for thisdict in dicts:
        if thisdict['name'] == 'rack': return thisdict['number']
    return rack


# all <SELECT> settings are transmitted
# this routine compares those transmitted settings against existing settings
# to determine which settings are new, and therefore the intended commands(s)
def commandFilter(webList, rack, refresh):
    # determine which rack file
    rackFileName = devFullPath('rack_' + rack + '.txt')
    # get applicable shelve information
    shelfstring = readFile(rackFileName)
    shelvesLst = shelvesDict(shelfstring,rack)  
    # replace each shelve's dataset with the information received from the website
    # keeping the order intact
    cmdList = []
    '''for intN in range(len(shelvesLst)):
        memEntry = shelvesLst[intN]
        nam = memEntry['name']
        num = memEntry['number'] 
        if 'rack' in nam: continue
        for webEntry in webList:
            if not refresh:
                if webEntry['name'].lower() == nam.lower() and webEntry['number'] != num:
                    # always save the new assignement
                    assignment = webEntry['number']
                    cmdList.append({'shelf':str(intN-1), 'assignment':assignment})  
            else:
                if webEntry['name'].lower() == nam.lower():
                    # always save the new assignement
                    assignment = webEntry['number']
                    cmdList.append({'shelf':str(intN-1), 'assignment':assignment})'''  

    for intN in range(1, len(shelvesLst)):
        if  refresh or (webList[intN]['number'] != shelvesLst[intN]['number']):
            cmdList.append({'shelf':str(intN-1), 'assignment':webList[intN]['number']})


    return cmdList


# convert dictionary strings to CYTEC command strings
def commConvert(rk, cmds, exclusive):
    excl = 'X' if exclusive else ''
    fullCommand = ''
    for cmd in cmds:
        if cmd['assignment'] == None:
            cmd['assignment'] = '-1'
        commandString = excl + 'L'+ str(rk) + ' ' + cmd['shelf'] + ' ' + cmd['assignment']
        fullCommand += ',' + commandString
    if not fullCommand == '': 
        appendFile(devFullPath("cmdfile.txt"),fullCommand)

def getExclusive(message):
    excl = message[0]['value']
    message.pop(0)
    return excl

def getRefreshAll(message):
    refr = message[0]['value']
    message.pop(0)
    return refr


# index event
@app.route('/')
def index(rackstring='0'):
    thisdict =loadConfig(rackstring)
    return render_template('index.html', context=thisdict, async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
        {'data': message['data'], 'count': session['receive_count']})


# rack selection event
@socketio.on('rackselect_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    #index(message['rack'])
    thisdict =loadConfig(message['rack'])
    emit('rack_response', thisdict)
 


# submit button event
@socketio.on('submit_event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    refreshAll = getRefreshAll(message)
    exclusive = getExclusive(message)
    rack = getRack(message)
    # update 
    commandList = commandFilter(message, rack, refreshAll)
    #convert commandlist to standard commands and append cmdfile
    if len(commandList) >0:
        appendStr = commConvert(rack, commandList, exclusive)
    time.sleep(len(commandList))
    # HANDLED BY THE BACKGROUND_THREAD THAT PICKS UP ALL CHANGES EXECUTED BY THE STATE MACHINE
    #emit('submit_response', message, broadcast=True)


@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()


    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':    
    IPAddr = '192.168.200.111'
    socketio.run(app, host=IPAddr)#, debug=True)
