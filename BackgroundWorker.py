#!/usr/bin/env python3
"""
This script runs in the background continuously checking the native cmdfile.txt for requested action
Load cmdfile.txt into memory
Delete cmdfile.txt
Execute commands
"""
import socket
import os
import time
import datetime


CMTSArray = ['Casa_(ns1.srv.eng.cv.net)', 'Cisco10K_(uBR102.cmts.eng.cv.net)', 'Arris_E6K_(cer101.cmts.eng.cv.net)',
             'CBR-8_(cBR101.cmts.eng.cv.net)', 'Gainspeed_(cdnt101.cmts.eng.cv.net)', 'XXX_(cdntXXX.cmts.eng.cv.net)']    
IPAddress = ''
port = 0


# Develop file path
def devfullPath(text):
    wrkPath = "/home/elitheiceman/CYTEC/configs/"
    return os.path.join(wrkPath,text)

# closes the socket elegantly, first freeing resources (shutdown)
# so that any underlying linux or windows process makes the socket instantly re-available
def closeSocket(skt):
    try:
        skt.shutdown()
        skt.close()
    except:
        i = 3

# connects the socket
def connectSocket(skt, IPAddress, port):
    try:
        skt.connect((IPAddress, port))
        return 'OK'
    except Exception as err:
        print(err)
        return err


# Passes the command to the relay
def sendCommand(socket, userInput, ResponseExpected = False):
    userInput = userInput + "\r"
    command = userInput.encode()
    try:
        socket.send(command)
        time.sleep(0.1)
        if ResponseExpected: return(receiveResponse(socket))
        return "OK"
    except Exception as err:
        print('socket error => attempting to reconnect and resend command')
        if connectSocket(socket, IPAddress, port) == 'OK':
            socket.send(command)
            time.sleep(0.1)
            return 'OK'

def receiveResponse(skt):
    #b'11111111\r\n11111111\r\n11111111\r\n11111111\r\n11111111\r\n11111111\r\n11111111\r\n11111111\r\n1\r\n'
    chunks = b''
    eol = False
    while eol is False:
        chunk = skt.recv(2048)
        chunks += chunk
        if "n1\\r\\n" or "n0\\r\\n" in str(chunks):
            eol = True
        if chunk == b'':
            droppedConnection = True
            break
    return(str(chunks))


# clear and latch
def clearInactiveLatches(skt, command):
    # used to clear any existing latch state for the specified rack and shelf
    # before executing the new latch
    # not used for any command except Latch
    # L0 5 0
    commandarray = command.split()
    rack = commandarray[0][1:]
    shelf = commandarray[1]
    CMTS = commandarray[2]
    delim = ""
    newCommand = ""
    latchState = "U"
    # send 4 at a time to save time (51 total characters are allowed -  including colons)
    for intCMTS in range(0, 3):
        if str(intCMTS) != CMTS:
            if newCommand != "": delim = ":"
            newCommand += delim + latchState + rack + ' ' + shelf + ' ' + str(intCMTS)
    resp = sendCommand(skt, newCommand)
    time.sleep(.25)
    newCommand = ""
    for intCMTS in range(3, 6):
        if str(intCMTS) != CMTS:
            if newCommand != "": delim = ":"
            newCommand += delim + latchState + rack + ' ' + shelf + ' ' + str(intCMTS)
    resp = sendCommand(skt, newCommand)
    time.sleep(.25)
    newCommand = ""
    for intCMTS in range(6, 8):
        if str(intCMTS) != CMTS:
            if newCommand != "": delim = ":"
            newCommand += delim + latchState + rack + ' ' + shelf + ' ' + str(intCMTS)
    resp = sendCommand(skt, newCommand)


# build a null commandset - all unlatched
def buildAllUnlatched(StationID):
    CurrentSettings = 'L' + str(StationID) + ' 0 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 1 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 2 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 3 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 4 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 5 -1'
    return CurrentSettings


def get_RackSettings(intRack):
    # get file name
    CurrentSiteFile = 'rack_' + str(intRack) + '.txt'
    CurrentSiteFile = devfullPath(CurrentSiteFile)
    # read existing settings into an array
    CurrentSettings = readFile(CurrentSiteFile)
    if CurrentSettings == "FNF": 
        return "FNF"#CurrentSettings = buildAllUnlatched(intStation)
    currSettArr = CurrentSettings.split('\n')
    for intN in range(len(currSettArr)):
        set =currSettArr[intN] 
        currSettArr[intN] = set.strip()
    return currSettArr


def update_RackSettings(currSettArr, intShelf, intCMTS):
    # read applicable shelf settings
    thisShelf = currSettArr[intShelf].strip()
    currShelfArr = thisShelf.split(':')
    # apply new settings to the shelf
    newShelf = currShelfArr[0] + ':' + str(intCMTS) + ":" + currShelfArr[2]
    currSettArr[intShelf] = newShelf
    return currSettArr

