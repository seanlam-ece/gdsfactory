from __future__ import annotations

from functools import partial

from numpy import float64

from gdsfactory import cell
from gdsfactory.component import Component
from gdsfactory.components.bend_circular import bend_circular, bend_circular180
from gdsfactory.components.bend_euler import bend_euler, bend_euler180
from gdsfactory.components.component_sequence import component_sequence
from gdsfactory.components.straight import straight as straight_function
from gdsfactory.typings import ComponentSpec


def _get_bend_size(bend90: Component) -> float64:
    p1, p2 = list(bend90.ports)[:2]
    bsx = abs(p2.dx - p1.dx)
    bsy = abs(p2.dy - p1.dy)
    return max(bsx, bsy)


@cell
def cutback_bend(
    component: ComponentSpec = bend_euler,
    straight: ComponentSpec = straight_function,
    straight_length: float = 5.0,
    rows: int = 6,
    cols: int = 5,
    **kwargs,
) -> Component:
    """Deprecated.

    Use cutback_bend90 instead with smaller footprint.

    Args:
        component: bend spec.
        straight: straight spec.
        straight_length: in um.
        rows: number of rows.
        cols: number of cols.
        kwargs: cross_section settings.

    .. code::

        this is a column
            _
          _|
        _|

        _ this is a row
    """
    from gdsfactory.pdk import get_component

    bend90 = get_component(component, **kwargs)
    straightx = straight(length=straight_length, **kwargs)

    # Define a map between symbols and (component, input port, output port)
    symbol_to_component = {
        "A": (bend90, "o1", "o2"),
        "B": (bend90, "o2", "o1"),
        "S": (straightx, "o1", "o2"),
    }

    # Generate the sequence of staircases
    s = ""
    for i in range(cols):
        s += "ASBS" * rows
        s += "ASAS" if i % 2 == 0 else "BSBS"
    s = s[:-4]

    c = component_sequence(
        sequence=s, symbol_to_component=symbol_to_component, start_orientation=90
    )
    c.info["n_bends"] = rows * cols * 2 + cols * 2 - 2
    return c


@cell
def cutback_bend90(
    component: ComponentSpec = bend_euler,
    straight: ComponentSpec = straight_function,
    straight_length: float = 5.0,
    rows: int = 6,
    cols: int = 6,
    spacing: int = 5,
    **kwargs,
) -> Component:
    """Returns bend90 cutback.

    Args:
        component: bend spec.
        straight: straight spec.
        straight_length: in um.
        rows: number of rows.
        cols: number of cols.
        spacing: in um.
        kwargs: cross_section settings.

    .. code::

           _
        |_| |
    """
    from gdsfactory.pdk import get_component

    bend90 = get_component(component, **kwargs)
    straightx = straight(length=straight_length, **kwargs)
    straight_length = 2 * _get_bend_size(bend90) + spacing + straight_length
    straighty = straight(length=straight_length, **kwargs)

    # Define a map between symbols and (component, input port, output port)
    symbol_to_component = {
        "A": (bend90, "o1", "o2"),
        "B": (bend90, "o2", "o1"),
        "-": (straightx, "o1", "o2"),
        "|": (straighty, "o1", "o2"),
    }

    # Generate the sequence of staircases
    s = "".join(
        "A-A-B-B-" * rows + "|" if i % 2 == 0 else "B-B-A-A-" * rows + "|"
        for i in range(cols)
    )
    s = s[:-1]

    # Create the component from the sequence
    c = component_sequence(
        sequence=s, symbol_to_component=symbol_to_component, start_orientation=0
    )
    c.info["n_bends"] = rows * cols * 4
    return c


@cell
def staircase(
    component: ComponentSpec = bend_euler,
    straight: ComponentSpec = straight_function,
    length_v: float = 5.0,
    length_h: float = 5.0,
    rows: int = 4,
    **kwargs,
) -> Component:
    """Returns staircase.

    Args:
        component: bend spec.
        straight: straight spec.
        length_v: vertical length.
        length_h: vertical length.
        rows: number of rows.
        cols: number of cols.
        kwargs: cross_section settings.
    """
    bend90 = component(**kwargs) if callable(component) else component

    wgh = straight(length=length_h, **kwargs)
    wgv = straight(length=length_v, **kwargs)

    # Define a map between symbols and (component, input port, output port)
    symbol_to_component = {
        "A": (bend90, "o1", "o2"),
        "B": (bend90, "o2", "o1"),
        "-": (wgh, "o1", "o2"),
        "|": (wgv, "o1", "o2"),
    }

    # Generate the sequence of staircases
    s = "-A|B" * rows + "-"

    c = component_sequence(
        sequence=s, symbol_to_component=symbol_to_component, start_orientation=0
    )
    c.info["n_bends"] = 2 * rows
    return c


@cell
def cutback_bend180(
    component: ComponentSpec = bend_euler180,
    straight: ComponentSpec = straight_function,
    straight_length: float = 5.0,
    rows: int = 6,
    cols: int = 6,
    spacing: float = 3.0,
    **kwargs,
) -> Component:
    """Returns cutback to measure u bend loss.

    Args:
        component: bend spec.
        straight: straight spec.
        straight_length: in um.
        rows: number of rows.
        cols: number of cols.
        spacing: in um.
        kwargs: cross_section settings.

    .. code::

          _
        _| |_  this is a row

        _ this is a column
    """
    from gdsfactory.pdk import get_component

    bend180 = get_component(component, **kwargs)
    straightx = straight(length=straight_length, **kwargs)
    wg_vertical = straight(
        length=2 * bend180.dxsize + straight_length + spacing,
        **kwargs,
    )

    # Define a map between symbols and (component, input port, output port)
    symbol_to_component = {
        "D": (bend180, "o1", "o2"),
        "C": (bend180, "o2", "o1"),
        "-": (straightx, "o1", "o2"),
        "|": (wg_vertical, "o1", "o2"),
    }

    # Generate the sequence of staircases
    s = "".join(
        "D-C-" * rows + "|" if i % 2 == 0 else "C-D-" * rows + "|" for i in range(cols)
    )

    s = s[:-1]

    c = component_sequence(
        sequence=s, symbol_to_component=symbol_to_component, start_orientation=0
    )
    c.info["n_bends"] = rows * cols * 2 + cols * 2 - 2
    return c


cutback_bend180circular = partial(cutback_bend180, component=bend_circular180)
cutback_bend90circular = partial(cutback_bend90, component=bend_circular)

if __name__ == "__main__":
    # c = cutback_bend()
    # c = cutback_bend90()
    c = cutback_bend90circular(rows=7, cols=4, radius=5)
    # c = cutback_bend_circular(rows=14, cols=4)
    # c = cutback_bend90()
    # c = cutback_bend180(rows=3, cols=1)
    # c = cutback_bend(rows=3, cols=2)
    # c = cutback_bend90(rows=3, cols=2)
    # c = cutback_bend180(rows=2, cols=2)
    # c = cutback_bend(rows=3, cols=2)
    c.show()
