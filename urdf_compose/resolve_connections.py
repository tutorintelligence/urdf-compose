from dataclasses import dataclass

from urdf_compose.composed_urdf import URDFConn
from urdf_compose.urdf_compose_error import URDFComposeError
from urdf_compose.urdf_obj import URDFObj, check_urdf  # noqa


@dataclass
class URDFDefConn:
    base_link: str
    extender_link: str


def resolve_conn(
    base_urdf: URDFObj,
    extender_urdf: URDFObj,
    conn: URDFConn,
) -> URDFDefConn | URDFComposeError:
    msg = f"Base URDFs: {base_urdf}, Extension URDFs: {extender_urdf}, Connection: {conn}"

    def get_resolve_error(error: str) -> URDFComposeError:
        return URDFComposeError(f"[{msg}]\n{error}", base_urdf, extender_urdf)

    def check_for_link(
        urdf: URDFObj, link_name: str | None, default_prefix: str, regular_prefix: str
    ) -> str | URDFComposeError:
        real_base_link = None
        for el in urdf.getroot().findall("link"):
            name = el.attrib["name"]
            if (link_name is None and name.find(f"{default_prefix}-") == 0) or (
                link_name is not None
                and (name == f"{regular_prefix}-{link_name}" or name == f"{default_prefix}-{link_name}")
            ):
                if real_base_link is None:
                    real_base_link = name
                else:
                    return get_resolve_error(
                        f"Multiple matches for default {default_prefix} link"
                        if link_name is None
                        else f"Multiple matches for {regular_prefix} link {link_name}"
                    )

        if not real_base_link:
            return get_resolve_error(
                f"Could not find default {regular_prefix} link"
                if link_name is None
                else (
                    f"Could not find {regular_prefix} link {regular_prefix}-{link_name} or "
                    f"{default_prefix}-{link_name}"
                )
            )
        return real_base_link

    real_base_link = check_for_link(base_urdf, conn.base_link, "OUTPUT", "output")
    if isinstance(real_base_link, URDFComposeError):
        return real_base_link
    real_extender_link = check_for_link(extender_urdf, conn.extender_link, "INPUT", "input")
    if isinstance(real_extender_link, URDFComposeError):
        return real_extender_link

    return URDFDefConn(
        real_base_link,
        real_extender_link,
    )
