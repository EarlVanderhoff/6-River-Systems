#!/usr/bin/env python3
"""
This app runs on commandline.
It receives user input
It creates cmdfile.txt and/or appends the text with the next command
"""
import os
import time


CMTSArray = ['Casa_(ns1.srv.eng.cv.net)', 'Cisco10K_(uBR102.cmts.eng.cv.net)', 'Arris_E6K_(cer101.cmts.eng.cv.net)',
             'CBR-8_(cBR101.cmts.eng.cv.net)', 'Gainspeed_(cdnt101.cmts.eng.cv.net)', 'XXX_(cdntXXX.cmts.eng.cv.net)',
             'Unlatch_ALL']
SitesArray = ['Rack 0 (leftmost rack)', 'Rack 1', 'Rack 2', 'Rack3', 'Rack 4', 'Rack 5 (rightmost rack)']

# Develop file path
def devfullPath(text):
    wrkPath = "/home/elitheiceman/CYTEC/configs/"
    return os.path.join(wrkPath,text)

# is it an integer or character string
def IsItInteger(digit):
    try:
        num = int(digit)
        return num
    except:
        return -1


# build a null commandset - all unlatched
def buildAllUnlatched(StationID):
    CurrentSettings = 'L' + str(StationID) + ' 0 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 1 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 2 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 3 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 4 -1' + ','
    CurrentSettings += 'L' + str(StationID) + ' 5 -1'
    return CurrentSettings


def getComboSettings(intStation):
    CurrentSite = SitesArray[intStation]
    CurrentSiteFile = "RacksNStations_" + CurrentSite + ".txt"
    CurrentSettings = readFile(CurrentSiteFile)
    if CurrentSettings == "FNF": CurrentSettings = buildAllUnlatched(intStation)
    shelfArray = CurrentSettings.split(',')
    ComboSettings = []
    for eachShelf in shelfArray:
        if len(eachShelf) < 6: continue
        newShelf = eachShelf[5:]
        if newShelf == -1: newShelf = len(SitesArray) - 1
        ComboSettings.append(int(newShelf))
    return ComboSettings


# save file
def saveFile(filnam, filtext):
    try:
        with open(filnam, 'w') as f:
            f.write(filtext)
            f.close()
    except:
        return False


# list files in directory
def getMemoryFiles():
    files = os.listdir()
    files_Memory = [i for i in files if 'Rack_' in i]
    return files_Memory


# reads file contents
def readFile(filename):
    try:
        f = open(filename, "r")
        contents = f.read()
        f.close
        return contents
    except:
        return "FNF"


def appendFile(filename, txt):
    try:
        f = open(filename, "a+")
        f.write(txt)
        f.close()
        return True
    except:
        return False


# Main Script
# ----------------------------------------------------------#
print("Welcome to the Cytec Switching System Script!")

quit = False
while (quit is False):
    formatErr = ''
    userInput = input("Enter a command (H for Help or Q to quit): ")
    userInput = userInput.lower()
    if userInput == 'q':
        quit = True
        continue
    elif userInput == 'h':
        print('')
        print('    All commands have the following parts:')
        print('    FUNCTION => Latch (L) or Unlatch  All (U)')
        print('    Chassis number => 0 to 4, followed by a <SPACE>')
        print('    Destinatoin/Shelf Number => 0 to 7, followed by a <SPACE>')
        print('    Source/CMTS Number => 0 to 7')
        print('')
        print('    example:')
        print('    Latch, for Chassis(Rack) 0, Destination(Shelf) #5, to Source(CMTS) # 1')
        print('    L0 5 1')
        print('')
        continue
    else:
        if not (len(userInput) == 6 and (not len(userInput) == 7)):
            formatErr = '    Comand must be 6 or 7 characters in length'
        else:
            firstchar = userInput[:1]
            inputArray = userInput.split()
            if not len(inputArray) == 3:
                formatErr = '    There must be exactly three sections, separated by spaces. Example: L0 5 1'
            else:
                ChassisNum = IsItInteger(inputArray[0][1:])
                DestNum = IsItInteger(inputArray[1])
                SourceNum = IsItInteger(inputArray[2])
                if not firstchar =='l' and not firstchar =='u':formatErr = '    First character must be either L or U'
                elif not len(inputArray[0]) == 2:formatErr = '    Command must start with either L or U, followed by a single digit Chassis number'
                elif not ChassisNum > -1 or not ChassisNum < 6:formatErr = '    Chassis Number must be 0-5'
                elif not DestNum > -1 or not DestNum < 8: formatErr = '    Destination/Shelf (middle section), must be a number between 0 and 8'
                elif not SourceNum > -1 or not SourceNum < 8: formatErr = '    Source/CMTS (last secton), must be a number between 0 and 7'

    if not formatErr == '':
        print(formatErr)
    elif not userInput == 's':
        written = False
        while written is False:
            written = appendFile(devfullPath('cmdfile.txt'), userInput + ",")
        time.sleep(2.5)


