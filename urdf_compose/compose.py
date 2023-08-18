import copy
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TypeAlias

from urdf_compose.composed_urdf import ComposedURDFObj, URDFConn
from urdf_compose.connect import connect
from urdf_compose.resolve_connections import URDFDefConn, resolve_conn
from urdf_compose.urdf_compose_error import URDFComposeError
from urdf_compose.urdf_obj import CheckURDFFailure, URDFObj, check_urdf  # noqa
from urdf_compose.utils import get_name


def general_urdf_append(
    base_urdf: URDFObj,
    children: list[tuple[URDFObj, URDFDefConn]],
    use_name_map: bool,
) -> ComposedURDFObj | URDFComposeError:
    prev_name_map = None
    new_urdf = ComposedURDFObj.construct(base_urdf)
    for extender_urdf, conn in children:
        if prev_name_map is not None:
            conn = URDFDefConn(
                prev_name_map[conn.base_link] if use_name_map else conn.base_link,
                conn.extender_link,
            )

        connection_result = connect(new_urdf, extender_urdf, conn)
        if isinstance(connection_result, URDFComposeError):
            return connection_result
        new_urdf = connection_result
    return new_urdf


zero_intertial_element = ET.fromstring(
    """
    <inertial>
        <origin xyz="0 0 0" rpy="0 0 0" />
        <mass value="0" />
        <inertia ixx="0" ixy="0" ixz="0" iyy="0" iyz="0" izz="0" />
    </inertial>
    """
)


def fix_urdf(urdf: URDFObj) -> None:
    for link in urdf.tree.findall("link"):
        if get_name(link) != "world" and link.find("inertial") is None:
            link.append(copy.deepcopy(zero_intertial_element))


GenURDFTree: TypeAlias = "URDFTree | URDFObj"
"""
A URDFTree or a URDFObj. This is helpful as a type b/c many of the composition
operations works both URDFTrees, and on URDFObjs.
"""
TreeChild: TypeAlias = "GenURDFTree | tuple[GenURDFTree, URDFConn]"
"""
Either a regular GenURDFTree, or a GenURDFTree with an explciit URDFConn. A
lone GenURDFTree with no URDFConn assumes use of default connection (where
the default connection is starting with upper-case "INPUT" and "OUTPUT" rather
than any link starting with lower-case "input" and "output")
"""
URDFObjChild: TypeAlias = URDFObj | tuple[URDFObj, URDFConn]
"""
Like TreeChild except only for single URDFObjs
"""


# A visualization tool for URDFTree would be super cool
class URDFTree:
    """
    Represents a web of URDFObjects that can be connected
    """

    def __init__(
        self,
        urdf: URDFObj,
        *children: tuple[GenURDFTree, URDFConn],
    ):
        self.urdf = urdf
        self.children = children

    def connect_safe(self) -> ComposedURDFObj | URDFComposeError:
        children_urdfs = list[tuple[URDFObj, URDFDefConn]]()
        for tree, conn in self.children:
            obj = tree if isinstance(tree, URDFObj) else tree.connect_safe()
            if not isinstance(obj, URDFObj):
                return obj
            def_conn = resolve_conn(
                self.urdf,
                tree if isinstance(tree, URDFObj) else tree.urdf,
                conn,
            )
            if isinstance(def_conn, URDFComposeError):
                return def_conn
            children_urdfs.append((obj, def_conn))
        return general_urdf_append(self.urdf, children_urdfs, use_name_map=False)

    def connect(self, log_errored_urdf_dir: Path | None = None) -> ComposedURDFObj:
        result = self.connect_safe()
        if isinstance(result, URDFComposeError):
            if log_errored_urdf_dir is not None:
                result.save_to(log_errored_urdf_dir)
            raise result
        return result

    def __iter__(self) -> Iterator[URDFObj]:
        yield self.urdf
        for child, _ in self.children:
            if isinstance(child, URDFObj):
                yield child
            else:
                for urdf in child:
                    yield urdf


def fix_tree_child(c: TreeChild) -> tuple[GenURDFTree, URDFConn]:
    return c if isinstance(c, tuple) else (c, URDFConn())


def fix_urdf_obj_child(
    c: URDFObjChild,
) -> tuple[URDFObj, URDFConn]:
    return c if isinstance(c, tuple) else (c, URDFConn())


def branch(urdf: URDFObj, children: Iterable[TreeChild]) -> URDFTree:
    """
    Creates a URDFTree with urdf as the base, and where each value in children
      is directly connected to urdf

    Raises a runtime error if given two of the same urdfs.
    """
    children_trees_or_urdfs = [child[0] if isinstance(child, tuple) else child for child in children]
    children_urdfs = [tree_or_urdf for tree_or_urdf in children_trees_or_urdfs if isinstance(tree_or_urdf, URDFObj)]
    all_urdfs = [urdf] + children_urdfs
    if len(all_urdfs) != len(set(all_urdfs)):
        raise RuntimeError("Attempted to create branch with two of the same URDFs. This is an illegal operation.")
    return URDFTree(urdf, *[fix_tree_child(c) for c in children])


def sequence(base: URDFObj, *children: URDFObjChild, branch: "TreeChild | None" = None) -> URDFTree:  # noqa: TC101
    """
    Creates a URDFTree where each urdf is connected to the previous once. All the urdfs aside
    from the "branch" argument must be single urdfs. The branch may be a Tree.
    """
    fixed_children = [fix_urdf_obj_child(c) for c in children]
    empty = len(fixed_children) == 0
    if empty:
        last = base
    else:
        last = fixed_children[-1][0]

    if branch is None:
        tree = URDFTree(last)
    else:
        fixed_branch = fix_tree_child(branch)
        urdf = fixed_branch[0]
        tree = URDFTree(urdf) if isinstance(urdf, URDFObj) else urdf
        tree = URDFTree(last, (tree, fixed_branch[1]))

    for i in reversed(range(len(fixed_children))):
        tree = URDFTree(base if i == 0 else fixed_children[i - 1][0], (tree, fixed_children[i][1]))
    return tree


def write_and_check_urdf(urdf: URDFObj, dest: Path, perform_fix: bool = True) -> CheckURDFFailure | None:
    """
    1. if "perform_fix" is true, call "fix_urdf"
    2. write the urdf to given destination
    3. check if the urdf is valid
    """
    if perform_fix:
        fix_urdf(urdf)
    urdf.write_xml(dest)
    return check_urdf(dest)
