__author__ = 'David Moulder'
__version__ = "0.0.1"
__date__ = "05/06/2016"

from PySide import QtCore, QtGui
from PySide.QtCore import Signal
import os
import uuid
import logging as log
import radarAttributeEditorForm
import radarListForm
import radarSelectSceneForm
from radarDBHandle import RadarMongoDBScene, ScenesTableModel, ItemsTableModel

log.basicConfig(level=log.DEBUG)

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
        self.brushSelected = QtGui.QBrush(QtGui.QColor.fromRgb(51, 187, 255))
        self.brushHover = QtGui.QBrush(QtGui.QColor.fromRgb(255, 255, 255))
        self.pen = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 50), 2)
        self.diameter = 12
        self._selected = False
        self._hovering = False
        self.setAcceptHoverEvents(True)
        self.dotRect = QtCore.QRectF(0-self.diameter / 2, 0 - self.diameter / 2, self.diameter, self.diameter)
        self._cachePos = None

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

    def setColour(self, qCol):
        self.brush = QtGui.QBrush(qCol)

    def toolTip(self, *args, **kwargs):
        model = self.scene().dataModel
        itemRowData = model.rowDataFromUUID(self.id())
        return itemRowData[0].data(QtCore.Qt.DisplayRole)[:4] + ".."

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
        if self.isSelected():
            b = self.brushSelected
        if self._hovering:
            # paint the tooltip.  Remember that when painting new things we need to update the boundingRect
            # so that the item redraws correctly.
            b = self.brushHover
            #painter.drawText( QtCore.QPoint( 12, + 4  ) ,self.toolTip())
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
    Reimplemented to access the public methods to do my own thing.  For now, just want mouse access to events
    In the future I think I'll have to link this to a DB or in the 1st place add some serialisation to this,
    more investigation needed
    """
    sceneDoubleClicked = Signal(QtCore.QPointF)
    radarItemClicked = Signal(RadarGraphicsItem)
    radarItemAdded = Signal(RadarGraphicsItem)

    def __init__(self,*args, **kwargs):
        super(RadarGraphicsScene, self).__init__(*args, **kwargs)
        self.dbScene = None
        self.tableModel = None
        self.sceneDoubleClicked.connect(self.addRadarItem)

        self.backgroundBrush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 17, 17))
        self.backgroundPenLines = QtGui.QPen(QtGui.QColor.fromRgb(0153, 38, 0, 25), 2)
        self.backgroundPenRings = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 75), 2)
        self.backgroundPenLinesBold = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 80), 2)

        self.setupBackground()
        self.setupAnimatedRadar()

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
        offset = self.width() / numberOfLines

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
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(0, 150, 150, 10))
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

    def showHideAnimatedRadar(self, state):
        item = getattr(self, "radarAnimItem", None)
        if item:
            if state:
                self.timeline.stop()
                item.hide()
            else:
                item.show()
                self.timeline.start()


    def setRadarMogoDbScene(self, scene ):
        self.dbScene = scene
        self.tableModel = ItemsTableModel(scene)

        for i in self.dbScene.items():
            graphicsItem = RadarGraphicsItem()
            graphicsItem.setId(i["_id"])
            graphicsItem.setPos(i["pos"][0], i["pos"][1])
            graphicsItem.setColour(QtGui.QColor(*i["colour"]))
            self.addItem(graphicsItem)
            self.tableModel.updateGraphicsItemColour.connect(graphicsItem.updateColour)


    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if QGraphicsSceneMouseEvent.button() == QtCore.Qt.LeftButton and \
                QGraphicsSceneMouseEvent.modifiers() == QtCore.Qt.ControlModifier:
            self.sceneDoubleClicked.emit(QGraphicsSceneMouseEvent.scenePos())

        return super(RadarGraphicsScene, self).mouseDoubleClickEvent(QGraphicsSceneMouseEvent)

    def mousePressEvent(self, QGraphicsSceneMouseEvent, **kwargs):
        item = self.itemAt(QGraphicsSceneMouseEvent.scenePos())
        if getattr(item, "id", ""):
            item.cachePosition()
            self.radarItemClicked.emit(item)
        return super(RadarGraphicsScene, self).mousePressEvent(QGraphicsSceneMouseEvent)

    def mouseReleaseEvent(self, QGraphicsSceneMouseEvent):
        item = self.itemAt(QGraphicsSceneMouseEvent.scenePos())
        if getattr(item, "id", ""):
            if item.hasMoved():
                record = self.tableModel.rawDataFromId(item.id())
                self.dbScene.updatePosition(record["_id"], item.scenePos().x(),
                                            item.scenePos().y())
                item.cachePosition()
        return super(RadarGraphicsScene, self).mouseReleaseEvent(QGraphicsSceneMouseEvent)


    def addRadarItem(self, pos):
        record = self.tableModel.addNewRadarItem()
        graphicsItem = RadarGraphicsItem()
        graphicsItem.setId(record["_id"])
        self.tableModel.updateGraphicsItemColour.connect(graphicsItem.updateColour)
        self.addItem(graphicsItem)
        graphicsItem.setPos(pos)
        self.dbScene.updatePosition(record["_id"], pos.x(), pos.y())
        super(RadarGraphicsScene, self).addItem(graphicsItem)
        self.radarItemAdded.emit(graphicsItem)

    def filterRadarItems(self):
        """
        :return:
        """
        # Probably should use layers!
        return [i for i in self.items() if getattr(i, "id", "")]

    def itemFromID(self, idx):
        log.debug("finding RadarGraphicsItem in scene by ID : {0}".format(idx))
        found = [i for i in self.filterRadarItems() if i.id() == idx]
        if found:
            return found[0]



class RadarItemModel(QtGui.QStandardItemModel):
    """
    This scene is to filter items on the radar board.
    """
    def __init__(self, *args, **kwds):
        QtGui.QStandardItemModel.__init__(self, *args, **kwds)

    def setHeaders(self):
        self.setColumnCount(6)
        self.setRowCount(0)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "UUID")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "POS")
        self.setHeaderData(2, QtCore.Qt.Horizontal, "NAME")
        self.setHeaderData(3, QtCore.Qt.Horizontal, "DESCRIPTION")
        self.setHeaderData(4, QtCore.Qt.Horizontal, "COMMENTS")
        self.setHeaderData(4, QtCore.Qt.Horizontal, "TAGS")

    def insertNewRowFromRadarItem(self, radarItem):
        if getattr(radarItem, "id", ""):
            idx = QtGui.QStandardItem(radarItem.id())
            pos = QtGui.QStandardItem("{0},{1}".format(radarItem.scenePos().x(), radarItem.scenePos().y()))
            name = QtGui.QStandardItem("New")
            description = QtGui.QStandardItem("")
            comments = QtGui.QStandardItem("")
            tags = QtGui.QStandardItem("")
            self.appendRow([name, pos, idx, description, comments, tags])


    def rowDataFromUUID(self, uuid):
        foundItems = self.findItems(uuid, column=2)
        data = []
        if foundItems:
            row = foundItems[0].row()
            for c in range(self.columnCount()):
                data.append(self.item(row, c))
        return data

    def rowDataFromRadarItem(self, radarItem):
        return self.rowDataFromUUID(radarItem.id())


class CentralWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.tabContainer = QtGui.QTabWidget(self)
        self.mainLayout.addWidget(self.tabContainer)
        self.tabIcon = QtGui.QIcon(g_IMAGES_PATH + "/radarTabIcon.png")
        self.tabContainer.setTabsClosable(True)
        self.tabContainer.tabCloseRequested.connect(self.closeTab)


    def closeTab(self, tabIndex):
        log.debug("Close : {0}".format(tabIndex))
        self.tabContainer.removeTab(tabIndex)

    def openSceneIds(self):
        ids = []
        for view in self.getGraphicsViews():
            ids.append(view.scene.dbScene.sceneId())
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

    def id(self):
        return self.scene.dbScene.sceneId()


class RadarSelectScenePanel(QtGui.QDockWidget):

    radarSelectionChanged = Signal(dict)

    def __init__(self, parent=None):
        super(RadarSelectScenePanel, self).__init__(" Radar List", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        containerWidget = QtGui.QWidget(self)
        self.form = radarSelectSceneForm.Ui_Form()
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.setWidget(containerWidget)
        self.radarDbHandle = RadarMongoDBScene()
        self.radarDbHandle.getScenes()

        self.model = QtGui.QSortFilterProxyModel(self)
        self.model.setSourceModel(ScenesTableModel(self))
        self.form.tableView_radarScenes.setModel(self.model)
        self.form.tableView_radarScenes.resizeColumnsToContents()
        self.model.setFilterKeyColumn(1)
        self.form.lineEdit_filter.textChanged.connect(self.model.setFilterRegExp)

        # hide columns we are not interested in sorting or displaying
        for cIndex in self.model.sourceModel().hiddenColumns:
            self.form.tableView_radarScenes.setColumnHidden(cIndex, True)

        # connect signals
        self.form.pushButton_new.clicked.connect(self.model.sourceModel().addNewRadar)
        self.form.tableView_radarScenes.doubleClicked.connect(self.radarDoubleClicked)

    def radarDoubleClicked(self, index):
        modelIndex = self.model.mapToSource(index)
        row = modelIndex.row()
        data = self.model.sourceModel().radarFromRow(row)
        self.radarSelectionChanged.emit(data)

class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def clear(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

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
            if tag.lower() not in self.__tags:
                self.__tags.append(tag.lower())
                tagWidget = QtGui.QPushButton(tag.lower())
                tagWidget.clicked.connect(self.removeTag)
                self.flowLayout.addWidget(tagWidget)
                self.tagAdded.emit(tag.lower())

    def removeTag(self):
        tag = self.sender().text()
        index = self.__tags.index(tag)
        self.flowLayout.takeAt(index)
        self.__tags.remove(index)
        self.tagRemoved.emit(tag)


class RadarFilterListPanel(QtGui.QDockWidget):

    radarListSelectionChanged = Signal(str)

    def __init__(self, parent=None):
        super(RadarFilterListPanel, self).__init__(" Radar List", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        containerWidget = QtGui.QWidget(self)
        self.form = radarListForm.Ui_Form()
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.form.itemTableView.clicked.connect(self.emitSelectionChange)

        self.proxyModel = QtGui.QSortFilterProxyModel(self)

        self.model = None

    def clear(self):
        self.model = None
        self.proxyModel = QtGui.QSortFilterProxyModel(self)

    def setModel(self, model):
        self.model = model
        self.proxyModel.setSourceModel(self.model)
        self.form.filter_lineEdit.textChanged.connect(self.proxyModel.setFilterRegExp)
        self.proxyModel.setFilterKeyColumn(self.model.columns.index("name"))
        self.form.itemTableView.setModel(self.proxyModel)
        for c in self.model.hiddenColumns:
            self.form.itemTableView.setColumnHidden(c, True)
        self.form.itemTableView.horizontalHeader().stretchLastSection()


    def updateSelectedFromRadarItem(self, radarItem):
        """
        Called when a radarItem is selected in the graphics scene.  Selects the row and scrolls to it in the view
        :param radarItem: RadarGraphicsItem
        :return: None
        """
        log.debug("Update List From Selected Item in Scene")
        # row = self.model.rowFromId(radarItem.id())
        # self.form.itemTableView.selectRow(row)
        # self.form.itemTableView.scrollTo(self.model.index(row, 0), QtGui.QAbstractItemView.PositionAtTop)

    def emitSelectionChange(self):
        log.debug("list view selection changed")
        modelIndex = self.form.itemTableView.selectionModel().selectedIndexes()[0]
        row = self.proxyModel.mapToSource(modelIndex).row()
        idx = self.model.rawDataFromRow(row)["_id"]
        self.radarListSelectionChanged.emit(str(idx))


class RadarItemAttributeEditor(QtGui.QDockWidget):
    def __init__(self, parent=None):
        super(RadarItemAttributeEditor, self).__init__(" Radar Attribute Editor", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.model = None
        self.radarItem = None
        self.form = radarAttributeEditorForm.Ui_Form()
        containerWidget = QtGui.QWidget(self)
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.record = {}
        self.row = None
        self.rowIndexes = {}
        self.radarItem = None
        self.tagWidget = TagFieldWidget(self)
        self.form.mainLayout.addWidget(self.tagWidget)
        self.connectSignals()

    def connectSignals(self):
        self.form.name_lineEdit.textChanged.connect(self.writeData)
        self.form.description_plainTextEdit.textChanged.connect(self.writeData)
        self.form.comments_plainTextEdit.textChanged.connect(self.writeData)
        self.form.pushButton_postComment.clicked.connect(self.postComment)
        self.tagWidget.tagAdded.connect(self.postTag)
        self.form.pickColour_pushButton.clicked.connect(self.pickColour)

    def pickColour(self):
        role = QtCore.Qt.EditRole
        rawCol = self.record["colour"]
        qCol = QtGui.QColor(rawCol[0], rawCol[1], rawCol[2])
        colour = QtGui.QColorDialog.getColor(qCol, self)
        if colour.isValid():
            self.model.setData(self.rowIndexes["colour"], colour, role)

    def setModel(self, model):
        self.model = model
        self.clearData()


    def postComment(self):
        role = QtCore.Qt.EditRole
        comment = self.form.comments_plainTextEdit.toPlainText()
        self.model.setData(self.rowIndexes["comments"], comment, role)
        self.form.comments_plainTextEdit.clear()
        self.setRadarItem(self.radarItem)


    def postTag(self, tag):
        role = QtCore.Qt.EditRole
        self.model.setData(self.rowIndexes["tags"], tag, role)

    def setRadarItem(self, radarItem):
        self.record = {}
        if radarItem and self.model:
            self.radarItem = radarItem
            self.row = self.model.rowFromId(self.radarItem.id())
            self.rowIndexes = self.model.rowModelIndexFromId(self.radarItem.id())
            self.record = self.model.rawDataFromRow(self.row)

        if self.record:
            self.form.name_lineEdit.setText(self.record["name"])
            self.form.description_plainTextEdit.setPlainText(self.record["description"])
            story = ""
            for i in reversed(range(len(self.record["comments"]))):
                cHist = self.record["comments"][i]
                post = "-"*10
                post+="\ncommnet by : {0}  date : {1}\n\n".format(cHist["user"], cHist["date"])
                post+= cHist["text"]
                story+= post + "\n"
            self.form.commentHistory_plainTextEdit.setPlainText(story)

            self.form.createdBy_lineEdit.setText(self.record["created_by"])
            self.form.createdOn_lineEdit.setText(self.record["created_on"].strftime("%Y-%m-%d:%X"))

            self.tagWidget.clearTags()
            self.tagWidget.setTags(self.record["tags"])


    def writeData(self):
        role = QtCore.Qt.EditRole
        sender = self.sender()
        if self.rowIndexes:
            if sender is self.form.name_lineEdit:
                self.model.setData(self.rowIndexes["name"], self.form.name_lineEdit.text(), role)
            elif sender is self.form.description_plainTextEdit:
                self.model.setData(self.rowIndexes["description"], self.form.description_plainTextEdit.toPlainText(), role)

    def clearData(self):
        self.radarItem = None
        self.record = {}
        self.rowIndexes = {}
        self.row = None
        self.setRadarItem(None)



class MainWindow(QtGui.QMainWindow):
    """
    Main UI for our Radar
    """
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Item Radar")
        self.setBaseSize(800, 1024)
        self.setWindowIcon(QtGui.QIcon(g_IMAGES_PATH + "/windowIcon.png"))
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

        self.radarSelectSceneView = RadarSelectScenePanel(self)
        self.radarSelectSceneView.radarSelectionChanged.connect(self.openScene)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.radarSelectSceneView)

        self.radarListView = RadarFilterListPanel(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.radarListView)

        self.radarItemAttributeEditor = RadarItemAttributeEditor(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.radarItemAttributeEditor)

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

        self.newSceneAct = QtGui.QAction(self.tr("N&ew"), self)
        self.newSceneAct.setShortcut(self.tr("Ctrl+N"))
        self.newSceneAct.setStatusTip(self.tr("New Radar Scene"))
        self.newSceneAct.triggered.connect(self.newScene)

        self.saveSceneAct = QtGui.QAction(self.tr("S&ave"), self)
        self.saveSceneAct.setShortcut(self.tr("Ctrl+S"))
        self.saveSceneAct.setStatusTip(self.tr("Save Radar Scene"))
        self.saveSceneAct.triggered.connect(self.saveScene)

        self.openSceneAct = QtGui.QAction(self.tr("O&pen"), self)
        self.openSceneAct.setShortcut(self.tr("Ctrl+O"))
        self.openSceneAct.setStatusTip(self.tr("Open Radar Scene"))
        self.openSceneAct.triggered.connect(self.openScene)

        self.exitAct = QtGui.QAction(self.tr("E&xit"), self)
        self.exitAct.setShortcut(self.tr("Ctrl+Q"))
        self.exitAct.setStatusTip(self.tr("Exit the application"))
        self.exitAct.triggered.connect(self.close)

        self.aboutAct = QtGui.QAction(self.tr("&About"), self)
        self.aboutAct.setStatusTip(self.tr("Show the application's About box"))
        self.aboutAct.triggered.connect(self.about)

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

        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.aboutAct)

    def createStatusBar(self):
        sb = QtGui.QStatusBar()
        sb.setFixedHeight(18)
        self.setStatusBar(sb)
        self.statusBar().showMessage(self.tr("Ready"))

    def setSelectedRadarItem(self, *args):
        print args

    def selectRadarItemByID(self, idx):
        """
        Handles selecting of radar items in the scene by the item id from mongoDB.  Other views can pass the id
        via a signal.  This slot can then handle the the selection of the items in the scene from the id
        :param idx: str
        :return: None
        """
        # Grab the View from the current Tab and thus dig down into the scene graph.
        # The the method to extract the radarItem.
        log.debug("Select Radar Item by ID")
        radarGraphicsView = self.centralTab.tabContainer.currentWidget()
        item = radarGraphicsView.scene.itemFromID(idx)

        log.debug("Found GraphicsItem in Radar : {0}".format(item))

        if item:
            # It was difficult to find out the best way to select items in the scene.  This is like drawing
            # a box selection on the viewport and the contained items are selected.
            radarGraphicsView.scene.clearSelection()
            painterPath = QtGui.QPainterPath()
            painterPath.addRect(item.boundingRect())
            painterPath.translate(item.scenePos())
            radarGraphicsView.scene.setSelectionArea(painterPath, QtGui.QTransform())
            self.updateRadarAttributeEditor(item)


    def updateRadarAttributeEditor(self, radarItem):
        """
        :param radarItem: RadarGraphicsItem
        :return:
        """
        log.debug("update radar attribute editor on : {0}".format(radarItem.id()))
        self.radarItemAttributeEditor.setRadarItem(radarItem)
        self.radarListView.updateSelectedFromRadarItem(radarItem)


    def connectModel(self, tabIndex):
        """
        When a new tab is selected we need to push the correct model onto the various editors
        :param tabIndex: int
        :return: None
        """
        radarGraphicsView = self.centralTab.tabContainer.widget(tabIndex)
        if radarGraphicsView:
            self.radarListView.setModel(radarGraphicsView.scene.tableModel)
            self.radarItemAttributeEditor.setModel(radarGraphicsView.scene.tableModel)

    def saveScene(self):
        log.debug("Save")

    def openScene(self, sceneRecord):

        if self.centralTab.sceneIsOpen(sceneRecord["_id"]):
            log.debug("Scene is Open : {0}".format(sceneRecord))
            index = self.centralTab.openSceneIds().index(sceneRecord["_id"])
            self.centralTab.tabContainer.setCurrentIndex(index)
            return

        log.debug("Open : {0}".format(sceneRecord))
        dbScene = RadarMongoDBScene(sceneRecord)

        scene = RadarGraphicsScene(-400,-300,800,600, self)
        scene.setRadarMogoDbScene(dbScene)
        radar = RadarGraphicsView(scene, self)
        self.radarItemAttributeEditor.clearData()
        self.radarListView.clear()
        self.centralTab.addRadarGraphicsView(sceneRecord["name"], radar)
        scene.radarItemClicked.connect(self.updateRadarAttributeEditor)
        scene.radarItemAdded.connect(self.updateRadarAttributeEditor)
        self.radarListView.radarListSelectionChanged.connect(self.selectRadarItemByID)

        lastIndex = self.centralTab.tabContainer.count()-1
        self.centralTab.tabContainer.setCurrentIndex(lastIndex)

    def newScene(self):
        """
        Create a new radar scene and adds it to the central tab widget
        :return: None
        """
        log.debug("New")
        scene = RadarGraphicsScene(-400,-300,800,600, parent=self)
        radar = RadarGraphicsView(scene, self)
        self.centralTab.addRadarGraphicsView("Untitled", radar)
        scene.radarItemClicked.connect(self.updateRadarAttributeEditor)
        scene.radarItemAdded.connect(self.updateRadarAttributeEditor)
        self.radarListView.radarListSelectionChanged.connect(self.selectRadarItemByID)

