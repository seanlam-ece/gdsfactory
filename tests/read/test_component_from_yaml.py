from __future__ import annotations

import numpy as np
import pytest
from pytest_regressions.data_regression import DataRegressionFixture

from gdsfactory.difftest import difftest
from gdsfactory.read.from_yaml import from_yaml, sample_doe_function, sample_mmis

sample_connections = """
name: sample_connections

instances:
    wgw:
      component: straight
      settings:
        length: 1
    wgn:
      component: straight
      settings:
        length: 0.5

connections:
    wgw,o1: wgn,o2

"""

#
#        __Lx__
#       |      |
#       Ly     Lyr
#       |      |
#  CP1==|      |==CP2
#       |      |
#       Ly     Lyr
#       |      |
#      DL/2   DL/2
#       |      |
#       |__Lx__|
#


sample_mirror_simple = """
name: sample_mirror_simple

instances:
    s:
        component: straight

    b:
        component: bend_circular

placements:
    b:
        mirror: True
        port: o1

connections:
    b,o1: s,o2

"""


def test_sample() -> None:
    c = from_yaml(sample_mmis)
    assert len(c.insts) == 6, len(c.insts)
    assert len(c.ports) == 3, len(c.ports)
    c.delete()


def test_connections() -> None:
    c = from_yaml(sample_connections)
    assert len(c.insts) == 2
    assert len(c.ports) == 0
    c.delete()


sample_2x2_connections = """
name: connections_2x2_solution

instances:
    mmi_bottom:
      component: mmi2x2
      settings:
            length_mmi: 5
    mmi_top:
      component: mmi2x2
      settings:
            length_mmi: 10

placements:
    mmi_top:
        x: 100
        y: 100

routes:
    optical:
        links:
            mmi_bottom,o4: mmi_top,o1
            mmi_bottom,o3: mmi_top,o2

        settings:
            cross_section:
                cross_section: strip

"""


def test_connections_2x2() -> None:
    c = from_yaml(sample_2x2_connections)
    assert len(c.insts) == 11, len(c.insts)
    assert len(c.ports) == 0, len(c.ports)

    length = c.routes["optical-mmi_bottom,o3-mmi_top,o2"].length
    assert np.isclose(length, 135000), length
    c.delete()


sample_different_factory = """
name: sample_different_factory

instances:
    bl:
      component: pad
    tl:
      component: pad
    br:
      component: pad
    tr:
      component: pad

placements:
    tl:
        x: 0
        y: 200

    br:
        x: 400
        y: 400

    tr:
        x: 400
        y: 600

routes:
    electrical:
        settings:
            port_type: electrical
            separation: 20
            cross_section:
                cross_section: metal3
                settings:
                    width: 10
        links:
            tl,e3: tr,e1
            bl,e3: br,e1
"""


def test_connections_different_factory() -> None:
    c = from_yaml(sample_different_factory)
    lengths = [660000] * 2 + [700000]
    assert c.routes["electrical-tl,e3-tr,e1"].length == lengths[0], c.routes[
        "electrical-tl,e3-tr,e1"
    ].length
    assert c.routes["electrical-bl,e3-br,e1"].length == lengths[1], c.routes[
        "electrical-bl,e3-br,e1"
    ].length


sample_different_link_factory = """
name: sample_path_length_matching

instances:
    bl:
      component: pad
    tl:
      component: pad
    br:
      component: pad
    tr:
      component: pad

placements:
    tl:
        x: 0
        y: 200

    br:
        x: 900
        y: 400

    tr:
        x: 900
        y: 600

routes:
    route1:
        routing_strategy: route_bundle_path_length_match
        settings:
            radius: 10
            extra_length: 500
        links:
            tl,e3: tr,e1
            bl,e3: br,e1

"""


sample_waypoints = """
name: sample_waypoints

instances:
    t:
      component: pad_array
      settings:
          orientation: 270
    b:
      component: pad_array
      settings:
          orientation: 90

placements:
    t:
        x: -250
        y: 1000
routes:
    route1:
        routing_strategy: route_bundle_from_waypoints
        settings:
            waypoints:
                - [0, 300]
                - [400, 300]
                - [400, 400]
                - [-250, 400]
            auto_widen: False
        links:
            b,e11: t,e11
            b,e12: t,e12
"""


