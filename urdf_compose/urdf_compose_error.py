from pathlib import Path

from urdf_compose.urdf_obj import URDFObj


class URDFComposeError(RuntimeError):
    def __init__(self, msg: str, base_urdf: URDFObj, extender_urdf: URDFObj):
        super().__init__(msg)
        self.base_urdf = base_urdf
        self.extender_urdf = extender_urdf
        self.saved_locations = list[str]()

    def save_to(self, dir: Path) -> None:
        base_output_name = "base_error.urdf"
        extender_output_name = "extender_error.urdf"
        self.base_urdf.write_xml(dir / base_output_name)
        self.extender_urdf.write_xml(dir / extender_output_name)
        self.saved_locations.append(f"Debugging files {base_output_name} and {extender_output_name} outputted in {dir}")

    def __str__(self) -> str:
        saved_location_str = "" if len(self.saved_locations) == 0 else self.saved_locations[-1]
        return f"{super().__str__()}\n{saved_location_str}"


class InteranlURDFComposeError(RuntimeError):
    pass
