from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from typing_extensions import Self

import urdf_compose.xml_utils as xml
from urdf_compose.urdf_compose_error import InteranlURDFComposeError
from urdf_compose.urdf_obj import URDFObj
from urdf_compose.utils import (
    NAME_KEY,
    all_names,
    find_element_named,
    get_name,
    has_name,
    set_name,
)


class UnaccountedForURDFError(RuntimeError):
    def __init__(self, unaccounted_for_urdf: URDFObj) -> None:
        self.unaccounted_for_urdf = unaccounted_for_urdf
        super().__init__()


class RepeatedURDFError(RuntimeError):
    def __init__(self, repeated_urdf: URDFObj) -> None:
        self.repeated_urdf = repeated_urdf
        super().__init__()


NameMapLookup = dict[URDFObj, dict[str, str]]


class ComposedURDFNameMap:
    """
    An object to lookup the new names of links after composition occurs
    """

    def __init__(
        self,
        name_map_lookup: NameMapLookup,
        name_to_urdf_and_og_name: dict[str, tuple[URDFObj, str]],
    ) -> None:
        self.name_map_lookup = name_map_lookup
        # Name map lookup: goes from a urdf object, to a name map, #
        # where the name map maps original name to new name
        self.name_to_urdf_and_og_name = name_to_urdf_and_og_name
        # Maps name in composed urdf to the original urdf and name it comes from
        # Values are a list b/c materials can map to multiple sources

    def copy(self) -> ComposedURDFNameMap:
        new_name_map_lookup = {urdf_obj: copy.deepcopy(map) for urdf_obj, map in self.name_map_lookup.items()}
        new_name_to_urdf_and_og_name = copy.copy(self.name_to_urdf_and_og_name)
        return ComposedURDFNameMap(new_name_map_lookup, new_name_to_urdf_and_og_name)

    @staticmethod
    def construct(explicit_urdf: URDFObj) -> ComposedURDFNameMap:
        names = all_names(explicit_urdf)
        base_name_map = {name: name for name in names}
        name_map_lookup = {explicit_urdf: base_name_map}
        name_to_urdf_and_og_name = {name: (explicit_urdf, name) for name in names}
        return ComposedURDFNameMap(
            name_map_lookup=name_map_lookup,
            name_to_urdf_and_og_name=name_to_urdf_and_og_name,
        )

    def incorporate(self, other_map: Self) -> None:
        overlapping_names = set(self.name_to_urdf_and_og_name.keys()).intersection(
            other_map.name_to_urdf_and_og_name.keys()
        )
        # The below assertion should not be able to be fired b/c it implies that
        #   a composition happened with name overlaps
        assert (
            len(overlapping_names) == 0
        ), f"Got invalid overlap in ComposedURDFNameMap.incorporate: {overlapping_names = }"
        overlapping_explicit_urdfs = set(self.name_map_lookup.keys()).intersection(other_map.name_map_lookup.keys())
        # This assertion CAN FIRE--need to fix
        assert (
            len(overlapping_explicit_urdfs) == 0
        ), f"Got invalid overlap in ComposedURDFNameMap.incorporate: {overlapping_explicit_urdfs = }"

        self.name_map_lookup.update(other_map.name_map_lookup)
        self.name_to_urdf_and_og_name.update(other_map.name_to_urdf_and_og_name)

    def rename(self, name: str, new_name: str) -> None:
        explicit_urdf, og_name = self.name_to_urdf_and_og_name[name]
        self.name_map_lookup[explicit_urdf][og_name] = new_name
        self.name_to_urdf_and_og_name[new_name] = (explicit_urdf, og_name)
        del self.name_to_urdf_and_og_name[name]

    def remove(self, name: str) -> None:
        explicit_urdf, og_name = self.name_to_urdf_and_og_name[name]
        del self.name_to_urdf_and_og_name[name]
        name_map = self.name_map_lookup[explicit_urdf]
        del name_map[og_name]

    def lookup(self, urdf: URDFObj, name: str) -> str | None:
        """
        Lookup in the composed urdf the name of component from "urdf" that
          has the name "name" in "urdf"
        Returns None if it doesn't exist
        """

        if find_element_named(urdf, element=None, name=name) is None:
            return None
        else:
            return self.name_map_lookup[urdf][name]

    def _transform(self, transform_name_map: dict[str, str]) -> ComposedURDFNameMap:
        # Update all the new names with the transform_name_map

        def lookup_name(name: str) -> str:
            # Note: we have to do this defaulting b/c we erase materials
            # There is certainly a better way to do it which I will get around to
            #   at some point
            return transform_name_map[name] if name in transform_name_map else name

        new_name_map_lookup = {
            urdf: {og_name: lookup_name(new_name) for og_name, new_name in name_map.items()}
            for urdf, name_map in self.name_map_lookup.items()
        }
        new_name_to_urdf_and_og_name = {
            lookup_name(new_name): value for new_name, value in self.name_to_urdf_and_og_name.items()
        }
        return ComposedURDFNameMap(
            name_map_lookup=new_name_map_lookup,
            name_to_urdf_and_og_name=new_name_to_urdf_and_og_name,
        )

    def _collapse(
        self, primitive_urdfs: set[URDFObj], assert_no_others: bool
    ) -> ComposedURDFNameMap | UnaccountedForURDFError | RepeatedURDFError:
        # primitive_urdfs will be the keys of the dictionary onice collapsed
        compose_obj_to_collaped_name_maps = dict[ComposedURDFObj, ComposedURDFNameMap]()

        new_name_map_lookup = dict[URDFObj, dict[str, str]]()
        for explict_urdf, base_name_map in self.name_map_lookup.items():
            if explict_urdf in primitive_urdfs:
                # If we are looking for this explicit urdf, add it to the new name map lookup
                if explict_urdf in new_name_map_lookup:
                    # If we've already seen it, return RepeatedURDFError
                    return RepeatedURDFError(explict_urdf)
                new_name_map_lookup[explict_urdf] = base_name_map.copy()
            elif isinstance(explict_urdf, ComposedURDFObj):
                # Collapse given composed urdf with same primitive urdfs
                collapse_result = explict_urdf.name_map._collapse(primitive_urdfs, assert_no_others)
                if not isinstance(collapse_result, ComposedURDFNameMap):
                    # Collapse failed
                    return collapse_result

                overlapping_explicit_urdfs = set(new_name_map_lookup.keys()).intersection(
                    collapse_result.name_map_lookup.keys()
                )
                if len(overlapping_explicit_urdfs) != 0:
                    return RepeatedURDFError(list(overlapping_explicit_urdfs)[0])
                new_result = collapse_result._transform(base_name_map)

                compose_obj_to_collaped_name_maps[explict_urdf] = new_result

                new_name_map_lookup.update(new_result.name_map_lookup)
            elif assert_no_others:
                return UnaccountedForURDFError(explict_urdf)

        new_name_to_urdf_and_og_name = dict[str, tuple[URDFObj, str]]()
        for name, (urdf, og_name) in self.name_to_urdf_and_og_name.items():
            if urdf not in compose_obj_to_collaped_name_maps:
                new_name_to_urdf_and_og_name[name] = (urdf, og_name)
            else:
                assert isinstance(urdf, ComposedURDFObj), f"Internal urdf_compose_error. Debugging info: {urdf = }"
                new_name_to_urdf_and_og_name.update(compose_obj_to_collaped_name_maps[urdf].name_to_urdf_and_og_name)

        return ComposedURDFNameMap(new_name_map_lookup, new_name_to_urdf_and_og_name)

    def collapse_safe(self, primitive_urdfs: set[URDFObj]) -> ComposedURDFNameMap | RepeatedURDFError:
        """
        Collapse this name map into one who's keys use "primitive_urdfs"
        """
        collapse_result = self._collapse(primitive_urdfs, False)
        if isinstance(collapse_result, UnaccountedForURDFError):
            raise InteranlURDFComposeError("collapse with assert_no_others=False returned UnaccountedForURDFError")
        return collapse_result

    def collapse_strict_safe(
        self, primitive_urdfs: set[URDFObj]
    ) -> ComposedURDFNameMap | UnaccountedForURDFError | RepeatedURDFError:
        """
        like collapse but if this set of urdfs doesn't acount for all of the names in this map,
        it will return "UnaccountedForURDFError" which will have as an attribute the urdf
        that the given primitive_urdfs don't account for
        """
        return self._collapse(primitive_urdfs, True)

    def collapse(self, primitive_urdfs: set[URDFObj]) -> ComposedURDFNameMap:
        collapse_result = self.collapse_safe(primitive_urdfs)
        if not isinstance(collapse_result, ComposedURDFNameMap):
            raise collapse_result
        return collapse_result

    def collapse_strict(self, primitive_urdfs: set[URDFObj]) -> ComposedURDFNameMap:
        collapse_result = self.collapse_strict_safe(primitive_urdfs)
        if not isinstance(collapse_result, ComposedURDFNameMap):
            raise collapse_result
        return collapse_result

    def __repr__(self) -> str:
        return (
            f"ComposedURDFNameMap: \n\nname_map_lookup = {repr(self.name_map_lookup)} \n\n"
            f"name_to_urdf_and_og_name = {repr(self.name_to_urdf_and_og_name)}"
        )


