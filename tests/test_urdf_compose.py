from pathlib import Path

import pytest

from urdf_compose import ExplicitURDFObj, URDFConn, branch, sequence
from urdf_compose.compose import write_and_check_urdf


class TestURDFCompose:
    def test_urdf(self) -> None:
        num_extenders = 3
        dir = Path(__file__).parent
        output = dir / "output.urdf"
        try:
            output.unlink()
        except BaseException:
            pass
        extender_urdf = ExplicitURDFObj(dir / "extender.urdf")
        tree = sequence(
            ExplicitURDFObj(dir / "extender.urdf"),
            *[(extender_urdf, URDFConn("vgc10_extender_stick")) for _ in range(num_extenders - 1)],
        )
        connected_urdf = tree.connect()
        assert write_and_check_urdf(connected_urdf, output) is None

    def test_urdf2(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        tree = sequence(*urdfs)
        composed_urdf = tree.connect()
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_alternating_urdf(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender2.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        tree = sequence(*urdfs)
        composed_urdf = tree.connect()
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_cant_branch_with_same_urdf(self) -> None:
        dir = Path(__file__).parent
        urdf_obj = ExplicitURDFObj(dir / "extender.urdf")
        with pytest.raises(RuntimeError):
            branch(
                urdf_obj,
                [urdf_obj],
            )

    def test_can_branch_with_equivilant_urdfs(self) -> None:
        dir = Path(__file__).parent
        b = branch(
            ExplicitURDFObj(dir / "extender.urdf"),
            [ExplicitURDFObj(dir / "extender.urdf")],
        )
        b.connect()
