from collections.abc import Iterable
from pathlib import Path
from typing import TypeAlias, TypeVar

from urdf_compose.composed_urdf import ComposedURDFObj, URDFConn
from urdf_compose.connect import connect
from urdf_compose.resolve_connections import URDFDefConn, resolve_conn
from urdf_compose.urdf_compose_error import URDFComposeError
from urdf_compose.urdf_obj import CheckURDFFailure, URDFObj, check_urdf  # noqa


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


URDFObjOrError = URDFObj | URDFComposeError
URDFObjChild: TypeAlias = URDFObjOrError | tuple[URDFObjOrError, URDFConn]
"""
Either a regular URDFObjOrError, or a URDFObjOrError with an explciit URDFConn. A
lone URDFObjOrError with no URDFConn assumes use of default connection (where
the default connection is starting with upper-case "INPUT" and "OUTPUT" rather
than any link starting with lower-case "input" and "output")
"""


def fix_urdf_obj_child(
    c: URDFObjChild,
) -> tuple[URDFObjOrError, URDFConn]:
    return c if isinstance(c, tuple) else (c, URDFConn())


T = TypeVar("T")


def raise_if_compose_error(v: T | URDFComposeError, save_error_dir: Path | None = None) -> T:
    """
    Will raise if the value is a URDFComposeError, and will save debugging info if given
    a `save_error_dir`

    Otherwise, will return the value, indicating to typing it is not a URDFComposeError
    """
    if isinstance(v, URDFComposeError):
        if save_error_dir is not None:
            v.save_to(save_error_dir)
        raise v
    return v


def branch(urdf: URDFObjOrError, children: Iterable[URDFObjChild]) -> ComposedURDFObj | URDFComposeError:
    """
    Creates a composed urdf object where each of the children connects directly to the base urdf

    Returns any errors encountered during composition, or if any of the inputs
    have an error instead of a urdf object.
    """
    fixed_children = [fix_urdf_obj_child(c) for c in children]
    real_children = []
    if isinstance(urdf, URDFComposeError):
        return urdf
    for fixed_child in fixed_children:
        if isinstance(fixed_child[0], URDFComposeError):
            return fixed_child[0]
        # We do a branch here to create a unique composed urdf obj key for each child
        # This stops name collisions if a user inputs two of the same urdfs to branch
        real_children.append((wrap_urdf_as_composed(fixed_child[0]), fixed_child[1]))

    children_urdfs = list[tuple[URDFObj, URDFDefConn]]()
    for obj, conn in real_children:
        if not isinstance(obj, URDFObj):
            return obj
        def_conn = resolve_conn(
            urdf,
            obj,
            conn,
        )
        if isinstance(def_conn, URDFComposeError):
            return def_conn
        children_urdfs.append((obj, def_conn))
    return general_urdf_append(urdf, children_urdfs, use_name_map=False)


def wrap_urdf_as_composed(urdf: URDFObj) -> ComposedURDFObj:
    return raise_if_compose_error(branch(urdf, []), None)


def sequence(base: URDFObjOrError, *children: URDFObjChild) -> ComposedURDFObj | URDFComposeError:
    """
    Creates a composed urdf, where each urdf connects to the previous

    Returns any errors encountered during composition, or if any of the inputs
    have an error instead of a urdf object.
    """
    if len(children) == 0:
        return wrap_urdf_as_composed(base) if isinstance(base, URDFObj) else base
    else:
        child0_urdf, child0_conn = fix_urdf_obj_child(children[0])
        return branch(base, [(sequence(child0_urdf, *children[1:]), child0_conn)])


def write_and_check_urdf(urdf: URDFObj, dest: Path) -> None:
    """
    1. write the urdf to given destination
    2. check if the urdf is valid

    Raises a CheckURDFFailure if check urdf fails
    """
    urdf.write_xml(dest)
    if (error := check_urdf(dest)) is not None:
        raise error