class ComposedURDFObj(URDFObj):
    """
    A urdf object created through composition
    """

    def __init__(self, tree: ET.ElementTree, name_map: ComposedURDFNameMap):
        super().__init__(tree)
        self.name_map = name_map

    @staticmethod
    def construct(explicit_urdf: URDFObj) -> ComposedURDFObj:
        tree = copy.deepcopy(explicit_urdf.tree)
        name_map = ComposedURDFNameMap.construct(explicit_urdf)
        return ComposedURDFObj(tree, name_map)

    def rename_elements(self, name_map: dict[str, str]) -> None:
        name_dict = frozenset([NAME_KEY, "link"])

        for name, new_name in name_map.items():
            self.name_map.rename(name, new_name)

        def rename_element(el: ET.Element) -> None:
            if has_name(el, name_dict) and (name := get_name(el, name_dict)) in name_map:
                new_name = name_map[name]
                set_name(el, new_name, name_dict)

            for el_ in el:
                rename_element(el_)

        rename_element(self.getroot())

    def outlaw_duplicates_with(self, base_urdf: URDFObj) -> None:
        outlawed_names = all_names(base_urdf)
        outlawed_new_names = all_names(self)
        name_map = dict()
        # set up name map, and change names of top levels
        for i in self.getroot():
            if name := get_name(i):
                name_map[name] = first_available(outlawed_names, outlawed_new_names, name)
                outlawed_names.add(name_map[name])

        self.rename_elements(name_map)

    def remove_duplicate_materials(self, base_urdf: URDFObj) -> None:
        for el in base_urdf.getroot().findall("material"):
            for extend_el in self.getroot().findall("material"):
                if xml.el_equal(el, extend_el):
                    self.getroot().remove(extend_el)
                    name = get_name(extend_el)
                    if name is not None:
                        self.name_map.remove(name)

    def copy(self) -> ComposedURDFObj:
        return ComposedURDFObj(copy.deepcopy(self.tree), self.name_map.copy())

    def concatenate(self, obj: Self) -> None:
        obj_copy = obj.copy()
        obj_copy.outlaw_duplicates_with(self)
        self.name_map.incorporate(obj_copy.name_map)
        for el in obj_copy.getroot():
            self.getroot().append(el)


def first_available(outlawed_names: set[str], outlawed_new_names: set[str], name: str) -> str:
    def make_name(name: str, to_add: int) -> str:
        if to_add == 0:
            return name
        else:
            return name + "(" + str(to_add) + ")"

    to_add = 0
    while make_name(name, to_add) in outlawed_names or (to_add > 0 and make_name(name, to_add) in outlawed_new_names):
        to_add += 1
    return make_name(name, to_add)


def first_available_from_urdf(urdf: URDFObj, name: str) -> str:
    return first_available(all_names(urdf), set(), name)


@dataclass
class URDFConn:
    """
    An explicit urdf connection
    """

    base_link: str | None = None
    extender_link: str | None = None
