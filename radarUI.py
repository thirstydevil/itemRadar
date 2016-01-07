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
        self.brush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 255, 17))
        self.brushSelected = QtGui.QBrush(QtGui.QColor.fromRgb(51, 187, 255))
        self.brushHover = QtGui.QBrush(QtGui.QColor.fromRgb(255, 255, 255))
        self.pen = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 50), 2)
        self.diameter = 12
        self._selected = False
        self._hovering = False
        self.setAcceptHoverEvents(True)
        self.dotRect = QtCore.QRectF(0-self.diameter / 2, 0 - self.diameter / 2, self.diameter, self.diameter)

    def setId(self, id):
        self._id = id

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

    def setRadarMogoDbScene(self, scene ):
        self.dbScene = scene
        self.tableModel = ItemsTableModel(scene)

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

    def addRadarItem(self, pos, **kwargs):
        record = self.tableModel.addNewRadarItem()
        graphicsItem = RadarGraphicsItem()
        graphicsItem.setId(record["_id"])
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

    def itemFromUUID(self, uuid):
        log.debug("finding uuid in items : {0}".format(uuid))
        found = [i for i in self.filterRadarItems() if i.id() == uuid]
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

    def addRadarGraphicsView(self, name, view):
        self.tabContainer.addTab(view, self.tabIcon, name)

    def getRadarGraphicsView(self, view):
        if isinstance(view, basestring):
            for idx in range(self.tabContainer.count()):
                if self.tabContainer.tabText(idx) == view:
                    return self.tabContainer.widget(idx)
        else:
            for idx in range(self.tabContainer.count()):
                if self.tabContainer.widget(idx) == view:
                    return view


class RadarGraphicsView(QtGui.QGraphicsView):
    def __init__(self, scene, parent=None):
        super(RadarGraphicsView, self).__init__(parent)

        self.scene = scene
        #self.setMaximumSize(805, 605)
        self.setScene(self.scene)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

        self.backgroundBrush = QtGui.QBrush(QtGui.QColor.fromRgb(34, 17, 17))
        self.backgroundPenLines = QtGui.QPen(QtGui.QColor.fromRgb(0153, 38, 0, 25), 2)
        self.backgroundPenRings = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 75), 2)
        self.backgroundPenLinesBold = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 80), 2)

        self.setupBackground()
        self.setupAnimatedRadar()

    def showHideAnimatedRadar(self, state):
        item = getattr(self, "radarAnimItem", None)
        if item:
            if state:
                self.timeline.stop()
                item.hide()
            else:
                item.show()
                self.timeline.start()


    def setupAnimatedRadar(self):
        pen = QtGui.QPen(QtGui.QColor.fromRgb(153, 38, 0, 25), 2)
        brush = QtGui.QBrush(QtGui.QColor.fromRgb(0, 150, 150, 10))
        rad = self.maxRadarDiameter() / 2
        self.radarAnimItem = self.scene.addEllipse(0-rad, 0-rad, rad*2, rad*2, pen, brush)
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
        offset = self.scene.width() / numberOfLines

        # draw the radar circles
        for i in range(ringCount):
            self.scene.addEllipse(0-(diameter/2), 0-(diameter/2), diameter, diameter, backgroundPenRings, backgroundBrush)
            diameter -= ringOffset

        # overlay the grid
        for i in range(numberOfLines):
            if i not in [0, numberOfLines]:
                l = self.scene.addLine(screenPosX, topX, screenPosX+1, bottomX, backgroundPenLines)
                ll = self.scene.addLine(topX, screenPosY, bottomX, screenPosY+1, backgroundPenLines)

                ## Draw the darker center lines
                if screenPosX == 0:
                    l.setPen(self.backgroundPenLinesBold)
                if screenPosY == 0:
                    ll.setPen(self.backgroundPenLinesBold)
            screenPosX += ringOffset / 2
            screenPosY += ringOffset / 2

    def maxRadarDiameter(self):
        return self.scene.width() + self.scene.height() / 2


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

        for cIndex in self.model.sourceModel().hiddenColumns:
            self.form.tableView_radarScenes.setColumnHidden(cIndex, True)
        self.form.pushButton_new.clicked.connect(self.model.sourceModel().addNewRadar)

        self.form.tableView_radarScenes.doubleClicked.connect(self.radarDoubleClicked)

    def radarDoubleClicked(self, index):
        modelIndex = self.model.mapToSource(index)
        row = modelIndex.row()
        data = self.model.sourceModel().radarFromRow(row)
        self.radarSelectionChanged.emit(data)



