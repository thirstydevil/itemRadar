__author__ = 'David Moulder'

from PySide import QtCore, QtGui
from PySide.QtCore import Signal
import logging as log
log.basicConfig(level=log.DEBUG)
import uuid

class RadarGraphicsItem(QtGui.QGraphicsItem):
    """
    TODO :  Want to be able to draw a a simple elipse but have a highlight state and selected state.
      also want to change to colour of the dot based on data saved on the dot.  Like user ratings,
      item classification etc
    """

    def __init__(self, parent=None):
        super(RadarGraphicsItem, self).__init__(parent)
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemIsMovable)
        self.brush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 255, 17))
        self.brushSelected = QtGui.QBrush(QtGui.QColor.fromRgb(102, 204, 255))
        self.pen = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 50), 2)
        self.diameter = 12
        self._selected = False
        self._id = uuid.uuid4()

    def id(self):
        return str(self._id)

    def boundingRect(self, *args, **kwargs):
        return QtCore.QRectF(0-self.diameter / 2, 0 - self.diameter / 2, self.diameter, self.diameter)

    def paint(self, painter, option, widget, **kwargs):
        if self._selected:
            b = self.brushSelected
        else:
            b = self.brush
        if self.isSelected():
            b = self.brushSelected
        painter.setPen(self.pen)
        painter.setBrush(b)
        painter.drawEllipse(self.boundingRect())

    def mousePressEvent(self, event, **kwargs):
        self._selected = True
        self.update()
        return super(RadarGraphicsItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event, **kwargs):
        self._selected = False
        self.update()
        return super(RadarGraphicsItem, self).mouseReleaseEvent(event)


class RadarGraphicsScene(QtGui.QGraphicsScene):
    """
    Reimplemented to access the public methods to do my own thing.  For now, just want mouse access to events
    In the future I think I'll have to link this to a DB or in the 1st place add some serialisation to this,
    more investigation needed
    """
    sceneDoubleClicked = Signal(QtCore.QPointF)
    radarItemClicked = Signal(RadarGraphicsItem)

    def __init__(self, *args, **kwds):
        QtGui.QGraphicsScene.__init__(self, *args, **kwds)
        self.dataModel = RadarItemModel()

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if QGraphicsSceneMouseEvent.button() == QtCore.Qt.LeftButton and \
                QGraphicsSceneMouseEvent.modifiers() == QtCore.Qt.ControlModifier:
            self.sceneDoubleClicked.emit(QGraphicsSceneMouseEvent.scenePos())

        return super(RadarGraphicsScene, self).mouseDoubleClickEvent(QGraphicsSceneMouseEvent)

    def mousePressEvent(self, QGraphicsSceneMouseEvent, **kwargs):
        item = self.itemAt(QGraphicsSceneMouseEvent.scenePos())
        if getattr(item, "id", ""):
            self.radarItemClicked.emit(item)
        return super(RadarGraphicsScene, self).mousePressEvent(QGraphicsSceneMouseEvent)

    def addItem(self, item, **kwargs):
        print self.selectedItems()
        if getattr(item, "id", ""):
            idx = QtGui.QStandardItem(item.id())
            pos = QtGui.QStandardItem("{0},{1}".format(item.scenePos().x(), item.scenePos().y()))
            name = QtGui.QStandardItem(item.id()[:5])
            self.dataModel.appendRow([name, pos, idx])
        super(RadarGraphicsScene, self).addItem(item)



class RadarItemModel(QtGui.QStandardItemModel):
    """
    This scene is to filter items on the radar board.
    """
    def __init__(self, *args, **kwds):
        QtGui.QStandardItemModel.__init__(self, *args, **kwds)



class MainDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(MainDialog, self).__init__(parent)

        self.mainLayout = QtGui.QVBoxLayout()
        self.mainPanelHLayout = QtGui.QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.addLayout(self.mainPanelHLayout)

        self.createRadarBtn = QtGui.QPushButton("New")
        self.deleteRadarBtn = QtGui.QPushButton("Delete")
        btnLayout = QtGui.QHBoxLayout()
        btnLayout.addWidget(self.createRadarBtn)
        btnLayout.addWidget(self.deleteRadarBtn)
        self.leftRadarVLayout =QtGui.QVBoxLayout()
        self.leftRadarVLayout.addLayout(btnLayout)

        self.mainPanelHLayout.addLayout(self.leftRadarVLayout)




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

        self.scene = RadarGraphicsScene(-400,-300,800,600, parent=self)
        self.graphicsView = QtGui.QGraphicsView(self)
        self.graphicsView.setMaximumSize(805, 605)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.mainPanelHLayout.addWidget(self.graphicsView)

        self.itemListView = QtGui.QListView(self)
        self.itemListView.setMaximumHeight(605)
        self.mainPanelHLayout.addWidget(self.itemListView)
        self.itemListView.setModel(self.scene.dataModel)
        #self.itemListView.selectionModel().selectionChanged.connect(self.setSelectedRadarItem)

        self.setupBackground()

        self.scene.sceneDoubleClicked.connect(self.addRadarItem)
        self.scene.radarItemClicked.connect(self.updateRadarAttributes)

    def setSelectedRadarItem(self, *args):
        print args

    def updateRadarAttributes(self, radarItem):
        print "update radar attribute editor on : {0}".format(radarItem.id())

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
            self.scene.addEllipse(0-(diameter/2), 0-(diameter/2), diameter, diameter, backgroundPenRings, backgroundBrush)
            diameter-=ringOffset

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
        e = RadarGraphicsItem()
        e.setPos(scenePos)
        self.scene.addItem(e)
        log.debug("X{0}, Y{1}".format(scenePos.x()-5, scenePos.y()-5))

