__author__ = 'David Moulder'
__version__ = "0.9.0"
__date__ = "05/06/2016"

from PySide import QtCore, QtGui
from PySide.QtCore import Signal
import os
import logging as log
import radarAttributeEditorForm
import radarListForm
import radarSelectSceneForm
from radarDBHandle import MongoSceneHandle, RadarScenesTableModel, RadarItemsTableModel, getpass
import random

log.basicConfig(level=log.INFO)

g_ROOT_PATH = os.path.dirname(__file__)
g_RESOURCE_PATH = os.path.join(g_ROOT_PATH, "resources")
g_IMAGES_PATH = os.path.join(g_RESOURCE_PATH, "images")


class RadarGraphicsItem(QtGui.QGraphicsItem):
    """
    TODO :  Want to be able to draw a a simple elipse but have a highlight state and selected state.
      also want to change to colour of the dot based on data saved on the dot.  Like user ratings,
      item classification etc
    """

    radarItemHovered = Signal("")

    def __init__(self, parent=None):
        super(RadarGraphicsItem, self).__init__(parent)
        self.setFlags(QtGui.QGraphicsItem.ItemIsSelectable | QtGui.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.brush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 255, 17))
        self.brushSelected = QtGui.QBrush(QtGui.QColor.fromRgb(255, 255, 255))
        # self.brushSelected = self.brush
        # self.brushHover = QtGui.QBrush(QtGui.QColor.fromRgb(255, 255, 255))
        self.diameter = 12
        self._selected = False
        self._hovering = False
        self.setAcceptHoverEvents(True)
        self._cachePos = None
        self.record = {}
        self._playing = False
        self.tl = QtCore.QTimeLine(50)
        self.tl.setLoopCount(200)
        self.itemAnimation = QtGui.QGraphicsItemAnimation()
        self.itemAnimation.setItem(self)
        self.itemAnimation.setTimeLine(self.tl)
        self.itemAnimation.setScaleAt(1, 1.5, 1.5)

    def play(self):
        if not self.tl.currentValue() > 0:
            self.tl.start()

    def stop(self):
        if self.tl.currentValue() > 0:
            self.tl.stop()
            self.tl.setCurrentTime(0)

    @property
    def dotRect(self):
        if any([self._selected, self._hovering, self.isSelected()]):
            self.diameter = 14
        else:
            self.diameter = 12
        return QtCore.QRectF(0-self.diameter / 2, 0 - self.diameter / 2, self.diameter, self.diameter)

    @property
    def pen(self):
        if any([self._selected, self._hovering, self.isSelected()]):
            return QtGui.QPen(QtGui.QColor.fromRgb(255, 255, 255), 2)
        else:
            return QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 50), 2)

    def cachePosition(self):
        self._cachePos = self.scenePos()

    def hasMoved(self):
        return self._cachePos != self.scenePos()

    def setId(self, id):
        self._id = id

    def updateColour(self, idx, colour):
        if self.id() == idx:
            log.debug("Update Colour")
            self.setColour(colour)
            self.update()

    def setColour(self, qCol):
        self.brush = QtGui.QBrush(qCol)

    def toolTip(self, *args, **kwargs):
        return self.record.get('name', '')[:4] + ".."

    def hoverEnterEvent(self, *args, **kwargs):
        self._hovering = True
        self.update()
        return super(RadarGraphicsItem, self).hoverEnterEvent(*args, **kwargs)

    def hoverLeaveEvent(self, *args, **kwargs):
        """
        I'd like to draw my own tooltip when hovering to help identify hard some dots
        :param args:
        :param kwargs:
        :return:
        """
        self._hovering = False
        self.update()
        return super(RadarGraphicsItem, self).hoverLeaveEvent(*args, **kwargs)

    def id(self):
        return str(self._id)

    def boundingRect(self, *args, **kwargs):
        if not self._hovering:
            return self.dotRect
        else:
            return QtCore.QRectF(0-self.diameter / 2, 0 - self.diameter / 2 -2, self.diameter + 36, self.diameter+4)

    def paint(self, painter, option, widget, **kwargs):
        """
        Custom widget to paint my own dots and react to status updates and when a user is potentially updating it.
        If I use a Db backend then multiple users could be working on the same scene.  Thus we may want to lock an
        item selected by a user.
        :param painter:
        :param option:
        :param widget:
        :param kwargs:
        :return: None
        """

        if self._selected:
            b = self.brushSelected
        else:
            b = self.brush
        # if self.isSelected():
        #     b = self.brushSelected
        if self._hovering:
            # paint the tooltip.  Remember that when painting new things we need to update the boundingRect
            # so that the item redraws correctly.
            b = self.brush
            painter.drawText(QtCore.QPoint( 12, + 4  ) ,self.toolTip())
        painter.setPen(self.pen)
        painter.setBrush(b)
        painter.drawEllipse(self.dotRect)

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
    Reimplemented to access the public methods to do my own thing.
    """
    sceneDoubleClicked = Signal(QtCore.QPointF)
    radarItemClicked = Signal(RadarGraphicsItem)
    radarItemAdded = Signal(RadarGraphicsItem)
    radarItemMoved = Signal(RadarGraphicsItem)

    def __init__(self,*args, **kwargs):
        super(RadarGraphicsScene, self).__init__(*args, **kwargs)
        self.mongoSceneHandle = None
        self.radarItemTableModel = None

        self.backgroundBrush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 17, 17, 50))
        self.backgroundPenLines = QtGui.QPen(QtGui.QColor.fromRgb(0153, 38, 0, 25), 2)
        self.backgroundPenRings = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 75), 2)
        self.backgroundPenLinesBold = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 80), 2)

        self.setupBackground()
        self.setupAnimatedRadar()
        self.attributeEditor = None
        self.listPanel = None

        self._itemDict = {}

    def initScene(self, mongoSceneHandle, attribEditor, listPanel):
        """
        Setup the scene with the data form the db, builds the table model for the views to connect to.
        :param mongoSceneHandle: MongoSceneHandle, RadarAttributeEditor, RadarListPanel
        :return: None
        """
        self.mongoSceneHandle = mongoSceneHandle
        self.sourceModel = RadarItemsTableModel(mongoSceneHandle)
        self.proxyModel = ItemFilterProxyMode(self)
        self.proxyModel.setSourceModel(self.sourceModel)
        self.attributeEditor = attribEditor
        self.listPanel = listPanel
        self.attributeEditor.clearData()
        assert isinstance(self.attributeEditor, RadarAttributeEditor)
        assert isinstance(self.listPanel, RadarListPanel)
        self.listPanel.form.filter_lineEdit.textChanged.connect(self.proxyModel.setFilterRegExp)
        self.listPanel.radarListSelectionChanged.connect(self.selectRadarItemByID)
        self.proxyModel.setFilterKeyColumn(self.sourceModel.columns.index("name"))

        # Add all the items to the scene
        for i in self.mongoSceneHandle.items():
            graphicsItem = RadarGraphicsItem()
            graphicsItem.setId(i["_id"])
            graphicsItem.setPos(i["pos"][0], i["pos"][1])
            graphicsItem.setColour(QtGui.QColor(*i["colour"]))
            graphicsItem.record = i
            self.addItem(graphicsItem)
            self.sourceModel.updateGraphicsItemColour.connect(graphicsItem.updateColour)


    def addItem(self, item):
        idx = getattr(item, 'id', '')
        if idx:
            self._itemDict[str(idx())] = item
        return super(RadarGraphicsScene, self).addItem(item)

    def removeItem(self, item):
        idx = getattr(item, 'id', '')
        if idx:
            self._itemDict.pop(str(idx()), None)
        super(RadarGraphicsScene, self).removeItem(item)

    def setActive(self):
        if self.attributeEditor:
            self.attributeEditor.setGraphicsScene(self)
        if self.listPanel:
            self.listPanel.setGraphicsScene(self)

    def radarItemToProxyIndex(self, item, columnName='name'):
        index = self.radarItemToSourceIndex(item, columnName)
        if index.isValid() and index.model() is self.sourceModel:
            return self.proxyModel.mapFromSource(index)

    def radarItemToSourceIndex(self, item, columnName='name'):
        rowData = self.sourceModel.rowModelIndexFromId(item.id())
        if rowData:
            return rowData[columnName]

    def radarItemToSourceRowIndexData(self, item):
        return self.sourceModel.rowModelIndexFromId(item.id())

    def updateItemRecord(self, item):
        record = self.sourceModel.rawDataFromId(item.id())
        item.record = record

    def selectRadarItemByID(self, scene, idx):
        """
        Handles selecting of radar items in the scene by the item id from mongoDB.  Other views can pass the id
        via a signal.  This slot can then handle the the selection of the items in the scene from the id
        :param idx: str
        :return: None
        """
        # Grab the View from the current Tab and thus dig down into the scene graph.
        # The the method to extract the radarItem.

        if scene is self:
            log.debug("Select Radar Item by ID")
            item = self.itemFromID(idx)
            log.debug("Found GraphicsItem in Radar : {0}".format(item))
            if item:
                # It was difficult to find out the best way to select items in the scene.  This is like drawing
                # a box selection on the viewport and the contained items are selected.
                self.clearSelection()
                painterPath = QtGui.QPainterPath()
                painterPath.addRect(item.boundingRect())
                painterPath.translate(item.scenePos())
                self.attributeEditor.setRadarItem(item)
                self.setSelectionArea(painterPath, QtGui.QTransform())

    def maxRadarDiameter(self):
        return self.width() + self.height() / 2

    def setupBackground(self):
        """
        I was so tempted to just download a nice picture but in the end I manually drew the radar on the canvas
        :return: None
        """
        backgroundBrush = self.backgroundBrush
        backgroundPenLines = self.backgroundPenLines
        backgroundPenRings = self.backgroundPenRings
        diameter = self.maxRadarDiameter()
        topY = diameter / 2 * -1
        topX = diameter / 2 * -1
        bottomX = topX * -1
        bottomY = topY * -1
        ringCount = 10
        ringOffset = diameter / ringCount
        screenPosX = (diameter / 2) * -1
        screenPosY = (diameter / 2) * -1
        numberOfLines = ringCount * 2

        # draw the radar circles
        for i in range(ringCount):
            self.addEllipse(0-(diameter/2), 0-(diameter/2), diameter, diameter, backgroundPenRings, backgroundBrush)
            diameter -= ringOffset

        # overlay the grid
        for i in range(numberOfLines):
            if i not in [0, numberOfLines]:
                l = self.addLine(screenPosX, topX, screenPosX+1, bottomX, backgroundPenLines)
                ll = self.addLine(topX, screenPosY, bottomX, screenPosY+1, backgroundPenLines)

                ## Draw the darker center lines
                if screenPosX == 0:
                    l.setPen(self.backgroundPenLinesBold)
                if screenPosY == 0:
                    ll.setPen(self.backgroundPenLinesBold)
            screenPosX += ringOffset / 2
            screenPosY += ringOffset / 2

    def setupAnimatedRadar(self):
        pen = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 25), 2)
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(0, 150, 150, 25))
        rad = self.maxRadarDiameter() / 2
        self.radarAnimItem = self.addEllipse(0-rad, 0-rad, rad*2, rad*2, pen, brush)
        self.radarAnimItem.setPos(0,0)
        self.radarAnimItem.setSpanAngle(360 * 2)
        self.timeline = QtCore.QTimeLine(5000)
        self.timeline.setEasingCurve(QtCore.QEasingCurve.Linear)
        self.timeline.setLoopCount(0)
        self.timeline.setFrameRange(0, 1)
        self.animclip = QtGui.QGraphicsItemAnimation()
        self.animclip.setItem(self.radarAnimItem)
        self.animclip.setTimeLine(self.timeline)
        self.animclip.setPosAt(0, QtCore.QPointF(0, 0))
        self.animclip.setRotationAt(1, 360)
        self.timeline.start()
        self.timeline.valueChanged.connect(self.itemAnimUpdate)

    def itemAnimUpdate(self, f):
        collidingItems = [i for i in self.collidingItems(self.radarAnimItem) if i in self._itemDict.values()]
        if collidingItems:
            i = random.choice(collidingItems)
            i.play()

        nonCollidingItems = [i for i in self._itemDict.values() if i not in collidingItems]
        for i in nonCollidingItems:
            i.stop()


    def showHideAnimatedRadar(self, state):
        item = getattr(self, "radarAnimItem", None)
        if item:
            if state:
                self.timeline.stop()
                item.hide()
            else:
                item.show()
                self.timeline.start()

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if QGraphicsSceneMouseEvent.button() == QtCore.Qt.LeftButton and \
                QGraphicsSceneMouseEvent.modifiers() == QtCore.Qt.ControlModifier:
            self.addRadarItem(QGraphicsSceneMouseEvent.scenePos())
        return super(RadarGraphicsScene, self).mouseDoubleClickEvent(QGraphicsSceneMouseEvent)

    def mousePressEvent(self, QGraphicsSceneMouseEvent, **kwargs):
        item = self.itemAt(QGraphicsSceneMouseEvent.scenePos())
        if item:
            if getattr(item, "id", ""):
                item.cachePosition()
                self.updateItemRecord(item)
                self.listPanel.selectRadarItem(self, item)
                self.attributeEditor.setRadarItem(item)
            return super(RadarGraphicsScene, self).mousePressEvent(QGraphicsSceneMouseEvent)

    def mouseReleaseEvent(self, QGraphicsSceneMouseEvent):
        item = self.itemAt(QGraphicsSceneMouseEvent.scenePos())
        if getattr(item, "id", ""):
            if item.hasMoved():
                item.cachePosition()
                index = self.radarItemToSourceIndex(item, 'pos')
                log.debug("Item Moved")
                self.sourceModel.setData(index,
                                         [item.scenePos().x(), item.scenePos().y()],
                                         QtCore.Qt.EditRole)
                self.proxyModel.reset()

        return super(RadarGraphicsScene, self).mouseReleaseEvent(QGraphicsSceneMouseEvent)

    def addRadarItem(self, pos):
        record = self.sourceModel.addNewRadarItem()
        graphicsItem = RadarGraphicsItem()
        graphicsItem.setId(record["_id"])
        self.sourceModel.updateGraphicsItemColour.connect(graphicsItem.updateColour)
        self.addItem(graphicsItem)
        graphicsItem.setPos(pos)
        graphicsItem.record = record
        self.mongoSceneHandle.updatePosition(record["_id"], pos.x(), pos.y())
        self.radarItemAdded.emit(graphicsItem)

    def filterRadarItems(self):
        """
        :return:
        """
        # Probably should use layers!
        return [i for i in self.items() if getattr(i, "id", "")]

    def itemFromID(self, idx):
        if idx in self._itemDict:
            return self._itemDict[idx]
        log.debug("finding RadarGraphicsItem in scene by ID : {0}".format(idx))
        found = [i for i in self.filterRadarItems() if i.id() == idx]
        if found:
            return found[0]


class ExtendedQLabel(QtGui.QLabel):

    clicked = Signal()

    def __init(self, parent):
        super(ExtendedQLabel, self).__init__(parent)

    def mouseReleaseEvent(self, ev):
        self.clicked.emit()


class SimpleColourPicker(QtGui.QWidget):

    setColor = Signal(QtGui.QColor)

    def __init__(self, parent=None):
        super(SimpleColourPicker, self).__init__(parent)
        self.setLayout(QtGui.QHBoxLayout())
        self.colours = [
            QtGui.QColor(202, 227, 116),
            QtGui.QColor(183, 136, 174),
            QtGui.QColor(128, 45, 112),
            QtGui.QColor(203, 172, 197),
            QtGui.QColor(231, 206, 146),
            QtGui.QColor(206, 176, 104),
            QtGui.QColor(255, 236, 190),
            QtGui.QColor(107, 116, 158),
            QtGui.QColor(135, 142, 175),
            QtGui.QColor(79, 90, 141),
            QtGui.QColor(53, 65, 122),
            QtGui.QColor(203, 221, 139),
            QtGui.QColor(145, 170, 60),
            QtGui.QColor(230, 244, 181),
            QtGui.QColor(175, 197, 99),
        ]
        self.widgets = []
        for col in self.colours:
            w = ExtendedQLabel()
            self.widgets.append(w)
            pix = QtGui.QPixmap(QtCore.QSize(24,24))
            pix.fill(col)
            w.setPixmap(pix)
            self.layout().addWidget(w)
            w.clicked.connect(self.colorSelected)

    def colorSelected(self):
        col = self.colours[self.widgets.index(self.sender())]
        self.setColor.emit(col)


class CentralWidget(QtGui.QWidget):

    tabClosed = Signal(int)

    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.tabContainer = QtGui.QTabWidget(self)
        self.mainLayout.addWidget(self.tabContainer)
        self.tabIcon = QtGui.QIcon(g_IMAGES_PATH + "/radarTabIcon.png")
        self.tabContainer.setTabsClosable(True)
        self.tabContainer.tabCloseRequested.connect(self.closeTab)

    def updateSceneName(self, idx, name):
        openIds = self.openSceneIds(asString=True)
        if idx in openIds:
            index = openIds.index(idx)
            self.tabContainer.setTabText(index, name)

    def closeTab(self, tabIndex):
        log.debug("Close : {0}".format(tabIndex))
        self.tabContainer.removeTab(tabIndex)
        widget = self.tabContainer.widget(tabIndex)
        try:
            widget.close()
            widget.deletLater()
        except:pass
        self.tabClosed.emit(tabIndex)

    def openSceneIds(self, asString=False):
        ids = []
        for view in self.getGraphicsViews():
            data = view.scene.mongoSceneHandle.sceneId()
            if asString:
                ids.append(str(data))
            else:
                ids.append(data)
        return ids

    def sceneIsOpen(self, idx):
        return any([i==idx for i in self.openSceneIds()])

    def getGraphicsViews(self):
        views = []
        for tIndex in range(self.tabContainer.count()):
            views.append(self.tabContainer.widget(tIndex))
        return views

    def addRadarGraphicsView(self, name, view):
        self.tabContainer.addTab(view, self.tabIcon, name)


class RadarGraphicsView(QtGui.QGraphicsView):
    def __init__(self, scene, parent=None):
        super(RadarGraphicsView, self).__init__(parent)
        self.scene = scene
        self.setScene(self.scene)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)


class SceneFilterProxyMode(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SceneFilterProxyMode, self).__init__(parent)
        self.__showOnlyMySubscriptions = True
        self.user = getpass.getuser()

    def setShowOnlyMySubscriptions(self, state):
        self.__showOnlyMySubscriptions = state
        self.reset()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        baseAccept = super(SceneFilterProxyMode, self).filterAcceptsRow(sourceRow, sourceParent)
        if self.__showOnlyMySubscriptions:
            subColumnIndex = self.sourceModel().columns.index('subscribers')
            createdByColumnIndex = self.sourceModel().columns.index('created_by')
            subscribersIndex = self.sourceModel().index(sourceRow, subColumnIndex, sourceParent)
            cratedByIndex = self.sourceModel().index(sourceRow, createdByColumnIndex, sourceParent)
            createdBy = self.sourceModel().data(cratedByIndex)
            data = self.sourceModel().data(subscribersIndex)
            data.append(createdBy)
            return all([self.user in data, baseAccept])
        else:
            return baseAccept

class ItemFilterProxyMode(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(ItemFilterProxyMode, self).__init__(parent)
        self.__tags = set()
        self.__zones = set()
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

    @property
    def zones(self):
        return self.__zones

    @property
    def tags(self):
        return self.__tags

    def clearTags(self):
        self.__tags = set()
        self.reset()

    def addTag(self, tag):
        self.__tags.add(tag)
        self.reset()

    def removeTag(self, tag):
        self.__tags.remove(tag)
        self.reset()

    def clearZones(self):
        self.__zones = set()
        self.reset()

    def addZone(self, zone):
        self.__zones.add(zone)
        self.reset()

    def removeZone(self, zone):
        self.__zones.remove(zone)
        self.reset()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        acceptTag = True
        acceptZone = True
        contains_filter = True
        if self.__tags:
            subColumnIndex = self.sourceModel().columns.index('tags')
            subscribersIndex = self.sourceModel().index(sourceRow, subColumnIndex, sourceParent)
            data = set([n for n in self.sourceModel().data(subscribersIndex).split(',') if n])
            acceptTag = bool(data & self.__tags)
        if self.__zones:
            subColumnIndex = self.sourceModel().columns.index('zone')
            subscribersIndex = self.sourceModel().index(sourceRow, subColumnIndex, sourceParent)
            acceptZone = self.sourceModel().data(subscribersIndex) in self.__zones

        regEx = self.filterRegExp()
        if not regEx.isEmpty():
            patern = regEx.pattern().lower()
            nameColumnIndex = self.sourceModel().columns.index('name')
            nameIndex = self.sourceModel().index(sourceRow, nameColumnIndex, sourceParent)
            filter_text = self.sourceModel().data(nameIndex, self.filterRole()).lower()
            contains_filter = patern in filter_text

        if all([self.__zones, self.__tags]):
            return all([acceptTag, acceptZone, contains_filter])
        elif self.__tags:
            return all([acceptTag, contains_filter])
        elif self.__zones:
            return all([acceptZone, contains_filter])
        else:
            return contains_filter

class RadarScenesPanel(QtGui.QDockWidget):

    radarSelectionChanged = Signal(dict)
    radarSceneDeleted = Signal(str)

    def __init__(self, parent=None):
        super(RadarScenesPanel, self).__init__(" Scenes", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        containerWidget = QtGui.QWidget(self)
        self.form = radarSelectSceneForm.Ui_Form()
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.setWidget(containerWidget)
        self.radarDbHandle = MongoSceneHandle()
        self.radarDbHandle.getScenes()

        self._model = SceneFilterProxyMode(self)
        self._model.setSourceModel(RadarScenesTableModel(self))
        self.form.tableView_radarScenes.setModel(self._model)
        self.form.tableView_radarScenes.resizeColumnsToContents()
        self._model.setFilterKeyColumn(self.sourceModel.columns.index('name'))
        self.form.lineEdit_filter.textChanged.connect(self._model.setFilterRegExp)

        self.form.tableView_radarScenes.customContextMenuRequested.connect(self.showRMBMenu)
        self.form.checkBox.toggled.connect(self._model.setShowOnlyMySubscriptions)

        # hide columns we are not interested in sorting or displaying
        for cIndex in self._model.sourceModel().hiddenColumns:
            self.form.tableView_radarScenes.setColumnHidden(cIndex, True)

        # connect signals
        self.form.pushButton_new.clicked.connect(self._model.sourceModel().addNewRadar)
        self.form.tableView_radarScenes.doubleClicked.connect(self.radarDoubleClicked)

        self.createActions()
        self.createMenus()

    @property
    def sourceModel(self):
        return self._model.sourceModel()

    def getSourceModel(self):
        return self._model.sourceModel()

    def createMenus(self):
        self.rmbMenu = QtGui.QMenu()
        self.rmbMenu.addAction(self.deleteRadarAction)
        self.rmbMenu.addAction(self.inviteUserAction)

    def createActions(self):
        self.deleteRadarAction = QtGui.QAction(self.tr("Delete Scene"), self)
        self.deleteRadarAction.setStatusTip(self.tr("Delete a Radar Scene"))
        self.deleteRadarAction.triggered.connect(self.doSceneDelete)

        self.inviteUserAction = QtGui.QAction(self.tr("Invite User"), self)
        self.inviteUserAction.setStatusTip(self.tr("Invite a user by username to the scene"))
        self.inviteUserAction.triggered.connect(self.inviteUser)

    def inviteUser(self):
        radar = self.radarFromSelected()
        text, state = QtGui.QInputDialog.getText(self, 'Invite User', "User name:")
        if state:
            scene = MongoSceneHandle(radar)
            scene.addSubscription(text)

    def doSceneDelete(self):
        radar = self.radarFromSelected()
        result = QtGui.QMessageBox.warning(self, "Delete Radar Scene",
                        "Are you sure you want to delete {}".format(radar["name"]),
                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
        if result == QtGui.QMessageBox.Ok:
            idx = radar["_id"]
            self._model.sourceModel().deleteRadar(idx)
            self.radarSceneDeleted.emit(idx)

    def selectedToSource(self):
        modelIndex = self.form.tableView_radarScenes.selectionModel().selectedIndexes()[0]
        sourceIndex = self._model.mapToSource(modelIndex)
        sourceModel = self._model.sourceModel()
        return sourceModel, sourceIndex

    def radarFromSelected(self):
        sourceModel, sourceIndex = self.selectedToSource()
        radar = sourceModel.radarFromRow(sourceIndex.row())
        return radar

    def showRMBMenu(self, position):
        self.rmbMenu.move(self.form.tableView_radarScenes.mapToGlobal(position))
        self.rmbMenu.show()

    def radarDoubleClicked(self, index):
        modelIndex = self._model.mapToSource(index)
        row = modelIndex.row()
        data = self._model.sourceModel().radarFromRow(row)
        self.radarSelectionChanged.emit(data)

class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        # if parent is not None:
        #     self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def clear(self):
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().deleteLater()
        self.itemList = []

    def deleteItemAt(self, index):
        self.takeAt(index).widget().deleteLater()

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


class TagFieldWidget(QtGui.QWidget):

    tagAdded = Signal(str)
    tagRemoved = Signal(str)

    def __init__(self, parent=None):
        super(TagFieldWidget, self).__init__(parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        groupBox = QtGui.QGroupBox("Tags")
        font = groupBox.font()
        font.setBold(True)
        groupBox.setFont(font)
        gbLayout = QtGui.QVBoxLayout()
        groupBox.setLayout(gbLayout)
        self.layout().addWidget(groupBox)
        self.le_newTag = QtGui.QLineEdit()
        self.le_newTag.setToolTip("use , as a tag separator")
        self.le_newTag.returnPressed.connect(self.addNewTag)
        self.flowLayout = FlowLayout()

        gbLayout.addWidget(self.le_newTag)
        gbLayout.addLayout(self.flowLayout)
        self.__tags = []

    def clearTags(self):
        self.__tags = []
        self.flowLayout.clear()

    def addNewTag(self):
        tags = self.le_newTag.text().replace(" ", "").split(",")
        self.setTags(tags)

    def setTags(self, tags):
        if not getattr(tags, "__iter__", ""):
            tags = [tags]
        for tag in tags:
            if tag:
                if tag.lower() not in self.__tags:
                    self.__tags.append(tag.lower())
                    tagWidget = QtGui.QPushButton(tag.lower())
                    tagWidget.clicked.connect(self.removeTag)
                    self.flowLayout.addWidget(tagWidget)
                    self.tagAdded.emit(tag.lower())
        self.le_newTag.setText("")


    def removeTag(self):
        tag = self.sender().text()
        index = self.__tags.index(tag)
        self.flowLayout.deleteItemAt(index)
        self.__tags.pop(index)
        self.tagRemoved.emit(tag)


class RadarListPanel(QtGui.QDockWidget):

    radarListSelectionChanged = Signal(RadarGraphicsScene, str)

    def __init__(self, parent=None):
        super(RadarListPanel, self).__init__(" Radar List", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        containerWidget = QtGui.QWidget(self)
        self.form = radarListForm.Ui_Form()
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.form.itemTableView.clicked.connect(self.emitSelectionChange)
        self.form.itemTableView.setSortingEnabled(True)
        self.form.pushButton_filterTags.clicked.connect(self.showFiltersMenu)
        self.form.pushButton_filterZone.clicked.connect(self.showZonesMenu)
        self._scene = None

    @property
    def scene(self):
        return self._scene

    def setFilterTag(self):
        cb = self.sender()
        if cb.isChecked():
            self._scene.proxyModel.addTag(cb.text())
        else:
            self._scene.proxyModel.removeTag(cb.text())

    def setFilterZone(self):
        cb = self.sender()
        if cb.isChecked():
            self._scene.proxyModel.addZone(cb.text())
        else:
            self._scene.proxyModel.removeZone(cb.text())

    def showZonesMenu(self):
        menu = QtGui.QMenu("menu")
        zones = ['P1', 'P2', 'P3', 'P4']
        action = QtGui.QAction('clear', menu)
        menu.addAction(action)
        action.triggered.connect(self._scene.proxyModel.clearZones)
        for i in zones:
            action = QtGui.QAction(i, menu, checkable=True)
            menu.addAction(action)
            if i in self._scene.proxyModel.zones:
                action.setChecked(True)
            action.triggered.connect(self.setFilterZone)
        menu.move(self.mapToGlobal(self.form.pushButton_filterTags.pos()))
        menu.exec_()

    def showFiltersMenu(self):
        menu = QtGui.QMenu("menu")
        sceneTags = self._scene.mongoSceneHandle.allSceneTags()
        action = QtGui.QAction('clear', menu)
        menu.addAction(action)
        action.triggered.connect(self._scene.proxyModel.clearTags)
        for i in sceneTags:
            action = QtGui.QAction(i, menu, checkable=True)
            menu.addAction(action)
            if i in self._scene.proxyModel.tags:
                action.setChecked(True)
            action.triggered.connect(self.setFilterTag)
        menu.move(self.mapToGlobal(self.form.pushButton_filterTags.pos()))
        menu.exec_()

    def setGraphicsScene(self, scene):
        if scene:
            self._scene = scene
            self.form.itemTableView.setModel(self._scene.proxyModel)
            for col in self._scene.sourceModel.hiddenColumns:
                self.form.itemTableView.setColumnHidden(col, True)
        else:
            self.form.itemTableView.setModel(None)


    def getGraphicsScene(self):
        return self._scene

    def selectRadarItem(self, scene, radarItem):
        """
        Called when a radarItem is selected in the graphics scene.  Selects the row and scrolls to it in the view
        :param radarItem: RadarGraphicsItem
        :return: None
        """
        if self.scene is scene:
            index = self.scene.radarItemToProxyIndex(radarItem)
            if index.isValid():
                log.debug("Update List From Selected Item in Scene")
                self.form.itemTableView.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop)
                self.form.itemTableView.selectRow(index.row())
        else:
            raise LookupError()

    def emitSelectionChange(self):
        if self.scene:
            log.debug("list view selection changed")

            modelIndex = self.form.itemTableView.selectionModel().selectedIndexes()[0]
            row = self.scene.proxyModel.mapToSource(modelIndex).row()
            idx = self.scene.sourceModel.rawDataFromRow(row)["_id"]
            self.radarListSelectionChanged.emit(self.scene, str(idx))


class RadarAttributeEditor(QtGui.QDockWidget):
    def __init__(self, parent=None):
        super(RadarAttributeEditor, self).__init__(" Radar Attribute Editor", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.radarItem = None
        self.form = radarAttributeEditorForm.Ui_Form()
        containerWidget = QtGui.QWidget(self)
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.radarItem = None
        self.rowIndexes = {}
        self.tagWidget = TagFieldWidget(self)
        self.form.mainLayout.addWidget(self.tagWidget)
        self.connectSignals()
        self._scene = None
        self.simpleColPicker = SimpleColourPicker(self)
        self.simpleColPicker.setColor.connect(self.quickSetColour)
        self.form.mainLayout.insertWidget(5, self.simpleColPicker)

    @property
    def scene(self):
        return self._scene

    def setGraphicsScene(self, scene):
        self._scene = scene
        self.clearData()

    def getGraphicsScene(self):
        return self._scene

    def connectSignals(self):
        self.form.name_lineEdit.textChanged.connect(self.writeData)
        self.form.description_plainTextEdit.textChanged.connect(self.writeData)
        self.form.comments_plainTextEdit.textChanged.connect(self.writeData)
        self.form.pushButton_postComment.clicked.connect(self.postComment)
        self.tagWidget.tagAdded.connect(self.setTags)
        self.tagWidget.tagRemoved.connect(self.removeTag)
        self.form.pickColour_pushButton.clicked.connect(self.pickColour)
        self.form.link_lineEdit.textChanged.connect(self.writeData)

    def quickSetColour(self, colour):
        role = QtCore.Qt.EditRole
        if all([self.scene, self.radarItem]):
            if colour.isValid():
                self.scene.sourceModel.setData(self.rowIndexes["colour"], colour, role)

    def pickColour(self):
        if all([self.scene, self.radarItem]):
            role = QtCore.Qt.EditRole
            rawCol = self.radarItem.record["colour"]
            qCol = QtGui.QColor(rawCol[0], rawCol[1], rawCol[2])
            colour = QtGui.QColorDialog.getColor(qCol, self)
            if colour.isValid():
                self.scene.sourceModel.setData(self.rowIndexes["colour"], colour, role)

    def postComment(self):
        if all([self.scene, self.radarItem]):
            role = QtCore.Qt.EditRole
            comment = self.form.comments_plainTextEdit.toPlainText()
            self.scene.sourceModel.setData(self.rowIndexes["comments"], comment, role)
            self.scene.updateItemRecord(self.radarItem)
            self.form.comments_plainTextEdit.clear()
            self.setRadarItem(self.radarItem)

    def setTags(self, tag):
        if all([self.scene, self.radarItem]):
            role = QtCore.Qt.EditRole
            currentTags = [n for n in self.rowIndexes["tags"].data(QtCore.Qt.DisplayRole).split(",") if n]
            if tag.lower() not in currentTags:
                currentTags.append(tag.lower())
                self.scene.sourceModel.setData(self.rowIndexes["tags"], currentTags, role)

    def removeTag(self, tag):
        if all([self.scene, self.radarItem]):
            role = QtCore.Qt.EditRole
            currentTags = [n for n in self.rowIndexes["tags"].data(QtCore.Qt.DisplayRole).split(",") if n]
            if tag.lower() in currentTags:
                currentTags.remove(tag.lower())
                self.scene.sourceModel.setData(self.rowIndexes["tags"], currentTags, role)


    def setRadarItem(self, radarItem):

        if all([radarItem, self.scene]):
            self.radarItem = radarItem
            self.rowIndexes = self.scene.sourceModel.rowModelIndexFromId(self.radarItem.id())

            self.form.name_lineEdit.setText(self.radarItem.record["name"])
            self.form.description_plainTextEdit.setPlainText(self.radarItem.record["description"])
            story = ""
            for i in reversed(range(len(self.radarItem.record["comments"]))):
                cHist = self.radarItem.record["comments"][i]
                post = "-"*10
                post+="\ncommnet by : {0}  date : {1}\n\n".format(cHist["user"], cHist["date"])
                post+= cHist["text"]
                story+= post + "\n"
            self.form.commentHistory_plainTextEdit.setPlainText(story)

            self.form.createdBy_lineEdit.setText(self.radarItem.record["created_by"])
            self.form.createdOn_lineEdit.setText(self.radarItem.record["created_on"].strftime("%Y-%m-%d:%X"))

            self.form.link_lineEdit.setText(self.radarItem.record["link"])

            self.tagWidget.clearTags()
            self.tagWidget.setTags(self.radarItem.record["tags"])
        else:
            self.tagWidget.clearTags()
            self.form.name_lineEdit.setText("")
            self.form.description_plainTextEdit.setPlainText("")
            self.form.commentHistory_plainTextEdit.setPlainText("")
            self.form.createdBy_lineEdit.setText("")
            self.form.createdOn_lineEdit.setText("")
            self.form.link_lineEdit.setText("")


    def writeData(self):
        if self.scene:
            role = QtCore.Qt.EditRole
            sender = self.sender()
            model = self.scene.sourceModel
            if self.radarItem:
                if sender is self.form.name_lineEdit:
                    model.setData(self.rowIndexes["name"], self.form.name_lineEdit.text(), role)
                    self.radarItem.record['name'] = self.form.name_lineEdit.text()
                elif sender is self.form.description_plainTextEdit:
                    model.setData(self.rowIndexes["description"], self.form.description_plainTextEdit.toPlainText(), role)
                elif sender is self.form.link_lineEdit:
                    model.setData(self.rowIndexes["link"], self.form.link_lineEdit.text(), role)

    def clearData(self):
        self.radarItem = None
        self.rowIndexes = {}
        self.setRadarItem(None)



class MainWindow(QtGui.QMainWindow):
    """
    Main UI for our Radar
    """
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Item Radar")
        self.setBaseSize(800, 1024)
        self.setWindowIcon(QtGui.QIcon(g_IMAGES_PATH + "/radar_window_icon.png"))
        self.pb = QtGui.QProgressBar(self.statusBar())
        self.statusBar().addPermanentWidget(self.pb)


        self.createActions()
        self.createMenus()
        # self.createToolbar() # TESTING May not need
        self.hide_progress_bar()

        # Add the central tab widget to contain many open radars
        self.centralTab = CentralWidget(self)
        self.setCentralWidget(self.centralTab)
        self.centralTab.tabContainer.currentChanged.connect(self.connectModel)

        self.radarSelectSceneView = RadarScenesPanel(self)
        self.radarSelectSceneView.getSourceModel().radarSceneRenamed.connect(self.centralTab.updateSceneName)
        self.radarSelectSceneView.radarSelectionChanged.connect(self.openScene)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.radarSelectSceneView)

        self.itemListPanel = RadarListPanel(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.itemListPanel)

        self.attributeEditor = RadarAttributeEditor(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.attributeEditor)

        self.centralTab.tabClosed.connect(self.sceneTabClosed)

        self.setMinimumSize(800, 1024)

    def update_progress(self, n, nrows):
        self.pb.show()
        self.pb.setRange(0, nrows)
        self.pb.setValue(n)
        self.statusBar().showMessage(self.tr("Parsing eventlog data..."))

    def hide_progress_bar(self):
        self.pb.hide()
        self.statusBar().showMessage(self.tr("Finished"))

    def about(self):
        QtGui.QMessageBox.about(self, self.tr("About ItemRadar"),
            self.tr("ItemRadar\n\n"
                    "%s\n"
                    "%s\n"
                    "%s" % (__author__, __version__, __date__)))

    def createToolbar(self):
        self.mainToolBar = self.addToolBar('mainTools')
        self.mainToolBar.addAction(self.tb_exitAction)


    def createActions(self):

        self.exitAct = QtGui.QAction(self.tr("E&xit"), self)
        self.exitAct.setShortcut(self.tr("Ctrl+Q"))
        self.exitAct.setStatusTip(self.tr("Exit the application"))
        self.exitAct.triggered.connect(self.close)

        self.aboutAct = QtGui.QAction(self.tr("&About"), self)
        self.aboutAct.setStatusTip(self.tr("Show the application's About box"))
        self.aboutAct.triggered.connect(self.about)

        self.exportAct = QtGui.QAction(self.tr("E&xport Scene"), self)
        self.exportAct.setShortcut(self.tr("Ctrl+S"))
        self.exportAct.setStatusTip(self.tr("Export the current scene to a json file"))
        self.exportAct.triggered.connect(self.exportScene)

        #  TOOLBAR ACTIONS
        self.tb_exitAction = QtGui.QAction(QtGui.QIcon('exit24.png'), 'Exit', self)
        self.tb_exitAction.setShortcut('Ctrl+Q')
        self.tb_exitAction.triggered.connect(self.close)


    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))

        # self.fileMenu.addAction(self.openSceneAct)
        # self.fileMenu.addAction(self.newSceneAct)
        # self.fileMenu.addAction(self.saveSceneAct)

        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.fileMenu.addAction(self.exportAct)

        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.aboutAct)

    def createStatusBar(self):
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        self.setStatusBar(sb)
        self.statusBar().showMessage(self.tr("Ready"))

    def connectModel(self, tabIndex):
        """
        When a new tab is selected we need to push the correct model onto the various editors
        :param tabIndex: int
        :return: None
        """
        radarGraphicsView = self.centralTab.tabContainer.widget(tabIndex)
        if radarGraphicsView:
            radarGraphicsView.scene.setActive()
        else:
            pass

    def sceneTabClosed(self):
        self.attributeEditor.setGraphicsScene(None)
        self.itemListPanel.setGraphicsScene(None)
        self.connectModel(self.centralTab.tabContainer.currentIndex())

    def exportScene(self):
        graphicsViewIndex = self.centralTab.tabContainer.currentIndex()
        if graphicsViewIndex != -1:
            view = self.centralTab.tabContainer.widget(graphicsViewIndex)
            options = QtGui.QFileDialog.Options()
            fileName, _ = QtGui.QFileDialog.getSaveFileName(self,
                "export scene",
                "",
                "All Files (*);;Scene Files (*.json)")
            if fileName:
                view.scene.mongoSceneHandle.exportAs(fileName)

    def openScene(self, sceneRecord):

        if self.centralTab.sceneIsOpen(sceneRecord["_id"]):
            log.debug("Scene is Open : {0}".format(sceneRecord))
            index = self.centralTab.openSceneIds().index(sceneRecord["_id"])
            self.centralTab.tabContainer.setCurrentIndex(index)
            return

        log.debug("Open : {0}".format(sceneRecord))
        mongoSceneHandle = MongoSceneHandle(sceneRecord)

        scene = RadarGraphicsScene(-400,-300,800,600, self)
        scene.initScene(mongoSceneHandle, self.attributeEditor, self.itemListPanel)
        radar = RadarGraphicsView(scene, self)

        self.centralTab.addRadarGraphicsView(sceneRecord["name"], radar)
        # scene.radarItemClicked.connect(self.updateRadarAttributeEditor)

        lastIndex = self.centralTab.tabContainer.count()-1
        self.centralTab.tabContainer.setCurrentIndex(lastIndex)