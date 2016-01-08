__author__ = "dmoulder"

from PySide import QtCore, QtGui
from PySide.QtCore import Signal
from pymongo import MongoClient
from pprint import pformat, pprint
import datetime
import getpass

_g_client = None
_g_DB = "itemRadar"
_g_localMode = False


def getClient():
    global _g_client
    if not _g_client:
        _g_client = MongoClient('localhost', 27017)
    return _g_client

def getItemRadarDb():
    client = getClient()
    db = client[_g_DB]
    return db

def init():
    """
    Makes the default collections we need in the db
    :return: None
    """
    db = getItemRadarDb()
    if "scenes" not in db.collection_names():
        db.create_collection("scenes")
    if "items" not in db.collection_names():
        db.create_collection("items")

init()

class RadarMongoDBScene(QtCore.QObject):

    item_record_template = {
        "name": "New",
        "pos": [0,0],
        "colour": [34, 255, 17],
        "scene_id": None,
        "link": "",
        "description": "",
        "comments" : [],
        "tags" : [],
        "locked" : False,
        "created_on" : datetime.datetime.now(),
        "created_by" : getpass.getuser()
    }

    scene_template = {
        "name": "Untitled",
        "description": "",
        "locked" : False,
        "created_on" : datetime.datetime.now(),
        "created_by" : getpass.getuser(),
        "subscribers" : []
    }

    def __init__(self, sceneRecord=None):
        super(RadarMongoDBScene, self).__init__()
        self._sceneRecord = sceneRecord
        self.db = getItemRadarDb()

    def __repr__(self):
        return "radarMongoDBScene(id:{0}, name:{1})".format(self.sceneId(), getattr())

    def __updateItem__(self, id, data):
        collection = self.db.get_collection("items")
        collection.find_one_and_update({"_id":id}, {"$set": data})
        return self.findItem(id)


    @classmethod
    def findSceneFromId(cls, id):
        db = getItemRadarDb()
        return db.scenes.find_one({"_id": id})

    @classmethod
    def getScenes(cls):
        db = getItemRadarDb()
        cursor = db.scenes.find({})
        return [cls(d) for d in cursor]

    @classmethod
    def createNewScene(cls):
        db = getItemRadarDb()
        result = db.scenes.insert_one(cls.scene_template.copy())
        record = cls.findSceneFromId(result.inserted_id)
        return cls(record)

    def setSceneRecord(self, sceneRecord):
        self._sceneRecord = sceneRecord

    def items(self):
        cursor = self.db.items.find({"scene_id": self.sceneId()})
        return [r for r in cursor]

    def isValidScene(self):
        if self._sceneRecord:
            if self.db.scenes.find_one({"_id":self.sceneId()}):
                return True
        return False

    def sceneId(self):
        if self._sceneRecord:
            return self._sceneRecord["_id"]

    def sceneName(self):
        if self._sceneRecord:
            return self._sceneRecord["name"]

    def renameScene(self, name):
        db = getItemRadarDb()
        collection = db.get_collection("scenes")
        collection.find_one_and_update({"_id":self.sceneId()}, {"$set": {"name":name}})

    def newItem(self):
        if self._sceneRecord:
            newRecord = self.item_record_template.copy()
            newRecord["scene_id"] = self.sceneId()
            result = self.db.items.insert_one(newRecord)
            record = self.findItem(result.inserted_id)
            return record
        raise LookupError("No internal scene set on this object : RadarMongoDBScene")

    def updateItemName(self, itemId, name):
        itemRecord = self.findItem(itemId)
        itemRecord["name"] = name
        self.__updateItem__(itemId, itemRecord)

    def updatePosition(self, itemId, x, y):
        itemRecord = self.findItem(itemId)
        itemRecord["pos"] = [x, y]
        return self.__updateItem__(itemId, itemRecord)

    def postComment(self, itemId, text):
        comment = {"date": datetime.datetime.now(),
                   "user": getpass.getuser(),
                   "text": str(text)}
        itemRecord = self.findItem(itemId)
        itemRecord["comments"].append(comment)
        return self.__updateItem__(itemId, itemRecord)

    def updateDescription(self, itemId, text):
        itemRecord = self.findItem(itemId)
        itemRecord["description"] = text
        return self.__updateItem__(itemId, itemRecord)

    def addTag(self, itemId, tag):
        itemRecord = self.findItem(itemId)
        if tag not in itemRecord["tags"]:
            itemRecord["tags"].append(tag)
            return self.__updateItem__(itemId, itemRecord)
        else:
            return itemRecord

    def deleteTag(self, itemId, tag):
        itemRecord = self.findItem(itemId)
        if tag in itemRecord["tags"]:
            itemRecord["tags"] = itemRecord["tags"].remove(tag)
            return self.__updateItem__(itemId, itemRecord)
        return itemRecord

    def clearTags(self, itemId):
        itemRecord = self.findItem(itemId)
        itemRecord["tags"] = []
        return self.__updateItem__(itemId, itemRecord)

    def setTags(self, itemId, tags):
        assert getattr(tags, "__iter__", None)
        itemRecord = self.findItem(itemId)
        itemRecord["tags"] = tags
        return self.__updateItem__(itemId, itemRecord)

    def updateColour(self, itemId, colour):
        itemRecord = self.findItem(itemId)
        colour = colour.toRgb()
        itemRecord["colour"] = [colour.red(), colour.green(), colour.blue()]
        return self.__updateItem__(itemId, itemRecord)

    def updateLink(self, itemId, hyperLink):
        itemRecord = self.findItem(itemId)
        itemRecord["link"] = hyperLink
        return self.__updateItem__(itemId, itemRecord)

    def findItem(self, itemId):
        # note to self.  should be a ObjectId not a str
        return self.db.items.find_one({"_id": itemId, "scene_id": self.sceneId()})