def save_RackSettings(rackN, newSetts):
    #build the string
    fullString= ''
    delim = ''
    for set in newSetts:
        if not fullString == '': delim = '\n'
        fullString += delim + set
    CurrentSiteFile = 'rack_' + str(rackN) + '.txt'
    CurrentSiteFile = devfullPath(CurrentSiteFile)
    saveFile(CurrentSiteFile, fullString)


# save file
def saveFile(filnam, filtext):
    try:
        with open(filnam, 'w') as f:
            f.write(filtext)
            f.close()
    except:
        return False


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

 
# derives the rack number from the command string contents
def getRackNo(cmdString):
    newCmdArr = cmdString.split()
    firstPart = newCmdArr[0]
    return int(firstPart[1:])


# derives the shelf number from the command string contents
def getShelfNo(cmdString):
    newCmdArr= cmdString.split()
    return int(newCmdArr[1])


# derives the CMTS number from the command string contents
def getCMTSNo(cmdString):
    newCmdArr = cmdString.split()
    return int(newCmdArr[2])


# create the file-based update to the web-based system
def msgInABottle(fileString):
    now = str(datetime.datetime.now())[:19]
    now = now.replace(":","_")
    fil = devfullPath("Executed " + now + ".txt")
    saveFile(fil, fileString)


    


# Main Script
# ----------------------------------------------------------#

IPAddress = "10.0.0.144"
port = 8080
skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = connectSocket(skt, IPAddress, port)
if not connected == 'OK':
    print(connected)
    print('exiting BackgroundWorker.py')
    exit()
resp = sendCommand(skt, "e 0 73") # echo off

#Test section - for proof ONLY
'''resp = sendCommand(skt, "a 1 73",True) # answer-back on
time.sleep(.5)
resp = sendCommand(skt, "S0", True)'''
#Test section - for proof ONLY

resp = sendCommand(skt, "a 0 73")
intrack = 0
intsrc = 0
inquit = False
cycleinterval = 1
cmdstring = ''
while (inquit is False):
    if cmdstring == '':
        # read command file with fault tolerance
        red = False
        begin = time.time()
        while red is False:
            # config Path
            cmdPath = devfullPath("cmdfile.txt")
            cmdstring = readFile(cmdPath)
            if cmdstring == "" or cmdstring == "FNF":
                time.sleep(1)
                if begin - time.time() > 60:
                    # get the hardware state every minute
                    begin = time.time()
                    resp = sendCommand(skt, "a 1 73",True) # answer-back on
                    time.sleep(.1)
                    state = sendCommand(skt, "S0", True)
                    time.sleep(.1)
                    resp = sendCommand(skt, "a 0 73") # answer-back off
            else:
                deleteFile(cmdPath)
                red = True
        # build the command array
        cmdarray = cmdstring.split(',')
        # send out each command until done
        while (len(cmdarray) > 0):
            newcommand = cmdarray.pop()
            newcommand = newcommand.strip()
            latchstate = newcommand[:1].upper()
            excl = False
            if 'X' in newcommand:
                excl = True
            newcommand = newcommand.replace('X', '')
            if newcommand == '': continue
            try:
                rackNo = getRackNo(newcommand)
                shelfNo = getShelfNo(newcommand)
                CMTSNo = getCMTSNo(newcommand)
            except:
                print('')
                print('    ' + newcommand.upper() + ' is malformed')
                print('')
                continue
            sendCMTSNo = CMTSNo
            if sendCMTSNo > len(CMTSArray)-1:
                sendCMTSNo = -1
                newcommand = 'L' + str(rackNo) + ' ' + str(shelfNo) + ' ' + str(sendCMTSNo)
            # Get existing shelf settings for this rack
            currentSettings = get_RackSettings(rackNo)
            if currentSettings == "FNF":
                time.sleep(cycleinterval)
                continue
            # Amend the specific shelf this command calls for
            newSettings = update_RackSettings(currentSettings, shelfNo, CMTSNo)
            #  Save the file
            save_RackSettings(rackNo, newSettings)
            # send the current command
            commstat = ''
            if excl == True or sendCMTSNo == -1:
                clearInactiveLatches(skt, newcommand)
                commstat = 'OK'
            if not sendCMTSNo == -1:
                commstat = sendCommand(skt, newcommand)
            if commstat == 'OK':
                print('')
                print('    ' + newcommand.upper() + ' Executed')
                print('')

            else:
                print(commstat)
            # wait
            time.sleep(cycleinterval)
        msgInABottle(cmdstring)
        cmdstring = ''

skt.close
