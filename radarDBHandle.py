__author__ = "dmoulder"

from PySide import QtCore
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
        "colour": [255, 255, 255, 0],
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
            return result.inserted_id

    def updatePosition(self, itemId, x, y):
        itemRecord = self.findItem(itemId)
        itemRecord["pos"] = [x, y]
        self.__updateItem__(itemId, itemRecord)

    def postComment(self, itemId, text):
        comment = {"date": datetime.datetime.now(),
                   "user": getpass.getuser(),
                   "text": str(text)}
        itemRecord = self.findItem(itemId)
        itemRecord["comments"].append(comment)
        self.__updateItem__(itemId, itemRecord)

    def updateDescription(self, itemId, text):
        itemRecord = self.findItem(itemId)
        itemRecord["description"] = text
        self.__updateItem__(itemId, itemRecord)

    def addTag(self, itemId, tag):
        itemRecord = self.findItem(itemId)
        if tag not in itemRecord["tags"]:
            itemRecord["tags"].append(tag)
            self.__updateItem__(itemId, itemRecord)

    def deleteTag(self, itemId, tag):
        itemRecord = self.findItem(itemId)
        if tag in itemRecord["tags"]:
            itemRecord["tags"] = itemRecord["tags"].remove(tag)
            self.__updateItem__(itemId, itemRecord)

    def clearTags(self, itemId):
        itemRecord = self.findItem(itemId)
        itemRecord["tags"] = []
        self.__updateItem__(itemId, itemRecord)

    def updateColour(self, itemId, colour):
        itemRecord = self.findItem(itemId)
        itemRecord["colour"] = [colour.toRGBF()]
        self.__updateItem__(itemId, itemRecord)

    def updateLink(self, itemId, hyperLink):
        itemRecord = self.findItem(itemId)
        itemRecord["link"] = hyperLink
        self.__updateItem__(itemId, itemRecord)

    def findItem(self, itemId):
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

if __name__ == "__main__":
    scene = RadarMongoDBScene.createNewScene()
    scene.renameScene("Demo Scene 01")
    for i in range(5):
        scene.newItem()
    scene.items()
    item = scene.items()[0]
    scene.postComment(item["_id"], "I hope this works")

