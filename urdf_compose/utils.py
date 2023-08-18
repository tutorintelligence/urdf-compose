import xml.etree.ElementTree as ET
from collections.abc import Iterator

import urdf_compose.xml_utils as xml
from urdf_compose.urdf_obj import URDFObj

NAME_KEY: str = "name"

name_key_set = frozenset([NAME_KEY])


def has_name(i: ET.Element, name_keys: frozenset[str] = name_key_set) -> bool:
    return any(map(lambda key: key in i.attrib, name_keys))


def get_name(i: ET.Element, name_keys: frozenset[str] = name_key_set) -> str | None:
    for key in name_keys:
        if key in i.attrib:
            return i.attrib[key]
    return None


def set_name(i: ET.Element, name: str, name_keys: frozenset[str] = name_key_set) -> None:
    for key in name_keys:
        if key in i.attrib:
            i.attrib[key] = name


def all_names(urdf: URDFObj) -> set[str]:
    names = set()
    for i in urdf.getroot():
        if name := get_name(i):
            names.add(name)
    return names


def find_element_named(urdf: URDFObj, element: str | None, name: str) -> ET.Element | None:
    for el, val in xml.xml_attributes(urdf.getroot(), element, "name"):
        if val == name:
            return el
    return None


def iter_model_attribute(urdf: URDFObj, element: str, attribute: str) -> Iterator[tuple[ET.Element, str]]:
    root = urdf.getroot()

    for el in root.iter(element):
        val = el.attrib.get(attribute)
        if val is not None:
            yield el, val
