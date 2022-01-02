from direct.distributed.PyDatagram import PyDatagram
from panda3d.core import QueuedConnectionManager, ConnectionWriter, NetAddress
import time

SERVER_PORT = 9099 # same for client and server
SERVER_IP = "localhost" #"ha.doma"
TIMEOUT = 3000  # How long, in milliseconds, until we give up trying to reach the server?


class MyApp():

    def __init__(self):
        cManager = QueuedConnectionManager()
        self.cWriter = ConnectionWriter(cManager, 0)
        print("Connecting to tcp://{}:{}, timeout={}".format(SERVER_IP, SERVER_PORT, TIMEOUT))
        self.connection = cManager.openTCPClientConnection(SERVER_IP, SERVER_PORT, TIMEOUT) #openUDPConnection()
        # self.serverAddress = NetAddress()
        # self.serverAddress.setHost(SERVER_IP, SERVER_PORT)
        if self.connection:
            print("Connected")
            count = 0
            while True:
                count += 1
                dgram = self.__createDatagram(count)
                self.cWriter.send(dgram, self.connection)
                time.sleep(1.0)

            # self.cReader.addConnection(self.connection)  # receive messages from server

    def run(self):
        count = 0
        while True:
            count += 1
            dgram = self.__createDatagram(count)
            # if self.connection:
                # self.cWriter.send(dgram, self.connection)
            time.sleep(1.0)
        print("Shutting down")

    def __createDatagram(self, data):
        # Send a test message
        myPyDatagram = PyDatagram()
        myPyDatagram.addUint8(data)
        myPyDatagram.addUint8(data)
        myPyDatagram.addUint8(data)
        return myPyDatagram

    def destroy(self):
        self.cWriter.shutdown()
        self.cManager.closeConnection(self.connection)

app = MyApp()
try:
    # app.run()
    app.destroy()
except SystemExit:
    app.destroy()