class RadarFilterListPanel(QtGui.QDockWidget):

    radarSelectionChanged = Signal(str)

    def __init__(self, parent=None):
        super(RadarFilterListPanel, self).__init__(" Radar List", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        containerWidget = QtGui.QWidget(self)
        self.form = radarListForm.Ui_Form()
        self.form.setupUi(containerWidget)
        self.setWidget(containerWidget)
        self.form.itemTableView.clicked.connect(self.emitSelectionChange)
        self.model = None


    def setModel(self, model):
        self.model = model
        self.form.itemTableView.setModel(model)


    def updateSelectedFromRadarItem(self, radarItem):
        log.debug("Update List From Selected Item in Scene")
        data = self.model.rowDataFromRadarItem(radarItem)
        rowIndexes = self.model.rowModelIndexFromId(radarItem.id())
        self.form.itemTableView.selectionModel().select(rowIndexes[0].index(), QtGui.QItemSelectionModel.ClearAndSelect)
        self.form.itemTableView.scrollTo(data[0].index())

    def emitSelectionChange(self):
        modelIndex = self.form.itemTableView.selectionModel().selectedIndexes()[0]
        idx = self.model.rawDataFromRow(modelIndex.row())["_id"]
        self.radarSelectionChanged.emit(idx)


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
        self.rowIndexes = {}
        self.connectSignals()

    def connectSignals(self):
        self.form.name_lineEdit.textChanged.connect(self.writeData)
        self.form.description_plainTextEdit.textChanged.connect(self.writeData)
        self.form.comments_plainTextEdit.textChanged.connect(self.writeData)
        self.form.addTag_lineEdit.returnPressed.connect(self.writeData)

    def setModel(self, model):
        self.model = model
        self.clearData()

    def setRadarItem(self, radarItem):
        record = {}
        if radarItem:
            row = self.model.rowFromId(radarItem.id())
            self.rowIndexes = self.model.rowModelIndexFromId(radarItem.id())
            record = self.model.rawDataFromRow(row)

        if record:
            self.form.name_lineEdit.setText(record["name"])
            self.form.description_plainTextEdit.setPlainText(record["description"])
            self.form.comments_plainTextEdit.setPlainText("".join(record["comments"]))

        if not record:
            self.form.addTag_lineEdit.setText("")

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
        self.setRadarItem(None)



class MainWindow(QtGui.QMainWindow):
    """
    Main UI for our Radar
    """
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Item Radar")
        self.setBaseSize(800, 800)
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

        ## Construct a scene and make sure we set an absolute rect.  If we offset the center od the rect we can fake
        ## the origin to the center of the screen.  Which we can do as we have a fixed radar size
        ## The reason I'm doing this is to easily calculate the distance from the center of the radar to organsie a list
        ## on items with the header data
        self.openSceneList = []

        self.radarSelectSceneView = RadarSelectScenePanel(self)
        self.radarSelectSceneView.radarSelectionChanged.connect(self.openScene)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.radarSelectSceneView)

        self.radarListView = RadarFilterListPanel(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.radarListView)

        self.radarItemAttributeEditor = RadarItemAttributeEditor(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.radarItemAttributeEditor)

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

    def selectRadarItemFromListView(self, uuid):
        """
        Handles selecting of radar items in the scene by the UUID.  Other views can pass the UUID
        via a signal.  This slot can then handle the the selection of the items in the scene from the UUID
        :param uuid: str
        :return: None
        """
        # Grab the View from the current Tab and thus dig down into the scene graph.
        # The the method to extract the radarItem.
        radarGraphicsView = self.centralTab.tabContainer.currentWidget()
        item = radarGraphicsView.scene.itemFromUUID(uuid)

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
        self.radarListView.setModel(radarGraphicsView.scene.tableModel)
        self.radarItemAttributeEditor.setModel(radarGraphicsView.scene.tableModel)

    def saveScene(self):
        log.debug("Save")

    def openScene(self, data):
        log.debug("Open : {0}".format(data))
        dbScene = RadarMongoDBScene(data)
        scene = RadarGraphicsScene(-400,-300,800,600)
        scene.setRadarMogoDbScene(dbScene)
        radar = RadarGraphicsView(scene, self)
        self.openSceneList.append(scene)
        self.centralTab.addRadarGraphicsView(data["name"], radar)
        # scene.radarItemClicked.connect(self.updateRadarAttributeEditor)
        scene.radarItemAdded.connect(self.updateRadarAttributeEditor)
        # self.radarListView.radarSelectionChanged.connect(self.selectRadarItemFromListView)

    def newScene(self):
        """
        Create a new radar scene and adds it to the central tab widget
        :return: None
        """
        log.debug("New")
        scene = RadarGraphicsScene(-400,-300,800,600, parent=self)
        radar = RadarGraphicsView(scene, self)
        self.openSceneList.append(scene)
        self.centralTab.addRadarGraphicsView("Untitled", radar)
        scene.radarItemClicked.connect(self.updateRadarAttributeEditor)
        scene.radarItemAdded.connect(self.updateRadarAttributeEditor)
        self.radarListView.radarSelectionChanged.connect(self.selectRadarItemFromListView)

