from examples.simple_chain.make_chain import ROD_PATH
from urdf_compose import ExplicitURDFObj
from urdf_compose.compose import raise_if_compose_error, sequence
from urdf_compose.composed_urdf import RepeatedURDFError


class TestNameMap:
    def test_simple_collapse(self) -> None:
        extender_urdf1 = ExplicitURDFObj(ROD_PATH)
        extender_urdf2 = ExplicitURDFObj(ROD_PATH)
        extender_urdf3 = ExplicitURDFObj(ROD_PATH)
        composed_urdf = raise_if_compose_error(sequence(extender_urdf1, extender_urdf2, extender_urdf3))
        name_map = composed_urdf.name_map.collapse_strict({extender_urdf1, extender_urdf2, extender_urdf3})
        assert name_map.lookup(extender_urdf1, "joint") == "joint"
        assert name_map.lookup(extender_urdf2, "joint") == "joint(2)"
        assert name_map.lookup(extender_urdf3, "joint") == "joint(1)"

    def test_bad_collapse_with_same_urdf(self) -> None:
        extender_urdf = ExplicitURDFObj(ROD_PATH)
        composed_urdf = raise_if_compose_error(sequence(extender_urdf, extender_urdf))
        name_map = composed_urdf.name_map.collapse_safe({extender_urdf})
        assert isinstance(name_map, RepeatedURDFError)

    def test_not_strict_repeated_urdf_is_fine_if_not_given_as_primitive(self) -> None:
        extender_urdf = ExplicitURDFObj(ROD_PATH)
        extender_urdf2 = ExplicitURDFObj(ROD_PATH)
        composed_urdf = raise_if_compose_error(sequence(extender_urdf, extender_urdf2, extender_urdf))
        name_map = composed_urdf.name_map.collapse({extender_urdf2})
        assert name_map.lookup(extender_urdf2, "joint") == "joint(2)"
