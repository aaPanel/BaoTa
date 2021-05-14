# -*- coding=utf-8
import xml.etree.ElementTree


class Xml2Dict(dict):

    def __init__(self, parent_node):
        if parent_node.items():
            self.updateDict(dict(parent_node.items()))
        for element in parent_node:
            if len(element):
                aDict = Xml2Dict(element)
                self.updateDict({element.tag: aDict})
            elif element.items():
                elementattrib = element.items()
                if element.text:
                    elementattrib.append((element.tag, element.text))
                self.updateDict({element.tag: dict(elementattrib)})
            else:
                self.updateDict({element.tag: element.text})

    def updateDict(self, aDict):
        for key in aDict:
            if key in self:
                value = self.pop(key)
                if type(value) is not list:
                    lst = list()
                    lst.append(value)
                    lst.append(aDict[key])
                    self.update({key: lst})
                else:
                    value.append(aDict[key])
                    self.update({key: value})
            else:
                self.update({key: aDict[key]})


if __name__ == "__main__":
    s = """<?xml version="1.0" encoding="utf-8" ?>
    <result xmlns= "wqa.bai.com">
        <count n="1">10</count>
        <data><id>1</id><name>test1</name></data>
        <data><id>2</id><name>test2</name></data>
        <data><id>3</id><name>test3</name></data>
    </result>"""
    root = xml.etree.ElementTree.fromstring(s)
    xmldict = Xml2Dict(root)
    print(xmldict)
