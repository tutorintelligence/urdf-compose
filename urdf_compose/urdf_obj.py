import copy
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid1

from urdf_compose.xml_utils import elements_equal

# URDFObj should not be specific to us as Tutor


class CheckURDFFailure(Exception):
    pass


_global_check_urdf_enabled = True


def globally_disable_check_urdf() -> None:
    """
    If you can't install check_urdf, you can globally disable it here
    If you do, the "check_urdf" will always just return None
    """
    global _global_check_urdf_enabled
    _global_check_urdf_enabled = False


def globally_enable_check_urdf() -> None:
    """
    check_urdf will default to be enabled, but if you disable it,
    you can re-enable it here
    """
    global _global_check_urdf_enabled
    _global_check_urdf_enabled = True


def check_urdf(urdf_path: Path) -> CheckURDFFailure | None:
    if not _global_check_urdf_enabled:
        return None

    with subprocess.Popen(
        [f'check_urdf "{urdf_path}" > /dev/null'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    ) as p:
        assert p.stderr is not None, "Pstderr was None"
        stderr = str(p.stderr.read(), "utf-8")
    if stderr == "":
        return None
    return CheckURDFFailure(stderr)


class URDFObj:
    """
    Represents a single urdf
    """

    def __init__(self, tree: ET.ElementTree):
        self.tree = tree

    def getroot(self) -> ET.Element:
        return self.tree.getroot()

    def write_xml(self, dest: Path) -> None:
        dir = dest.parent
        if not dir.is_dir():
            os.makedirs(str(dest.parents[0]))
        dest.touch(exist_ok=True)
        self.tree.write(str(dest), xml_declaration=True, encoding="UTF-8")

    def __hash__(self) -> int:
        return hash(id(self))

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, URDFObj) and id(self) == id(__value)

    def same_structure(self, urdf: "URDFObj") -> bool:
        root1 = self.getroot()
        root2 = urdf.getroot()

        if len(root1) != len(root2):
            return False

        for el1, el2 in zip(root1, root2, strict=True):
            if not elements_equal(el1, el2):
                return False

        return True


class ExplicitURDFObj(URDFObj):
    """
    Represents the urdf of a certain file
    """

    def __init__(self, path: Path, check: bool = True):
        self.path = Path(path)
        if not self.path.exists():
            raise RuntimeError(f"Attempted to create URDFObj from non-existent file {self.path}")

        tree = ET.ElementTree()
        tree.parse(str(self.path))
        super().__init__(tree)

        if check:
            check_urdf_result = check_urdf(path)
            if check_urdf_result is not None:
                raise check_urdf_result

    def __repr__(self) -> str:
        return f"ExplicitURDFObj from {self.path.name}"