sample_docstring = """
name: sample_docstring

instances:
    mmi_bot:
      component: mmi1x2
      settings:
        width_mmi: 5
        length_mmi: 11
    mmi_top:
      component: mmi1x2
      settings:
        width_mmi: 6
        length_mmi: 22

placements:
    mmi_top:
        port: o1
        x: 0
        y: 0
    mmi_bot:
        port: o1
        x: mmi_top,o2
        y: mmi_top,o2
        dx: 40
        dy: -40
routes:
    optical:
        links:
            mmi_top,o3: mmi_bot,o1
"""


sample_regex_connections = """
name: sample_regex_connections

instances:
    left:
      component: nxn
      settings:
        west: 0
        east: 3
        ysize: 20
    right:
      component: nxn
      settings:
        west: 3
        east: 0
        ysize: 20

placements:
    right:
        x: 20
routes:
    optical:
        links:
            left,o:1:3: right,o:3:1
"""

sample_regex_connections_backwards = """
name: sample_regex_connections_backwards

instances:
    left:
      component: nxn
      settings:
        west: 0
        east: 3
        ysize: 20
    right:
      component: nxn
      settings:
        west: 3
        east: 0
        ysize: 20

placements:
    right:
        x: 20
routes:
    optical:
        links:
            left,o:3:1: right,o:1:3
"""


def test_connections_regex() -> None:
    c = from_yaml(sample_regex_connections)
    route_names = [
        "optical-left,o1-right,o3",
        "optical-left,o2-right,o2",
        "optical-left,o3-right,o1",
    ]

    length = 12000
    for route_name in route_names:
        assert np.isclose(c.routes[route_name].length, length)


def test_connections_regex_backwards() -> None:
    c = from_yaml(sample_regex_connections_backwards)
    route_names = [
        "optical-left,o3-right,o1",
        "optical-left,o2-right,o2",
        "optical-left,o1-right,o3",
    ]

    length = 12000
    for route_name in route_names:
        assert np.isclose(c.routes[route_name].length, length), c.routes[
            route_name
        ].length


@pytest.mark.skip("not implemented")
def test_connections_waypoints() -> None:
    c = from_yaml(sample_waypoints)

    length = 2036548
    route_name = "optical-b,e11-t,e11"
    assert np.isclose(c.routes[route_name].length, length), c.routes[route_name].length


def test_docstring_sample() -> None:
    c = from_yaml(sample_docstring)
    route_name = "optical-mmi_top,o3-mmi_bot,o1"
    length = 38750
    assert np.isclose(c.routes[route_name].length, length), c.routes[route_name].length
    c.delete()


yaml_fail = """
name: yaml_fail
instances:
    mmi_long:
      component: mmi1x2
      settings:
        width_mmi: 4.5
        length_mmi: 10
    mmi_short:
      component: mmi1x2
      settings:
        width_mmi: 4.5
        length_mmi: 5

placements:
    mmi_short:
        port: o1
        x: mmi_long,o2
        y: mmi_long,o2
    mmi_long:
        port: o1
        x: mmi_short,o2
        y: mmi_short,o2
        dx : 10
        dy: 20
"""
#                      ______
#                     |      |
#           dx   1----| short|
#                |    |______|
#                | dy
#   ______ north |
#   |     |
#   |long |
#   |_____|
#       east

yaml_anchor = """
name: yaml_anchor
instances:
    mmi_long:
      component: mmi1x2
      settings:
        width_mmi: 4.5
        length_mmi: 10
    mmi_short:
      component: mmi1x2
      settings:
        width_mmi: 4.5
        length_mmi: 5

placements:
    mmi_short:
        port: o3
        x: 0
        y: 0
    mmi_long:
        port: o1
        x: mmi_short,east
        y: mmi_short,north
        dx : 10
        dy: 10
"""

sample_doe = """
name: mask

instances:
    mmi1x2_sweep:
       component: pack_doe
       settings:
         doe: mmi1x2
         do_permutations: True
         spacing: 100
         settings:
           length_mmi: [2, 100]
           width_mmi: [4, 10]
"""

sample_doe_grid = """
name: mask_grid

instances:
    mmi1x2_sweep:
       component: pack_doe_grid
       settings:
         doe: mmi1x2
         do_permutations: True
         spacing: [100, 100]
         shape: [2, 2]
         settings:
           length_mmi: [2, 100]
           width_mmi: [4, 10]
"""

sample_rotation = """
name: sample_rotation

instances:
  r1:
    component: rectangle
    settings:
        size: [4, 2]
  r2:
    component: rectangle
    settings:
        size: [2, 4]

placements:
    r1:
        xmin: 0
        ymin: 0
    r2:
        rotation: -90
        xmin: r1,east
        ymin: 0

"""

