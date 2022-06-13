from dataclasses import dataclass
from re import L
from sre_constants import FAILURE
from tkinter.tix import Tree
import xml.etree.ElementTree as ET 
from urdf_obj import URDFObj 
from typing import Dict, List, Optional, Set, Tuple, Union
import copy

NAME_KEY: str = "name"

def has_name(i: ET.Element, name_keys=set([NAME_KEY])) -> bool:
    return any(map(lambda key: key in i.attrib, name_keys))

def get_name(i: ET.Element, name_keys=set([NAME_KEY])) -> Optional[str]:
    for key in name_keys:
        if key in i.attrib:
            return i.attrib[key]

def set_name(i: ET.Element, name: str, name_keys=set([NAME_KEY])) -> Optional[str]:
    for key in name_keys:
        if key in i.attrib:
            i.attrib[key] = name

def all_names(urdf: URDFObj) -> Set[str]:
    names = set()
    for i in urdf.root:
        if has_name(i):
            names.add(get_name(i))
    return names


# only gets it right if the order is equal as well
def el_equal(el1: ET.Element, el2: ET.Element) -> bool:
    return el1.tag == el2.tag and el1.attrib == el2.attrib and len(el1) == len(el2) and [el_equal(el1_, el2_) for el1_, el2_ in zip(el1, el2)]

# removes from extender
def remove_duplicate_materials(base_urdf: URDFObj, extender_urdf: URDFObj):
    for el in base_urdf.root:
        if el.tag == "material":
            for extend_el in extender_urdf.root:
                if el_equal(el, extend_el):
                    extender_urdf.root.remove(extend_el)

    
def outlaw_duplicates(base_urdf: URDFObj, extender_urdf: URDFObj) -> Dict[str, str]:
    outlawed_names = all_names(base_urdf)
    name_map = dict()

    def make_name(name, to_add):
        if to_add == 0:
            return name 
        else:
            return name + "(" + str(to_add) + ")"

    # set up name map, and change names of top levels
    for i in extender_urdf.root:
        if has_name(i):
            name = get_name(i)
            to_add = 0
            while make_name(name, to_add) in outlawed_names:
                to_add += 1
            name_map[name] = make_name(name, to_add)
            outlawed_names.add(name_map[name])

    rename_elements(extender_urdf, name_map)
    return name_map



def rename_elements(urdf: URDFObj, name_map: Dict[str, str]):

    name_dict = set([NAME_KEY, "link"])

    def rename_element(el: ET.Element):
        if get_name(el, name_dict) in name_map:
            set_name(el, name_map[get_name(el, name_dict)], name_dict)

        for el_ in el:
            rename_element(el_)

    rename_element(urdf.root)

@dataclass
class URDFConn:
    base_link: str 
    extender_joint: str
                
# todo: base_link should also be able to automatically resolve to uniqueified version
# immutable
def connect(base_urdf: URDFObj, extender_urdf: URDFObj, conn: URDFConn, rename_dup_extender: bool = True) -> Tuple[URDFObj, Dict[str, str]]:
    
    if rename_dup_extender == False:
        raise Exception("No rename_dup_extender not implemented")

    if conn.base_link not in all_names(base_urdf):
        raise Exception("unkown link name " + conn.base_link)
    if conn.extender_joint not in all_names(extender_urdf):
        raise Exception("unkown joint name " + conn.extender_joint)

    extender_urdf = copy.deepcopy(extender_urdf)
    base_urdf = copy.deepcopy(base_urdf)

    remove_duplicate_materials(base_urdf, extender_urdf)
    name_map = outlaw_duplicates(base_urdf, extender_urdf)
    real_extender_joint = name_map[conn.extender_joint]

    for i in extender_urdf.root:
        if get_name(i) == real_extender_joint:
            if i.tag != "joint":
                raise Exception("extender_joint " + conn.extender_joint + " points to a " + i.tag)
            for el in i:
                if i.tag == "parent":
                    raise Exception("extender_joint " + conn.extender_joint + " has specified parent " + el.attrib["link"])
            parent_el = ET.Element("parent", dict([("link", conn.base_link)]))
            i.append(parent_el)
        base_urdf.root.append(i)

    return base_urdf, name_map

def urdf_append(base_urdf: URDFObj, children: List[Tuple[URDFObj, URDFConn]]) -> URDFObj:
    prev_name_map = None
    new_urdf = base_urdf
    for extender_urdf, conn in children:
        real_conn = conn if prev_name_map is None else URDFConn(prev_name_map[conn.base_link], conn.extender_joint)
        new_urdf, prev_name_map = connect(new_urdf, extender_urdf, real_conn)
    return new_urdf

class URDFTree:
    def __init__(self, urdf: URDFObj, children: List[Tuple["URDFTree", URDFConn]]):
        self.urdf = urdf 
        self.children = children

    def connect(self) -> URDFObj:
        children_urdfs = [(tree.connect(), conn) for tree, conn in self.children]
        return urdf_append(self.urdf, children_urdfs)


if __name__ == "__main__":
    num_extenders = 50
    connections = [(URDFObj("urdfs/extender.urdf"), URDFConn("extender", "fixed_extender")) for _ in range(num_extenders - 1)]
    new_urdf = urdf_append(URDFObj("urdfs/extender.urdf"), connections)
    new_urdf.write("urdfs/putTogether2.urdf")
