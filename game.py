from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence, Func
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from panda3d.core import Point3, CollisionBox, CollisionNode, CollisionHandlerQueue, CollisionTraverser
from panda3d.core import QueuedConnectionManager, QueuedConnectionListener, QueuedConnectionReader, PointerToConnection, NetAddress, NetDatagram
import random

SERVER_PORT = 9099
SCALE_X = 8
SCALE_Y = 6
MOUSE_MULTIPLIER = 3.0

'''
KEYS= {  # for documentation purposes, inherited from posegameclient.py
  'nose': 17,
  'left ear': 1,
  'right ear': 2,
  'left eye': 3,
  'right eye': 4,
  'left shoulder': 5,
  'right shoulder': 6,
  'left elbow': 7,
  'right elbow': 8,
  'left wrist': 9,
  'right wrist': 10,
  'left hip': 11,
  'right hip': 12,
  'left knee': 13,
  'right knee': 14,
  'left ankle': 15,
  'right ankle': 16
}
'''

EDGES = (
    (17, 3),  #('nose', 'left eye'),
    (17, 4),  #('nose', 'right eye'),
    (17, 1),  #('nose', 'left ear'),
    (17, 2),  #('nose', 'right ear'),
    (1, 3),  #('left ear', 'left eye'),
    (2, 4),  #('right ear', 'right eye'),
    (3, 4),  #('left eye', 'right eye'),
    (5, 6),  #('left shoulder', 'right shoulder'),
    (5, 7),  #('left shoulder', 'left elbow'),
    (5,11),  #('left shoulder', 'left hip'),
    (6, 8),  #('right shoulder', 'right elbow'),
    (6,12),  #('right shoulder', 'right hip'),
    (7, 9),  #('left elbow', 'left wrist'),
    (8,10),  #('right elbow', 'right wrist'),
    (11,12), #('left hip', 'right hip'),
    (11,13), #('left hip', 'left knee'),
    (12,14), #('right hip', 'right knee'),
    (13,15), #('left knee', 'left ankle'),
    (14,16)  #('right knee', 'right ankle'),
)

