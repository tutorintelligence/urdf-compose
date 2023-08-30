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
        connected_urdf = sequence(
            ExplicitURDFObj(dir / "extender.urdf"),
            *[(extender_urdf, URDFConn("vgc10_extender_stick")) for _ in range(num_extenders - 1)],
        )
        assert write_and_check_urdf(connected_urdf, output) is None

    def test_urdf2(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        composed_urdf = sequence(*urdfs)
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_alternating_urdf(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender2.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        composed_urdf = sequence(*urdfs)
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_can_sequence_with_same_urdf(self) -> None:
        dir = Path(__file__).parent
        urdf_obj = ExplicitURDFObj(dir / "extender.urdf")
        sequence(
            urdf_obj,
            urdf_obj,
        )

    def test_can_branch_with_same_urdf(self) -> None:
        dir = Path(__file__).parent
        urdf_obj = ExplicitURDFObj(dir / "extender.urdf")
        branch(
            urdf_obj,
            [urdf_obj],
        )

    def test_can_branch_with_equivilant_urdfs(self) -> None:
        dir = Path(__file__).parent
        branch(
            ExplicitURDFObj(dir / "extender.urdf"),
            [ExplicitURDFObj(dir / "extender.urdf")],
        )