sample_array2 = """
name: sample_array2
instances:
  s:
    component: splitter_tree
    settings:
      coupler: mmi1x2
      noutputs: 8
      spacing:
      - 50
      - 50
      bend_s: bend_s
      cross_section: strip
    na: 1
    nb: 1
    dax: 0
    day: 0
    dbx: 0
    dby: 0
  dbr:
    component: array
    settings:
      component: dbr
      spacing:
      - 0
      - 3
      columns: 1
      rows: 8
      add_ports: true
      centered: true
    na: 1
    nb: 1
    dax: 0
    day: 0
    dbx: 0
    dby: 0
placements:
  s:
    x: 0.0
    'y': 0.0
    dx: 0
    dy: 0
    rotation: 0
    mirror: false
  dbr:
    x: 300.0
    'y': 0.0
    dx: 0
    dy: 0
    rotation: 0
    mirror: false
connections: {}
routes:
  splitter_to_dbr:
    links:
      s,o2_2_1: dbr,o1_1_1
      s,o2_2_2: dbr,o1_2_1
      s,o2_2_3: dbr,o1_3_1
      s,o2_2_4: dbr,o1_4_1
      s,o2_2_5: dbr,o1_5_1
      s,o2_2_6: dbr,o1_6_1
      s,o2_2_7: dbr,o1_7_1
      s,o2_2_8: dbr,o1_8_1
    settings:
      radius: 5
      sort_ports: true
    routing_strategy: route_bundle
"""

sample_array = """
name: sample_array

instances:
  sa1:
    component: straight
    na: 5
    dax: 50
    nb: 4
    dby: 10
  s2:
    component: straight

connections:
    s2,o2: sa1<2.3>,o1

routes:
    b1:
        links:
            sa1<3.0>,o2: sa1<4.0>,o1
            sa1<3.1>,o2: sa1<4.1>,o1

ports:
    o1: s2,o1
    o2: sa1<0.0>,o1
"""

# FIXME: Fix both uncommented cases
# yaml_fail should actually fail
# sample_different_factory: returns a zero length straight that gives an error
# when extracting the netlist

yaml_strings = dict(
    yaml_anchor=yaml_anchor,
    # yaml_fail=yaml_fail,
    # sample_regex_connections_backwards=sample_regex_connections_backwards,
    # sample_regex_connections=sample_regex_connections,
    sample_docstring=sample_docstring,
    # sample_waypoints=sample_waypoints,
    # sample_different_link_factory=sample_different_link_factory,
    # sample_different_factory=sample_different_factory,
    sample_mirror_simple=sample_mirror_simple,
    sample_connections=sample_connections,
    sample_mmis=sample_mmis,
    sample_doe=sample_doe,
    # sample_doe_grid=sample_doe_grid,
    sample_doe_function=sample_doe_function,
    sample_rotation=sample_rotation,
    sample_array=sample_array,
    sample_array2=sample_array2,
)


@pytest.mark.parametrize("yaml_key", yaml_strings.keys())
def test_gds_and_settings(
    yaml_key: str, data_regression: DataRegressionFixture, check: bool = True
) -> None:
    """Avoid regressions in GDS geometry shapes and layers."""
    yaml_string = yaml_strings[yaml_key]
    c = from_yaml(yaml_string)
    difftest(c)

    if check:
        data_regression.check(c.to_dict())


# @pytest.mark.parametrize("yaml_key", yaml_strings.keys())
# def test_netlists(
#     yaml_key: str,
#     data_regression: DataRegressionFixture,
#     check: bool = True,
# ) -> None:
#     """Write netlists for hierarchical circuits. Checks that both netlists are
#     the same jsondiff does a hierarchical diff Component -> netlist ->
#     Component -> netlist.

#     Args:
#         yaml_key: to test.
#         data_regression: for regression test.
#         check: False, skips test.

#     """
#     yaml_string = yaml_strings[yaml_key]
#     c = from_yaml(yaml_string)
#     n = c.get_netlist()
#     if check:
#         data_regression.check(n)

#     yaml_str = OmegaConf.to_yaml(n, sort_keys=True)

#     # print(yaml_str)
#     c2 = from_yaml(yaml_str, name=c.name)
#     n2 = c2.get_netlist()
#     # pprint(d)
#     d = jsondiff.diff(n, n2)
#     assert len(d) == 0, pprint(d)


if __name__ == "__main__":
    # test_sample()
    test_connections_2x2()
    # test_connections_regex_backwards()
    # test_connections_different_factory()
    # import gdsfactory as gf

    # c = gf.read.from_yaml(sample_array2)
    # c.show()