class MyApp(ShowBase):
    
    activeConnections = []
    triggerScale = 40 # The higher the lower probability to generate new objects / generates one after longer time / easier level
    objectsDesired = 5
    objects = []
    score = 0
    
    def __init__(self):
        ShowBase.__init__(self)

        # Listen for network connection from posenet clients
        cManager = QueuedConnectionManager()
        self.cListener = QueuedConnectionListener(cManager, 0)
        self.cReader = QueuedConnectionReader(cManager, 0)
        # cWriter = ConnectionWriter(cManager, 0)
        port_address = SERVER_PORT #No-other TCP/IP services are using this port
        backlog = 1000 #If we ignore 1,000 connection attempts, something is wrong!
        tcpSocket = cManager.openTCPServerRendezvous(port_address,backlog)
        self.cListener.addConnection(tcpSocket)
        self.taskMgr.add(self.tskListenerPolling, "Poll the connection listener", -39)
        self.taskMgr.add(self.tskReaderPolling, "Poll the connection reader", -40)

        # Disable the camera trackball controls.
        self.disableMouse()

        self.background = OnscreenImage(parent=self.render2dp, image="background.png") # Load an image object
        self.cam2dp.node().getDisplayRegion(0).setSort(-20) # Force the rendering to render the background image first (so that it will be put to the bottom of the scene since other models will be necessarily drawn on top)

        # GUI
        self.scoreText = OnscreenText(text='0', fg=(1,0.5,0.8, 1),pos=(1.05, 0.85), scale=0.2)

        # Load the environment model.
        self.scene = self.loader.loadModel("models/yup-axis")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(1., 1., 1.)
        self.scene.setPos(-8, 42, 0)

        self.punch = self.loader.loadModel("models/box")
        self.punch.reparentTo(self.render)
        self.punch.setScale(0.2, 2., 0.2)
        self.punch.setPos(0, 15, 0)
        colliderNodePath = self.punch.attachNewNode(CollisionNode('cnode'))
        colliderNodePath.setPythonTag("owner", self.punch)
        colliderNodePath.node().addSolid(CollisionBox(Point3(0.5,0.5,0.5), 3.5,0.5,3.5))
        # colliderNodePath.show()
        self.traverser = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.traverser.addCollider(colliderNodePath, self.queue)

        # Add the moveCameraTask procedure to the task manager.
        self.taskMgr.add(self.moveObjectsTask, "moveObjectsTask")
        self.taskMgr.add(self.moveCameraTask, "moveCameraTask")

    def objectBumped(self,obj):
        if obj in self.objects:
            self.objects.remove(obj)
            obj.delete()

    def moveObjectsTask(self, task):
        if len(self.objects) < self.objectsDesired and random.randint(1, self.triggerScale) < (self.objectsDesired - len(self.objects)):
            if random.randint(1, 5) == 1:
                actor = Actor("models/frowney")
                points = -5
            else:
                actor = Actor("models/smiley")
                points = 1
            actor.reparentTo(self.render)
            x = random.random()*SCALE_X-SCALE_X/2
            y = random.random()*SCALE_Y-SCALE_Y/2
            actor.setPos(x, 100, y)
            actorInterval = actor.posInterval(2.0, Point3(x, -15, y))
            cb = CollisionBox(0, 1.0, 1.0, 1.0)
            colliderNodePath = actor.attachNewNode(CollisionNode('cnode'+str(x)))
            colliderNodePath.setPythonTag("owner", actor)
            colliderNodePath.setPythonTag("points", points)
            # colliderNodePath.show()
            colliderNodePath.node().addSolid(cb) # Enable collision
            mySequence = Sequence(actorInterval, Func(self.objectBumped, actor))
            mySequence.start()
            self.objects.append(actor)
        return Task.cont

    def moveCameraTask(self, task):
        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            self.camera.setPos(x * MOUSE_MULTIPLIER, 0, y * MOUSE_MULTIPLIER)
            # self.punch.setPos(x*10, 15, y*10)

        self.traverser.traverse(self.render) # Check if object was punched
        for entry in self.queue.entries:
            obj = entry.getIntoNodePath()
            actor = obj.getPythonTag("owner")
            points = obj.getPythonTag("points")
            self.objects.remove(actor)
            actor.delete()
            self.score += points
            self.scoreText.setText(str(self.score))
        return Task.cont


    def tskListenerPolling(self,taskdata):
        if self.cListener.newConnectionAvailable():

            rendezvous = PointerToConnection()
            netAddress = NetAddress()
            newConnection = PointerToConnection()

            if self.cListener.getNewConnection(rendezvous,netAddress,newConnection):
                newConnection = newConnection.p()
                self.activeConnections.append(newConnection) # Remember connection
                self.cReader.addConnection(newConnection)     # Begin reading connection
                print("New connection")
        return Task.cont

    def tskReaderPolling(self, taskdata):
        if self.cReader.dataAvailable():
            datagram = NetDatagram() 
            if self.cReader.getData(datagram):
                self.draw_pose(datagram)
        return Task.cont

    def draw_pose(self, datagram):
        scale_x, scale_y = SCALE_X / 320, SCALE_Y / 240
        xys = {}
        it = PyDatagramIterator(datagram)
        while True:
            label = it.getUint8()
            if label == 255: break  # End of datagram
            ky = it.getFloat64()
            kx = it.getFloat64()
            kp_y = (240 - ky) * scale_y
            kp_x = (320 - kx) * scale_x

            xys[label] = (kp_x, kp_y)
            if label == 17:
                self.punch.setPos(kp_x, 15, kp_y)

        # for a, b in EDGES:
            # if a not in xys or b not in xys: continue
            # ax, ay = xys[a]
            # bx, by = xys[b]
            # dwg.add(dwg.line(start=(ax, ay), end=(bx, by), stroke=color, stroke_width=2))

app = MyApp()
app.run()
