from __future__ import annotations

from functools import partial

import gdsfactory as gf
from gdsfactory import cell
from gdsfactory.component import Component
from gdsfactory.port import Port
from gdsfactory.typings import CrossSectionSpec, LayerSpec


@cell
def taper(
    length: float = 10.0,
    width1: float = 0.5,
    width2: float | None = None,
    port: Port | None = None,
    with_two_ports: bool = True,
    cross_section: CrossSectionSpec = "strip",
    port_names: tuple[str, str] = ("o1", "o2"),
    port_types: tuple[str, str] = ("optical", "optical"),
    with_bbox: bool = True,
    **kwargs,
) -> Component:
    """Linear taper, which tapers only the main cross section section.

    Args:
        length: taper length.
        width1: width of the west/left port.
        width2: width of the east/right port. Defaults to width1.
        port: can taper from a port instead of defining width1.
        with_two_ports: includes a second port.
            False for terminator and edge coupler fiber interface.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
        port_names: input and output port names. Second name only used if with_two_ports.
        port_types: input and output port types. Second type only used if with_two_ports.
        with_bbox: box in bbox_layers and bbox_offsets to avoid DRC sharp edges.
        kwargs: cross_section settings.
    """
    if len(port_types) != 2:
        raise ValueError("port_types should have two elements")

    x1 = gf.get_cross_section(cross_section, width=width1, **kwargs)
    if width2:
        width2 = gf.snap.snap_to_grid2x(width2)
        x2 = gf.get_cross_section(cross_section, width=width2, **kwargs)
    else:
        x2 = x1

    width1 = x1.width
    width2 = x2.width
    width_max = max([width1, width2])
    x = gf.get_cross_section(cross_section, width=width_max, **kwargs)
    layer = x.layer

    if isinstance(port, gf.Port) and width1 is None:
        width1 = port.width

    width2 = width2 or width1
    c = gf.Component()
    y1 = width1 / 2
    y2 = width2 / 2

    if length:
        p1 = gf.kdb.DPolygon([(0, y1), (length, y2), (length, -y2), (0, -y1)])
        c.add_polygon(p1, layer=layer)

        s0_width = x.sections[0].width

        for section in x.sections[1:]:
            delta_width = abs(section.width - s0_width)
            y1 = (width1 + delta_width) / 2
            y2 = (width2 + delta_width) / 2
            p1 = gf.kdb.DPolygon([(0, y1), (length, y2), (length, -y2), (0, -y1)])
            c.add_polygon(p1, layer=section.layer)

    if with_bbox:
        x.add_bbox(c)
    c.add_port(
        name=port_names[0],
        center=(0, 0),
        width=width1,
        orientation=180,
        layer=x.layer,
        cross_section=x1,
        port_type=port_types[0],
    )
    if with_two_ports:
        c.add_port(
            name=port_names[1],
            center=(length, 0),
            width=width2,
            orientation=0,
            layer=x.layer,
            cross_section=x2,
            port_type=port_types[1],
        )

    c.info["length"] = length
    c.info["width1"] = float(width1)
    c.info["width2"] = float(width2)
    return c


@gf.cell
def taper_strip_to_ridge(
    length: float = 10.0,
    width1: float = 0.5,
    width2: float = 0.5,
    w_slab1: float = 0.15,
    w_slab2: float = 6.0,
    layer_wg: LayerSpec = "WG",
    layer_slab: LayerSpec = "SLAB90",
    cross_section: CrossSectionSpec = "strip",
    use_slab_port: bool = False,
    **kwargs,
) -> Component:
    r"""Linear taper from strip to rib.

    Args:
        length: taper length (um).
        width1: in um.
        width2: in um.
        w_slab1: slab width in um.
        w_slab2: slab width in um.
        layer_wg: for input waveguide.
        layer_slab: for output waveguide with slab.
        cross_section: for input waveguide.
        use_slab_port: if True adds a second port for the slab.
        kwargs: cross_section settings.

    .. code::

                      __________________________
                     /           |
             _______/____________|______________
                   /             |
       width1     |w_slab1       | w_slab2  width2
             ______\_____________|______________
                    \            |
                     \__________________________

    """
    xs = gf.get_cross_section(cross_section, **kwargs)

    taper_wg = taper(
        length=length,
        width1=width1,
        width2=width2,
        cross_section=cross_section,
        layer=layer_wg,
    )
    taper_slab = taper(
        length=length,
        width1=w_slab1,
        width2=w_slab2,
        cross_section=cross_section,
        with_bbox=False,
        layer=layer_slab,
    )

    c = gf.Component()
    taper_ref_wg = c << taper_wg
    taper_ref_slab = c << taper_slab

    c.info["length"] = length
    c.add_port(name="o1", port=taper_ref_wg.ports["o1"])
    if use_slab_port:
        c.add_port(name="o2", port=taper_ref_slab.ports["o2"])
    else:
        c.add_port(name="o2", port=taper_ref_wg.ports["o2"])

    if length:
        xs.add_bbox(c)
    c.flatten()
    return c


