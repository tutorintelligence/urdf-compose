from pathlib import Path

from examples.simple_chain.make_chain import ROD_PATH
from urdf_compose import (
    ExplicitURDFObj,
    URDFConn,
    branch,
    raise_if_compose_error,
    write_and_check_urdf,
)

DIR = Path(__file__).parent
V_ROD_PATH = DIR / "v_rod.urdf"
SIMPLE_BRANCHED_CHAIN = DIR / "simple_branched_chain.urdf"
FULL_BRANCHED_CHAIN = DIR / "full_branched_chain.urdf"


def make_simple_branched_chain() -> None:
    rod_urdf1 = ExplicitURDFObj(ROD_PATH)
    rod_urdf2 = ExplicitURDFObj(ROD_PATH)
    v_rod_urdf = ExplicitURDFObj(V_ROD_PATH)
    simple_branched_chain = raise_if_compose_error(
        branch(v_rod_urdf, [rod_urdf1, (rod_urdf2, URDFConn("sideways_output"))])
    )
    write_and_check_urdf(simple_branched_chain, SIMPLE_BRANCHED_CHAIN)


if __name__ == "__main__":
    make_simple_branched_chain()
