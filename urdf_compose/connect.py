import xml.etree.ElementTree as ET

from urdf_compose.composed_urdf import ComposedURDFObj, first_available_from_urdf
from urdf_compose.resolve_connections import URDFDefConn
from urdf_compose.urdf_compose_error import InteranlURDFComposeError, URDFComposeError
from urdf_compose.urdf_obj import URDFObj
from urdf_compose.utils import find_element_named


def check_for_connection_issue(
    base_urdf: ComposedURDFObj,
    extender_urdf: URDFObj,
    conn: URDFDefConn,
) -> str | None:
    # verify that link and joint exist
    base_link = find_element_named(base_urdf, "link", conn.base_link)
    if base_link is None:
        return (
            f"Unknown base link {conn.base_link}. Have {[el.attrib['name'] for el in base_urdf.tree.findall('link')]}"
        )
    if len(base_link) > 0:
        return f"Found non-empty output link {conn.base_link}"
    # base_urdf.getroot().remove(base_link)
    if find_element_named(extender_urdf, "link", conn.extender_link) is None:
        return f"Extender link name unknown: {conn.extender_link}"

    for el in base_urdf.getroot().findall("joint"):
        parent_el = el.find("parent")
        if parent_el is not None and parent_el.attrib["link"] == conn.base_link:
            name = el.attrib["name"]
            return f"Attempted to connect to output link {conn.base_link}, but it already connected to joint {name}"

    for el in extender_urdf.getroot().findall("joint"):
        child_el = el.find("child")
        if child_el is not None and child_el.attrib["link"] == conn.extender_link:
            name = el.attrib["name"]
            return f"Attempted to connect to input link {conn.extender_link}, but it already connected to joint {name}"
    return None


def get_dummy_joint(name: str, base_link: str, extender_link: str) -> ET.Element:
    return ET.fromstring(
        f"""
<joint name="{name}" type="fixed">
    <origin xyz="0 0 0" rpy="0 0 0" />
    <parent link="{base_link}" />
    <child link="{extender_link}" />
    <axis xyz="0 0 0" />
</joint>
"""
    )


def connect(
    base_urdf: ComposedURDFObj,
    extender_urdf_: URDFObj,
    conn: URDFDefConn,
) -> ComposedURDFObj | URDFComposeError:
    extender_urdf = ComposedURDFObj.construct(extender_urdf_)
    base_urdf = base_urdf.copy()

    connection_issue = check_for_connection_issue(base_urdf, extender_urdf, conn)
    if connection_issue is not None:
        msg = f"Base URDF: {base_urdf}, Extension URDF: {extender_urdf}, Connection: {conn}"
        return URDFComposeError(f"[{msg}] {connection_issue}", base_urdf, extender_urdf)

    extender_urdf.remove_duplicate_materials(base_urdf)
    new_base_link_name = f"CONNECTED:{conn.base_link}"
    new_extender_link_name = first_available_from_urdf(extender_urdf, f"CONNECTED:{conn.extender_link}")
    connection_joint_name = "GENERATED_CONNECTION"

    real_new_base_link_name = first_available_from_urdf(base_urdf, new_base_link_name)

    extender_urdf.rename_elements({conn.extender_link: new_extender_link_name})
    base_urdf.rename_elements({conn.base_link: real_new_base_link_name})
    base_urdf.concatenate(extender_urdf) #TODO Back propigate changes into extender map.

    real_connection_joint_name = first_available_from_urdf(base_urdf, connection_joint_name)
    real_extender_link_name = base_urdf.name_map.lookup(extender_urdf_, conn.extender_link)
    if real_extender_link_name is None:
        raise InteranlURDFComposeError(
            f"Could not find {conn.extender_link = } in extneder urdf, even though check_for_connection_issue passed"
        )
    new_joint = get_dummy_joint(real_connection_joint_name, real_new_base_link_name, real_extender_link_name)
    base_urdf.getroot().insert(-1 * len(extender_urdf.getroot()), new_joint)

    return base_urdf
