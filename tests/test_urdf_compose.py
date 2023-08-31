from pathlib import Path

from urdf_compose import ExplicitURDFObj, URDFConn, branch, sequence
from urdf_compose.compose import raise_if_compose_error, write_and_check_urdf


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
        connected_urdf = raise_if_compose_error(
            sequence(
                ExplicitURDFObj(dir / "extender.urdf"),
                *[(extender_urdf, URDFConn("vgc10_extender_stick")) for _ in range(num_extenders - 1)],
            )
        )
        write_and_check_urdf(connected_urdf, output)

    def test_urdf2(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        composed_urdf = raise_if_compose_error(sequence(*urdfs))
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_alternating_urdf(self) -> None:
        dir = Path(__file__).parent
        urdfs = [
            ExplicitURDFObj(dir / "extender.urdf"),
            ExplicitURDFObj(dir / "extender2.urdf"),
            ExplicitURDFObj(dir / "extender.urdf"),
        ]
        composed_urdf = raise_if_compose_error(sequence(*urdfs))
        composed_urdf.name_map.collapse_strict(set(urdfs))

    def test_can_sequence_with_same_urdf(self) -> None:
        dir = Path(__file__).parent
        urdf_obj = ExplicitURDFObj(dir / "extender.urdf")
        raise_if_compose_error(
            sequence(
                urdf_obj,
                urdf_obj,
            )
        )

    def test_can_branch_with_same_urdf(self) -> None:
        dir = Path(__file__).parent
        urdf_obj = ExplicitURDFObj(dir / "extender.urdf")
        raise_if_compose_error(
            branch(
                urdf_obj,
                [urdf_obj],
            )
        )

    def test_can_branch_with_equivilant_urdfs(self) -> None:
        dir = Path(__file__).parent
        raise_if_compose_error(
            branch(
                ExplicitURDFObj(dir / "extender.urdf"),
                [ExplicitURDFObj(dir / "extender.urdf")],
            )
        )
