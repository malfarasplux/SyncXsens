
#Program to explore Synchrony via 2 BITalino 1-axis ACC Sensors (A5, A6) and sound feedback
from __future__ import division

import socket
import json
import threading
import select
import queue
import pandas as pd
import numpy as np
import bitalino
import time

# Mido imports
import mido
# Pynput imports
from pynput.keyboard import Key, Listener

class bitalino_data(object):
    def __init__(self):
        self.channel_id = ['ind', 'da', 'db', 'dc', 'dd', 'ACC1','ACC2']
        self.nchannels = len(self.channel_id)
        self.data = []
    def val(self, ch_name):
        try :
            i = self.channel_id.index(ch_name)
            return self.data.values[:,i]
        except:
            print("Non-existent ch_name", ch_name)
            return np.array([-1])

# Global
kcounter = 0
port = mido.open_output('loopMIDI Port 1')
current_note = 72
bit1 = bitalino_data()

def show_menu():
    for id in list(MENU_INPUT.keys()):
        print(str(id) + ' | ' + MENU_INPUT[id])

def server_request(action):
    if action == '0':
        print("Listing devices (print needed in code)")
        return 'devices'
    elif action == '1':
        return 'start'
    elif action == '2':
        return 'stop'
    else:
        return ''

# TCP client class
class TCPClient(object):
    global port
    global current_note

    def __init__(self):
        self.tcpIp = ''
        self.tcpPort = 5555
        self.buffer_size = 99999

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inputCheck = []
        self.outputCheck = []
        self.isChecking = False
        self.isAcquiring = False
        self.msgQueue = queue.Queue()
        self.txtFile = SaveAcquisition()
        self.flipPWM = False
        self.dark = False

    def connect(self):
        self.socket.connect((self.tcpIp, self.tcpPort))
        self.outputCheck.append(self.socket)
        self.isChecking = True

    def start(self):
        thread = threading.Thread(target=self.msgChecker)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.isChecking = False
        self.socket.close()

    def msgChecker(self):
        global bit1
        scaleFactor = 5
#        bit1 = bitalino_data()
        while self.isChecking:
            readable, writable, exceptional = select.select(self.inputCheck, self.outputCheck, self.inputCheck)
            for s in readable:
                message = s.recv(self.buffer_size)
                if not self.isAcquiring:
#                    print(message)
                    self.inputCheck = []
                    message = ""
                else:
                    # Print when acquiring (15@100Hz, 150@1000hz instances)
#                    print(message)
                    message = json.loads(message.decode('utf8'))
#                    print("json loaded")
                    message = message["returnData"]
                    if not self.txtFile.getHasHeader():
                        newLine = json.dumps(message) + "\n"
                        self.txtFile.addData(newLine)
                        print("json txt header")

                    else:
                        dataframe = []
                        for device in list(message.keys()):
                            dataframe.append(pd.DataFrame(message[device]))

                        # Convert the list into a pandas.core.frame.DataFrame
                        dataframe = pd.concat(dataframe, axis=1, ignore_index=True)
                        # print(dataframe)

                        # Store and normalise data
                        bit1.data = dataframe
                        bit1.ACC1 = (bit1.val("ACC1")-512)/1024
                        bit1.ACC2 = (bit1.val("ACC2")-512)/1024

                        avg1 = np.mean(bit1.ACC1)
                        avg2 = np.mean(bit1.ACC2)
                        dsync = (avg1 - avg2)
                        avgd = np.mean(dsync)
                        print ("%3.5f %3.5f %3.5f" % (avg1, avg2, avgd))

                        # Manipulate MIDI Pitch
                        pitchval = int(round((mido.MAX_PITCHWHEEL-1) * avgd * scaleFactor))
                        if pitchval > mido.MAX_PITCHWHEEL:
                            pitchval = mido.MAX_PITCHWHEEL
                        elif pitchval < (-1*mido.MAX_PITCHWHEEL):
                            pitchval = -1*mido.MAX_PITCHWHEEL
                        port.send(mido.Message('pitchwheel', pitch = pitchval, time = 90))

                        for line in dataframe.values:
                            self.txtFile.addData('\n')
                            self.txtFile.addData(",".join([str(x) for x in line]))

            for s in writable:
                try:
                    next_msg = self.msgQueue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    print("send ")
                    self.socket.send(next_msg.encode('utf-8'))

            for s in exceptional:
                print("exceptional ", s)

    def addMsgToSend(self, data):
        self.msgQueue.put(data)
        if self.socket not in self.outputCheck:
            self.outputCheck.append(self.socket)
        if self.socket not in self.inputCheck:
            self.inputCheck.append(self.socket)

    def setIsAcquiring(self, isAcquiring):
        self.isAcquiring = isAcquiring
        if self.isAcquiring:
            self.txtFile = SaveAcquisition()
            self.txtFile.start()
        else:
            self.txtFile.stop()

class SaveAcquisition(object):
    def __init__(self):
        self.fileTxt = None
        self.hasHeader = False

    def start(self):
        self.fileTxt = open("mytcpACC_Acquisition.txt", "w")

    def addData(self, data):
        self.fileTxt.write(data)
        self.hasHeader = True

    def stop(self):
        self.fileTxt.close()

    def getHasHeader(self):
        return self.hasHeader

def on_press(key):
    global kcounter
    global current_note

    if key == Key.shift:
        print('{0} pressed'.format(key))
        print (kcounter)
        kcounter = kcounter + 1
        if kcounter == 1:
            pass

def on_release(key):
    global kcounter
    global current_note


    if key == Key.shift:
        print('{0} release'.format(key))
        if kcounter != 0:
            kcounter = 0
            noteSound = False

    if key == Key.esc:
        # Stop keyboard listener
        return False


##################################################################################################
##################################################################################################
# BITalino OpenSignals(r) TCP client to get acquisition data
# Mido instructions send MIDI chords to the virtual port defined
# Code tested in Win10 via a loopMIDI virtual port mapped to Dexed


if __name__ == "__main__":
    MENU_INPUT = {1: 'Acquisition',
                  2: 'Stop',
                  3: 'Exit'
                  }
    try:
        thread_list = []
        CONNECTION = TCPClient()
        CONNECTION.connect()
        CONNECTION.start()

        # Define the mido basic chord
        chord_notes = [72,76,79]
        while True:
            show_menu()
            user_action = str(input('Acquisition(1), Stop(2), Exit(3): '))
            if user_action == '1':
                CONNECTION.setIsAcquiring(True)
                for note in chord_notes:
                    port.send(mido.Message('note_on', note = note, velocity = 80, time = 0))


            elif user_action == '2':
                CONNECTION.setIsAcquiring(False)
                for note in chord_notes:
                    port.send(mido.Message('note_off', note = note, velocity = 80, time = 960))


            elif user_action == '3':
                try:
                    CONNECTION.setIsAcquiring(False)
                except:
#                    print("set acquire False not possible")
                    pass
                CONNECTION.stop()
                break
            new_msg = server_request(user_action)
            CONNECTION.addMsgToSend(new_msg)

        print("END")
    finally:
        port.close()
