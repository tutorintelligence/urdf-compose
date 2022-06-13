from lib2to3.pgen2.token import NAME
from optparse import Option
from typing import Set
import xml.etree.ElementTree as ET 

class URDFObj:
    
    def __init__(self, path: str):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()