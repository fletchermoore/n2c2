import json

# as the name suggests, this is the guts of a tree
class Node():
    def __init__(self, text):
        self.text = text
        self.children = []
    
    def asJson(self): 
        ret = { "text": self.text, "children": [] }
        for child in self.children:
            jsonChild = child.asJson()
            ret["children"].append(jsonChild)
        return ret