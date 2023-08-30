from pathlib import Path

from urdf_compose import ExplicitURDFObj, raise_if_compose_error, sequence
from urdf_compose.compose import write_and_check_urdf

DIR = Path(__file__).parent
ROD_PATH = DIR / "rod.urdf"
ROD_PAIR_PATH = DIR / "rod_pair.urdf"
CHAIN_PATH = DIR / "chain.urdf"


def create_pair() -> None:
    extender_urdf = ExplicitURDFObj(ROD_PATH)
    composed_urdf = raise_if_compose_error(sequence(extender_urdf, extender_urdf))
    write_and_check_urdf(composed_urdf, ROD_PAIR_PATH)


def create_chain() -> None:
    extender_urdf = ExplicitURDFObj(ROD_PATH)
    num_extenders = 10
    composed_urdf = raise_if_compose_error(sequence(extender_urdf, *[extender_urdf for _ in range(num_extenders - 1)]))
    write_and_check_urdf(composed_urdf, CHAIN_PATH)


def illustrate_name_map() -> None:
    extender_urdf1 = ExplicitURDFObj(ROD_PATH)
    extender_urdf2 = ExplicitURDFObj(ROD_PATH)
    composed_urdf = raise_if_compose_error(sequence(extender_urdf1, extender_urdf2))
    name_map = composed_urdf.name_map.collapse_strict({extender_urdf1, extender_urdf2})
    assert name_map.lookup(extender_urdf1, "joint") == "joint"
    assert name_map.lookup(extender_urdf2, "joint") == "joint(1)"


if __name__ == "__main__":
    create_pair()
    create_chain()
    illustrate_name_map()
