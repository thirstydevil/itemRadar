__author__ = 'David Moulder'

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignal
import logging as log
log.basicConfig(level=log.DEBUG)


class RadarQScene(QtGui.QGraphicsScene):
    """
    Reimplemented to access the public methods to do my own thing.  For now, just want mouse access to events
    In the future I think I'll have to link this to a DB or in the 1st place add some serialisation to this,
    more investigation needed
    """
    sceneDoubleClicked = pyqtSignal(QtCore.QPointF)

    def __init__(self, *args, **kwds):
        QtGui.QGraphicsScene.__init__(self, *args, **kwds)

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if QGraphicsSceneMouseEvent.button() == QtCore.Qt.LeftButton:
            self.sceneDoubleClicked.emit(QGraphicsSceneMouseEvent.scenePos())
        return super(RadarQScene, self).mouseDoubleClickEvent(QGraphicsSceneMouseEvent)


class RadarItem(QtGui.QGraphicsItem):
    """
    TODO :  Want to be able to draw a a simple elipse but have a highlight state and selected state.
      also want to change to colour of the dot based on data saved on the dot.  Like user ratings,
      item classification etc
    """
    itemMoved = pyqtSignal()

    def __init__(self, parent=None):
        super(RadarItem, self).__init__(parent)


class MainDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(MainDialog, self).__init__(parent)
        self.setMinimumSize(1024, 1024)
        self.mainLayout = QtGui.QHBoxLayout()
        self.setLayout(self.mainLayout)

        # mainBackground colour pallets
        self.backgroundBrush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 17, 17))
        self.backgroundPenLines = QtGui.QPen(QtGui.QColor.fromRgb(0153, 38, 0, 25), 2)
        self.backgroundPenRings = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 75), 2)
        self.backgroundPenLinesBold = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 80), 2)

        # radar item size on the view
        self.radarItemDiameter = 12

        ## Construct a scene and make sure we set an absolute rect.  If we offset the center od the rect we can fake
        ## the origin to the center of the screen.  Which we can do as we have a fixed radar size
        ## The reason I'm doing this is to easily calculate the distance from the center of the radar to organsie a list
        ## on items with the header data

        self.scene = RadarQScene(-400,-300,800,600, parent=self)
        self.graphicsView = QtGui.QGraphicsView(self)
        self.graphicsView.setMaximumSize(805, 605)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.mainLayout.addWidget(self.graphicsView)

        self.setupBackground()

        self.scene.sceneDoubleClicked.connect(self.addRadarItem)

    def setupBackground(self):
        """
        I was so tempted to just download a nice picture but in the end I manually drew the radar on the canvas
        :return: None
        """
        backgroundBrush = self.backgroundBrush
        backgroundPenLines = self.backgroundPenLines
        backgroundPenRings = self.backgroundPenRings
        diameter = self.scene.width() + self.scene.height() / 2
        ringCount = 10
        ringOffset = diameter / ringCount
        screenPosX = self.scene.width() / 2 * -1
        screenPosY = -self.scene.height() / 2
        numberOfLines = 16
        offset = self.scene.width() / numberOfLines

        # draw the radar circles
        for i in range(ringCount):
            print i
            self.scene.addEllipse(0-(diameter/2), 0-(diameter/2), diameter, diameter, backgroundPenRings, backgroundBrush)
            diameter-=ringOffset
            print diameter

        # overlay the grid
        for i in range(numberOfLines):
            if i not in [0, numberOfLines]:
                l = self.scene.addLine(screenPosX, -300, screenPosX+1, 300, backgroundPenLines)
                ll = self.scene.addLine(-400, screenPosY, 400,screenPosY+1, backgroundPenLines)

                ## Draw the darker center lines
                if screenPosX == 0:
                    l.setPen(self.backgroundPenLinesBold)
                if screenPosY == 0:
                    ll.setPen(self.backgroundPenLinesBold)
            screenPosX += offset
            screenPosY += offset


    def addRadarItem(self, scenePos):
        """
        Only reasonable way to add items is to double click on the screen to add the items.  This is hooked up to the
        signal emitted by the sceneGraph when a user double clicks on the canvas
        :param scenePos: QScenePos
        :return: None
        """
        blackBrush = QtGui.QBrush(QtCore.Qt.green)
        redPen = QtGui.QPen(self.backgroundPenLinesBold)
        e = self.scene.addEllipse(scenePos.x()-5, scenePos.y()-5, self.radarItemDiameter,
                                  self.radarItemDiameter, redPen, blackBrush)
        e.setFlags(QtGui.QGraphicsItem.ItemIsMovable)
        #e.setFlags(QtGui.QGraphicsItem.ItemIsSelectable)
        log.debug("X{0}, Y{1}".format(scenePos.x()-5, scenePos.y()-5))

