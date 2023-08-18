import copy
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid1

from urdf_compose.xml_utils import elements_equal

# URDFObj should not be specific to us as Tutor

std_materials = ET.fromstring(
    """

<!-- Materials -->
<robot>
    <material name="Black">
        <color rgba="0.0 0.0 0.0 1.0" />
    </material>
    <material name="Red">
        <color rgba="0.85 0.19  0.21 1.0" />
    </material>
    <material name="Blue">
        <color rgba="0.28 0.52 0.92 1.0" />
    </material>
    <material name="Green">
        <color rgba="0.23 0.72 0.32 1.0" />
    </material>
    <material name="Yellow">
        <color rgba="0.95 0.76 0.05 1.0" />
    </material>
    <material name="White">
        <color rgba="1.0 1.0 1.0 1.0" />
    </material>
    <material name="Silver">
        <color rgba="0.753 0.753 0.753 1.0" />
    </material>
    <material name="DarkGrey">
        <color rgba="0.2 0.2 0.2 1.0" />
    </material>
</robot>
"""
)


class CheckURDFFailure(Exception):
    pass


def check_urdf(urdf_path: Path) -> CheckURDFFailure | None:
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
    Represents a single urdf. Is mostly a thin wrapper over an ET.ElementTree
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

    def _add_colors(self) -> None:
        materials_used = set()
        materials_defined = set()
        for material in self.getroot().iter("material"):
            name = material.attrib["name"]
            if len(material) == 0:
                materials_used.add(name)
            else:
                materials_defined.add(name)

        for mat in std_materials:
            if mat.attrib["name"] in materials_used and mat.attrib["name"] not in materials_defined:
                self.getroot().append(copy.deepcopy(mat))

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
        self.path = path
        if not self.path.exists():
            raise RuntimeError(f"Attempted to create URDFObj from non-existent file {self.path}")

        tree = ET.ElementTree()
        tree.parse(str(self.path))
        super().__init__(tree)
        self._add_colors()

        if check:
            check_file = self.path.parent / f"{self.path.name}_check_urdfOBJ{uuid1()}.urdf"
            self.write_xml(check_file)
            check_urdf_result = check_urdf(check_file)

            if check_file.exists() and check_urdf_result is None:
                check_file.unlink()
            else:
                raise RuntimeError(
                    f"Attempted to create URDFObj, but given invalid urdf file {path}. You can"
                    f"check adjusted file at {check_file}. {check_urdf_result=}",
                )

    def __repr__(self) -> str:
        return f"ExplicitURDFObj from {self.path.name}"