class ScenesTableModel(QtCore.QAbstractTableModel):

    columns = RadarMongoDBScene.scene_template.keys()

    def __init__(self, parent=None):
        super(ScenesTableModel, self).__init__(parent)
        self.datatable = []
        self.sync()
        self.userOnly = False
        self.hiddenColumns = [self.columns.index(k) for k in self.columns if k not in ["name", "created_on"]]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.columns[col]

    def addNewRadar(self):
        scene = RadarMongoDBScene.createNewScene()
        self.datatable.append(scene._sceneRecord)
        self.layoutChanged.emit()

    def radarFromRow(self, row):
        return self.datatable[row]

    def sync(self):
        self.datatable = [r._sceneRecord for r in RadarMongoDBScene.getScenes()]
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.columns)

    def rowCount(self, *args, **kwargs):
        return len(self.datatable)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return
        if role == QtCore.Qt.DisplayRole:
            row = self.datatable[index.row()]
            column_key = self.columns[index.column()]
            data = row[column_key]
            if column_key == "created_on":
                return data.strftime("%Y-%m-%d:%X")
            return row[column_key]
        else:
            return None


class ItemsTableModel(QtCore.QAbstractTableModel):

    columns = RadarMongoDBScene.scene_template.keys()

    updateGraphicsItemColour = Signal(str, QtGui.QColor)

    def __init__(self, radarMongoScene, parent=None):
        super(ItemsTableModel, self).__init__(parent)
        assert isinstance(radarMongoScene, RadarMongoDBScene)
        self.radarMongoScene = radarMongoScene
        self.datatable = []
        self.columns = RadarMongoDBScene.item_record_template.keys()
        self.hiddenColumns = [self.columns.index(k) for k in self.columns if k not in ["name"]]
        self.sync()

        self.colourBrush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
        self.colourBrush.setStyle(QtCore.Qt.SolidPattern)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.columns[col]

    def rowModelIndexFromId(self, idx):
        row = self.rowFromId(idx)
        data = {}
        if row != -1:
            for c in range(self.columnCount()):
                data[self.columns[c]] = self.index(row, c)
        return data

    def rowFromId(self, idx):
        foundItems = [row for row in self.datatable if str(row["_id"]) == str(idx)]
        if foundItems:
            row = self.datatable.index(foundItems[0])
            return row
        return -1

    def rawDataFromRow(self, row):
        return self.datatable[row]

    def rawDataFromId(self, id):
        row = self.rowFromId(id)
        return self.rawDataFromRow(row)

    def addNewRadarItem(self):
        self.datatable.append(self.radarMongoScene.newItem())
        self.layoutChanged.emit()
        return self.datatable[-1]

    def sync(self):
        self.datatable = self.radarMongoScene.items()
        self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.columns)

    def rowCount(self, *args, **kwargs):
        return len(self.datatable)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        row = self.datatable[index.row()]
        column_key = self.columns[index.column()]
        data = row[column_key]

        if role == QtCore.Qt.DisplayRole:

            if column_key == "created_on":
                return data.strftime("%Y-%m-%d:%X")
            return row[column_key]

        if role == QtCore.Qt.BackgroundRole:
            if column_key == "colour":
                return QtGui.QBrush(QtGui.QColor(data[0], data[1], data[2]))
        else:
            return None

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:

            row = index.row()
            column = index.column()
            col_name = self.columns[column]
            idx = self.datatable[row]["_id"]
            newData = None
            if col_name == "name":
                newData = self.radarMongoScene.updateItemName(idx, value)
            elif col_name == "comments":
                newData = self.radarMongoScene.postComment(idx, value)
            elif col_name == "tags":
                if getattr(value, "__iter__", ""):
                    newData = self.radarMongoScene.setTags(idx, value)
                else:
                    newData = self.radarMongoScene.addTag(idx, value)
            elif col_name == "tags":
                newData = self.radarMongoScene.addTag(idx, value)
            elif col_name == "colour":
                newData = self.radarMongoScene.updateColour(idx, value)
                self.updateGraphicsItemColour.emit(str(idx), value)

            if newData:
                self.datatable[row] = newData
                self.dataChanged.emit(index, index)


            return True
        return False


if __name__ == "__main__":
    scene = RadarMongoDBScene.createNewScene()
    scene.renameScene("Demo Scene 01")
    for i in range(5):
        scene.newItem()
    scene.items()
    item = scene.items()[0]
    scene.postComment(item["_id"], "I hope this works")