@gf.cell
def taper_strip_to_ridge_trenches(
    length: float = 10.0,
    width: float = 0.5,
    slab_offset: float = 3.0,
    trench_width: float = 2.0,
    trench_layer: LayerSpec = "DEEP_ETCH",
    layer_wg: LayerSpec = "WG",
    trench_offset: float = 0.1,
) -> gf.Component:
    """Defines taper using trenches to define the etch.

    Args:
        length: in um.
        width: in um.
        slab_offset: in um.
        trench_width: in um.
        trench_layer: trench layer.
        layer_wg: waveguide layer.
        trench_offset: after waveguide in um.
    """
    c = gf.Component()
    y0 = width / 2 + trench_width - trench_offset
    yL = width / 2 + trench_width - trench_offset + slab_offset

    # straight
    x = [0, length, length, 0]
    yw = [y0, yL, -yL, -y0]
    c.add_polygon(list(zip(x, yw)), layer=layer_wg)

    # top trench
    ymin0 = width / 2
    yminL = width / 2
    ymax0 = width / 2 + trench_width
    ymaxL = width / 2 + trench_width + slab_offset
    x = [0, length, length, 0]
    ytt = [ymin0, yminL, ymaxL, ymax0]
    ytb = [-ymin0, -yminL, -ymaxL, -ymax0]
    c.add_polygon(list(zip(x, ytt)), layer=trench_layer)
    c.add_polygon(list(zip(x, ytb)), layer=trench_layer)

    c.add_port(name="o1", center=(0, 0), width=width, orientation=180, layer=layer_wg)
    c.add_port(
        name="o2", center=(length, 0), width=width, orientation=0, layer=layer_wg
    )
    return c


taper_strip_to_slab150 = partial(taper_strip_to_ridge, layer_slab="SLAB150")


@gf.cell
def taper_sc_nc(
    width1=0.5,
    width2=1,
    length=20,
    layer_wg="WG",
    layer_nitride="WGN",
    width_tip_nitride=0.15,
    width_tip_silicon=0.15,
    cross_section: CrossSectionSpec = "strip",
    **kwargs,
) -> Component:
    """Taper from strip to nitride.

    Args:
        width1: strip width.
        width2: nitride width.
        length: taper length.
        layer_wg: strip layer.
        layer_nitride: nitride layer.
        width_tip_nitride: tip width for nitride.
        width_tip_silicon: tip width for strip.
        cross_section: cross_section specification.
        kwargs: cross_section settings.
    """
    return taper_strip_to_ridge(
        layer_wg=layer_wg,
        layer_slab=layer_nitride,
        length=length,
        width1=width1,
        width2=width_tip_nitride,
        w_slab1=width_tip_silicon,
        w_slab2=width2,
        use_slab_port=True,
        cross_section=cross_section,
        **kwargs,
    )


def taper_nc_sc(width1=1, width2=0.5, length=20, **kwargs) -> Component:
    return taper_sc_nc(width2=width1, width1=width2, length=length, **kwargs)


taper_electrical = partial(
    taper,
    port_types=("electrical", "electrical"),
    port_names=("e1", "e2"),
    cross_section="metal_routing",
)


if __name__ == "__main__":
    c = gf.grid([taper_nc_sc(), taper_sc_nc()])
    # c = taper(cross_section="rib", width2=5, port_types="optical")
    # c = taper_strip_to_ridge_trenches()
    # c = taper_strip_to_ridge()
    # c = taper(width1=1.5, width2=1, cross_section="rib")
    # c = taper_sc_nc()
    # c = taper(cross_section="rib")
    # c = taper(length=1, width1=0.54, width2=10, cross_section="strip")
    # c = taper_strip_to_ridge()
    # c = taper(width1=0.5, width2=10, length=20)
    # c = taper_sc_nc()
    # c.pprint_ports()
    c.show()
