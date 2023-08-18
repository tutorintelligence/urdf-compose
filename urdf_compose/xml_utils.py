import xml.etree.ElementTree as ET
from collections.abc import Iterator


def xml_attributes(el: ET.Element, element: str | None, attribute: str) -> Iterator[tuple[ET.Element, str]]:
    # note: might want to change iter to findall
    it = iter(el) if element is None else el.iter(element)
    for el_inner in it:
        val = el_inner.attrib.get(attribute)
        if val is not None:
            yield el_inner, val


# only gets it right if the order is equal as well
def el_equal(el1: ET.Element, el2: ET.Element) -> bool:
    header_eq = el1.tag == el2.tag and el1.attrib == el2.attrib
    contents_eq = len(el1) == len(el2) and all([el_equal(el1_, el2_) for el1_, el2_ in zip(el1, el2)])
    return header_eq and contents_eq


def elements_info_equal(e1: ET.Element, e2: ET.Element) -> bool:
    return e1.tag == e2.tag and e1.text == e2.text and e1.tail == e2.tail and e1.attrib == e2.attrib


def elements_equal(e1: ET.Element, e2: ET.Element) -> bool:
    return elements_info_equal(e1, e2) and len(e1) == len(e2) and all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))
