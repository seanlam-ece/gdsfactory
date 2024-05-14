"""You can define a path with a list of points combined with a cross-section.

A path can be extruded using any CrossSection returning a Component
The CrossSection defines the layer numbers, widths and offsets

Adapted from PHIDL https://github.com/amccaugh/phidl/ by Adam McCaughan
"""

from __future__ import annotations

import hashlib
import math
import warnings
from collections.abc import Callable, Iterable

import numpy as np
from numpy import mod, pi

from gdsfactory.cell import cell
from gdsfactory.component import Component
from gdsfactory.component_layout import (
    _GeometryHelper,
    _parse_move,
    _reflect_points,
    _rotate_points,
)
from gdsfactory.config import CONF
from gdsfactory.cross_section import CrossSection, Section, Transition
from gdsfactory.port import Port
from gdsfactory.typings import (
    ComponentSpec,
    Coordinates,
    CrossSectionSpec,
    Float2,
    LayerSpec,
    WidthTypes,
)


def _simplify(points, tolerance):
    import shapely.geometry as sg

    ls = sg.LineString(points)
    ls_simple = ls.simplify(tolerance=tolerance)
    return np.asarray(ls_simple.coords)


class Path(_GeometryHelper):
    """Path object for smooth Paths. You can extrude a Path with a CrossSection \
            to create a Component.

    Parameters:
        path: array-like[N][2], Path, or list of Paths. Points or Paths to append() initially.

    """

    def __init__(self, path=None) -> None:
        """Creates an empty path."""
        self.points = np.array([[0, 0]], dtype=np.float64)
        self.start_angle = 0
        self.end_angle = 0
        self.info = {}
        if path is not None:
            # If array[N][2]
            if (
                (np.asarray(path, dtype=object).ndim == 2)
                and np.issubdtype(np.array(path).dtype, np.number)
                and (np.shape(path)[1] == 2)
            ):
                self.points = np.array(path, dtype=np.float64)
                nx1, ny1 = self.points[1] - self.points[0]
                self.start_angle = np.arctan2(ny1, nx1) / np.pi * 180
                nx2, ny2 = self.points[-1] - self.points[-2]
                self.end_angle = np.arctan2(ny2, nx2) / np.pi * 180
            elif isinstance(path, Path):
                self.points = np.array(path.points, dtype=np.float64)
                self.start_angle = path.start_angle
                self.end_angle = path.end_angle
                self.info = {}
            elif np.asarray(path, dtype=object).size > 1:
                self.append(path)
            else:
                raise ValueError(
                    "Path() the `path` argument must be either blank, a path Object, "
                    "an array-like[N][2] list of points, or a list of these"
                )

    def __repr__(self) -> str:
        """Returns path points."""
        return (
            f"Path(start_angle={self.start_angle}, "
            f"end_angle={self.end_angle}, "
            f"points={self.points})"
        )

    def __len__(self) -> int:
        """Returns path points."""
        return len(self.points)

    def __iadd__(self, path_or_points) -> Path:
        """Adds points to current path."""
        return self.append(path_or_points)

    def __add__(self, path) -> Path:
        """Returns new path concatenating current and new path."""
        new = self.copy()
        return new.append(path)

    @property
    def bbox(self):
        """Returns the bounding box of the Path."""
        bbox = [
            (np.min(self.points[:, 0]), np.min(self.points[:, 1])),
            (np.max(self.points[:, 0]), np.max(self.points[:, 1])),
        ]
        return np.array(bbox)

    def append(self, path):
        """Attach Path to the end of this Path.

        The input path automatically rotates and translates such that it continues
        smoothly from the previous segment.

        Args:
            path: Path, array-like[N][2], or list of Paths. The input path that will be appended.
        """
        # If appending another Path, load relevant variables
        if isinstance(path, Path):
            start_angle = path.start_angle
            end_angle = path.end_angle
            points = path.points
        # If array[N][2]
        elif (
            (np.asarray(path, dtype=object).ndim == 2)
            and np.issubdtype(np.array(path).dtype, np.number)
            and (np.shape(path)[1] == 2)
        ):
            points = np.asfarray(path)
            nx1, ny1 = points[1] - points[0]
            start_angle = np.arctan2(ny1, nx1) / np.pi * 180
            nx2, ny2 = points[-1] - points[-2]
            end_angle = np.arctan2(ny2, nx2) / np.pi * 180
        # If list of Paths or arrays
        elif isinstance(path, list | tuple):
            for p in path:
                self.append(p)
            return self
        else:
            raise ValueError(
                "Path.append() the `path` argument must be either "
                "a Path object, an array-like[N][2] list of points, or a list of these"
            )

        # Connect beginning of new points with old points
        points = _rotate_points(points, angle=self.end_angle - start_angle)
        points += self.points[-1, :] - points[0, :]

        # Update end angle
        self.end_angle = mod(end_angle + self.end_angle - start_angle, 360)

        # Concatenate old points + new points
        self.points = np.vstack([self.points, points[1:]])

        return self

    def offset(self, offset: float | Callable[..., float] = 0):
        """Offsets Path so that it follows the Path centerline plus an offset.

        The offset can either be a fixed value, or a function
        of the form my_offset(t) where t goes from 0->1

        Args:
            offset: int or float, callable. Magnitude of the offset
        """
        if offset == 0:
            points = self.points
            start_angle = self.start_angle
            end_angle = self.end_angle
        elif callable(offset):
            # Compute lengths
            dx = np.diff(self.points[:, 0])
            dy = np.diff(self.points[:, 1])
            lengths = np.cumsum(np.sqrt((dx) ** 2 + (dy) ** 2))
            lengths = np.concatenate([[0], lengths])
            # Create list of offset points and perform offset
            points = self._centerpoint_offset_curve(
                self.points,
                offset_distance=offset(lengths / lengths[-1]),
                start_angle=self.start_angle,
                end_angle=self.end_angle,
            )
            # Numerically compute start and end angles
            tol = 1e-6
            ds = tol / lengths[-1]
            ny1 = offset(ds) - offset(0)
            start_angle = np.arctan2(-ny1, tol) / np.pi * 180 + self.start_angle
            # start_angle = np.round(start_angle, decimals=6)
            ny2 = offset(1) - offset(1 - ds)
            end_angle = np.arctan2(-ny2, tol) / np.pi * 180 + self.end_angle
            # end_angle = np.round(end_angle, decimals=6)
        else:  # Offset is just a number
            points = self._centerpoint_offset_curve(
                self.points,
                offset_distance=offset,
                start_angle=self.start_angle,
                end_angle=self.end_angle,
            )
            start_angle = self.start_angle
            end_angle = self.end_angle

        self.points = points
        self.start_angle = start_angle
        self.end_angle = end_angle
        return self

    def move(self, origin=(0, 0), destination=None, axis=None):
        """Moves the Path from the origin point to the destination.

        Both origin and destination can be 1x2 array-like or a Port.

        Args:
            origin : array-like[2], Port Origin point of the move.
            destination : array-like[2], Port Destination point of the move.
            axis : {'x', 'y'} Direction of move.

        """
        dx, dy = _parse_move(origin, destination, axis)
        self.points += np.array([dx, dy])

        return self

    def rotate(self, angle: float = 45, center: Float2 | None = (0, 0)):
        """Rotates all Polygons in the Component around the specified center point.

        If no center point specified will rotate around (0,0).

        Args:
            angle: Angle to rotate the Component in degrees.
            center: array-like[2] or None. component of the Component.
        """
        if angle == 0:
            return self
        self.points = _rotate_points(self.points, angle, center)
        if self.start_angle is not None:
            self.start_angle = mod(self.start_angle + angle, 360)
        if self.end_angle is not None:
            self.end_angle = mod(self.end_angle + angle, 360)
        return self

    def mirror(self, p1: Float2 = (0, 1), p2: Float2 = (0, 0)):
        """Mirrors the Path across the line formed between the two specified points.

        ``points`` may be input as either single points [1,2]
        or array-like[N][2], and will return in kind.

        Args:
            p1: First point of the line.
            p2: Second point of the line.
        """
        self.points = _reflect_points(self.points, p1, p2)
        angle = np.arctan2((p2[1] - p1[1]), (p2[0] - p1[0])) * 180 / pi
        if self.start_angle is not None:
            self.start_angle = mod(2 * angle - self.start_angle, 360)
        if self.end_angle is not None:
            self.end_angle = mod(2 * angle - self.end_angle, 360)
        return self

    def _centerpoint_offset_curve(
        self, points, offset_distance, start_angle, end_angle
    ):
        """Creates a offset curve (but does not account for cusps etc)\
        by computing the centerpoint offset of the supplied x and y points."""
        new_points = np.array(points, dtype=np.float64)
        dx = np.diff(points[:, 0])
        dy = np.diff(points[:, 1])
        theta = np.arctan2(dy, dx)
        theta = np.concatenate([theta[:1], theta, theta[-1:]])
        theta_mid = (np.pi + theta[1:] + theta[:-1]) / 2  # Mean angle between segments
        dtheta_int = np.pi + theta[:-1] - theta[1:]  # Internal angle between segments
        offset_distance = offset_distance / np.sin(dtheta_int / 2)
        new_points[:, 0] -= offset_distance * np.cos(theta_mid)
        new_points[:, 1] -= offset_distance * np.sin(theta_mid)
        if start_angle is not None:
            new_points[0, :] = points[0, :] + (
                np.sin(start_angle * np.pi / 180) * offset_distance[0],
                -np.cos(start_angle * np.pi / 180) * offset_distance[0],
            )
        if end_angle is not None:
            new_points[-1, :] = points[-1, :] + (
                np.sin(end_angle * np.pi / 180) * offset_distance[-1],
                -np.cos(end_angle * np.pi / 180) * offset_distance[-1],
            )
        return new_points

    def _parametric_offset_curve(self, points, offset_distance, start_angle, end_angle):
        """Creates a parametric offset (does not account for cusps etc) \
        by using gradient of the supplied x and y points."""
        x = points[:, 0]
        y = points[:, 1]
        dxdt = np.gradient(x)
        dydt = np.gradient(y)
        if start_angle is not None:
            dxdt[0] = np.cos(start_angle * np.pi / 180)
            dydt[0] = np.sin(start_angle * np.pi / 180)
        if end_angle is not None:
            dxdt[-1] = np.cos(end_angle * np.pi / 180)
            dydt[-1] = np.sin(end_angle * np.pi / 180)
        x_offset = x + offset_distance * dydt / np.sqrt(dxdt**2 + dydt**2)
        y_offset = y - offset_distance * dxdt / np.sqrt(dydt**2 + dxdt**2)
        return np.array([x_offset, y_offset]).T

    def length(self) -> float:
        """Return cumulative length."""
        x = self.points[:, 0]
        y = self.points[:, 1]
        dx = np.diff(x)
        dy = np.diff(y)
        return np.sum(np.sqrt((dx) ** 2 + (dy) ** 2))

    def curvature(self):
        """Calculates Path curvature.

        The curvature is numerically computed so areas where the curvature
        jumps instantaneously (such as between an arc and a straight segment)
        will be slightly interpolated, and sudden changes in point density
        along the curve can cause discontinuities.

        Returns:
            s: array-like[N] The arc-length of the Path
            K: array-like[N] The curvature of the Path
        """
        x = self.points[:, 0]
        y = self.points[:, 1]
        dx = np.diff(x)
        dy = np.diff(y)
        ds = np.sqrt((dx) ** 2 + (dy) ** 2)
        s = np.cumsum(ds)
        theta = np.arctan2(dy, dx)

        # Fix discontinuities arising from np.arctan2
        dtheta = np.diff(theta)
        dtheta[np.where(dtheta > np.pi)] += -2 * np.pi
        dtheta[np.where(dtheta < -np.pi)] += 2 * np.pi
        theta = np.concatenate([[0], np.cumsum(dtheta)]) + theta[0]

        K = np.gradient(theta, s, edge_order=2)
        return s, K

    def hash_geometry(self, precision: float = 1e-4) -> str:
        """Computes an SHA1 hash of the points in the Path and the start_angle and end_angle.

        Args:
            precision: Rounding precision for the the objects in the Component. For instance, \
                    a precision of 1e-2 will round a point at (0.124, 1.748) to (0.12, 1.75)

        Returns:
            str Hash result in the form of an SHA1 hex digest string.

        .. code::

            hash(
                hash(First layer information: [layer1, datatype1]),
                hash(Polygon 1 on layer 1 points: [(x1,y1),(x2,y2),(x3,y3)] ),
                hash(Polygon 2 on layer 1 points: [(x1,y1),(x2,y2),(x3,y3),(x4,y4)] ),
                hash(Polygon 3 on layer 1 points: [(x1,y1),(x2,y2),(x3,y3)] ),
                hash(Second layer information: [layer2, datatype2]),
                hash(Polygon 1 on layer 2 points: [(x1,y1),(x2,y2),(x3,y3),(x4,y4)] ),
                hash(Polygon 2 on layer 2 points: [(x1,y1),(x2,y2),(x3,y3)] ),
            )
        """
        # A random offset which fixes common rounding errors intrinsic
        # to floating point math. Example: with a precision of 0.1, the
        # floating points 7.049999 and 7.050001 round to different values
        # (7.0 and 7.1), but offset values (7.220485 and 7.220487) don't
        magic_offset = 0.17048614

        final_hash = hashlib.sha1()
        points = (
            np.ascontiguousarray(
                (self.points / precision) + magic_offset, dtype=np.float64
            )
            .round()
            .astype(np.int64)
        )
        final_hash.update(points)
        angles = (
            (
                np.ascontiguousarray(
                    (self.start_angle, self.end_angle), dtype=np.float64
                )
                / precision
            )
            .round()
            .astype(np.int64)
        )
        final_hash.update(angles)
        return final_hash.hexdigest()

    @classmethod
    def __get_validators__(cls):
        """For pydantic."""
        yield cls._validate

    @classmethod
    def _validate(cls, v, validation_info):
        """Pydantic Path validator."""
        assert isinstance(v, Path), f"TypeError, Got {type(v)}, expecting Path"
        return v

    def to_dict(self) -> dict[str, str]:
        return dict(hash=self.hash_geometry())

    def plot(self) -> None:
        """Plot path in matplotlib.

        .. plot::
            :include-source:

            import gdsfactory as gf

            p = gf.path.euler(radius=10)
            p.plot()
        """
        from gdsfactory.quickplotter import quickplot

        return quickplot(self)

    def extrude(
        self,
        cross_section: CrossSectionSpec | None = None,
        layer: LayerSpec | None = None,
        width: float | None = None,
        simplify: float | None = None,
        shear_angle_start: float | None = None,
        shear_angle_end: float | None = None,
        add_pins: bool = False,
        **kwargs,
    ) -> Component:
        """Returns Component by extruding a Path with a CrossSection.

        A path can be extruded using any CrossSection returning a Component
        The CrossSection defines the layer numbers, widths and offsets.

        Args:
            cross_section: to extrude.
            layer: optional layer.
            width: optional width in um.
            simplify: Tolerance value for the simplification algorithm. \
                    All points that can be removed without changing the resulting polygon\
                    by more than the value listed here will be removed.
            shear_angle_start: an optional angle to shear the starting face by (in degrees).
            shear_angle_end: an optional angle to shear the ending face by (in degrees).
            add_pins: if True adds pins to the ports of the component according to `cross_section`.

        Keyword Args:
            Supplied to :func:`gf.cell`.

        .. plot::
            :include-source:

            import gdsfactory as gf

            p = gf.path.euler(radius=10)
            c = p.extrude(layer=(1, 0), width=0.5)
            c.plot()
        """
        return extrude(
            p=self,
            cross_section=cross_section,
            layer=layer,
            width=width,
            simplify=simplify,
            shear_angle_start=shear_angle_start,
            shear_angle_end=shear_angle_end,
            add_pins=add_pins,
            **kwargs,
        )

    def copy(self):
        """Returns a copy of the Path."""
        p = Path()
        p.info = self.info.copy()
        p.points = np.array(self.points)
        p.start_angle = self.start_angle
        p.end_angle = self.end_angle
        return p


PathFactory = Callable[..., Path]


def _sinusoidal_transition(y1, y2):
    dy = y2 - y1

    def sine(t):
        return y1 + (1 - np.cos(np.pi * t)) / 2 * dy

    return sine


def _parabolic_transition(y1, y2):
    dy = y2 - y1

    def parabolic(t):
        return y1 + np.sqrt(t) * dy

    return parabolic


def _linear_transition(y1, y2):
    dy = y2 - y1

    def linear(t):
        return y1 + t * dy

    return linear

def _elliptical_transition(y1, y2):
    dy = y2 - y1

    def ellipse(t):
        return y2 - dy * np.sqrt(1 - t ** 2)

    return ellipse

def transition_exponential(y1, y2, exp=0.5):
    """Returns the function for an exponential transition.

    Args:
        y1: start width in um.
        y2: end width in um.
        exp: exponent.

    """

    def exponential(t):
        return y1 + (y2 - y1) * t**exp

    return exponential


adiabatic_polyfit_TE1550SOI_220nm = np.array(
    [
        1.02478963e-09,
        -8.65556534e-08,
        3.32415694e-06,
        -7.68408985e-05,
        1.19282177e-03,
        -1.31366332e-02,
        1.05721429e-01,
        -6.31057637e-01,
        2.80689677e00,
        -9.26867694e00,
        2.24535191e01,
        -3.90664800e01,
        4.71899278e01,
        -3.74726005e01,
        1.77381560e01,
        -1.12666286e00,
    ]
)


def transition_adiabatic(
    w1: float,
    w2: float,
    neff_w,
    wavelength: float = 1.55,
    alpha: float = 1,
    max_length: float = 200,
    num_points_ODE: int = 2000,
):
    """Returns the points for an optimal adiabatic transition for well-guided modes.

    Args:
        w1: start width in um.
        w2: end width in um.
        neff_w: a callable that returns the effective index as a function of width. \
                By default, use a compact model of neff(y) for fundamental 1550 nm TE \
                mode of 220nm-thick core with 3.45 index, fully clad with 1.44 index.\
                Many coefficients are needed to capture the behaviour.
        wavelength: wavelength, in same units as widths
        alpha: parameter that scales the rate of width change
            - closer to 0 means longer and more adiabatic;
            - 1 is the intuitive limit beyond which higher order modes are excited;
            - [2] reports good performance up to 1.4 for fundamental TE in SOI (for multiple core thicknesses)
        max_length: maximum length in um.
        num_points_ODE: number of samplings points for the ODE solve.

    References:
        [1] Burns, W. K., et al. "Optical waveguide parabolic coupling horns."
            Appl. Phys. Lett., vol. 30, no. 1, 1 Jan. 1977, pp. 28-30, doi:10.1063/1.89199.
        [2] Fu, Yunfei, et al. "Efficient adiabatic silicon-on-insulator waveguide taper."
            Photonics Res., vol. 2, no. 3, 1 June 2014, pp. A41-A44, doi:10.1364/PRJ.2.000A41.
    """
    from scipy.integrate import odeint

    # Define ODE
    def dWdx(w, x, neff_w, wavelength, alpha):
        return alpha * wavelength / (neff_w(w) * w)

    # Parse input
    if w2 < w1:
        wmin = w2
        wmax = w1
        order = -1
    else:
        wmin = w1
        wmax = w2
        order = 1

    # Solve ODE
    x = np.linspace(0, max_length, num_points_ODE)

    sol = odeint(dWdx, wmin, x, args=(neff_w, wavelength, alpha))

    # Extract optimal curve
    xs = x[np.where(sol[:, 0] < wmax)]
    ws = sol[:, 0][np.where(sol[:, 0] < wmax)]

    return xs, ws[::order]


def transition(
    cross_section1: CrossSectionSpec,
    cross_section2: CrossSectionSpec,
    width_type: WidthTypes | Callable = "sine",
) -> Transition:
    """Returns a smoothly-transitioning between two CrossSections.

    Only cross-sectional elements that have the `name` (as in X.add(..., name = 'wg') )
    parameter specified in both input CrossSections will be created.
    Port names will be cloned from the input CrossSections in reverse.

    Args:
        cross_section1: First CrossSection.
        cross_section2: Second CrossSection.
        width_type: sine or linear. type of width transition used if any widths \
                are different between the two input CrossSections.

    """
    from gdsfactory.pdk import get_cross_section, get_layer

    X1 = get_cross_section(cross_section1)
    X2 = get_cross_section(cross_section2)

    layers1 = {get_layer(section.layer) for section in X1.sections}
    layers2 = {get_layer(section.layer) for section in X2.sections}
    layers1.add(get_layer(X1.layer))
    layers2.add(get_layer(X2.layer))

    has_common_layers = bool(layers1.intersection(layers2))
    if not has_common_layers:
        raise ValueError(
            f"transition() found no common layers X1 {layers1} and X2 {layers2}"
        )

    return Transition(
        cross_section1=X1,
        cross_section2=X2,
        width_type=width_type,
    )


@cell
def along_path(
    p: Path,
    component: ComponentSpec,
    spacing: float,
    padding: float,
) -> Component:
    """Returns Component containing many copies of `component` along `p`.

    Places as many copies of `component` along each segment of `p` as possible
    under the given constraints. `spacing` is always followed precisely, but
    actual `padding` may exceed the provided value to place components evenly.

    Args:
        p: Path to place components along.
        component: Component to repeat along the path. The unrotated version of \
                this object should be oriented for placement on a horizontal line.
        spacing: distance between component placements.
        padding: minimum distance from the path start to the first component.
    """
    from gdsfactory.pdk import get_component

    component = get_component(component)

    length = p.length()
    number = (length - 2 * padding) // spacing + 1

    c = Component()

    cum_dist = 0
    next_component = (length - (number - 1) * spacing) / 2
    stop = length - next_component

    # Prepare in advance the rotation angle for each segment
    angle_list = [
        np.rad2deg(
            np.arctan2(
                (p.points[i + 1] - p.points[i])[1], (p.points[i + 1] - p.points[i])[0]
            )
        )
        for i in range(len(p.points) - 1)
    ]

    for i, start_pt in enumerate(p.points[:-1]):
        end_pt = p.points[i + 1]
        segment_vector = end_pt - start_pt
        segment_length = np.linalg.norm(segment_vector)
        unit_vector = segment_vector / segment_length

        # Get the pre-calculated angle for this segment
        angle = angle_list[i]

        while next_component <= cum_dist + segment_length and next_component <= stop:
            added_dist = next_component - cum_dist
            offset = added_dist * unit_vector
            component_ref = c << component
            component_ref.rotate(angle).move(start_pt + offset)
            next_component += spacing
        cum_dist += segment_length

    return c


@cell
def extrude(
    p: Path,
    cross_section: CrossSectionSpec | None = None,
    layer: LayerSpec | None = None,
    width: float | None = None,
    simplify: float | None = None,
    shear_angle_start: float | None = None,
    shear_angle_end: float | None = None,
    enforce_ports_on_grid: bool | None = None,
    add_pins: bool = False,
) -> Component:
    """Returns Component extruding a Path with a cross_section.

    A path can be extruded using any CrossSection returning a Component
    The CrossSection defines the layer numbers, widths and offsets

    Args:
        p: a path is a list of points (arc, straight, euler).
        cross_section: to extrude.
        layer: optional layer to extrude.
        width: optional width to extrude.
        simplify: Tolerance value for the simplification algorithm. \
                All points that can be removed without changing the resulting polygon \
                by more than the value listed here will be removed.
        shear_angle_start: an optional angle to shear the starting face by (in degrees).
        shear_angle_end: an optional angle to shear the ending face by (in degrees).
        add_pins: if True adds pins to the ports of the component according to `cross_section`.
    """
    from gdsfactory.pdk import (
        get_cross_section,
        get_layer,
    )

    if enforce_ports_on_grid is None:
        enforce_ports_on_grid = CONF.enforce_ports_on_grid

    if cross_section is None and layer is None:
        raise ValueError("CrossSection or layer needed")

    if cross_section is not None and layer is not None:
        raise ValueError("Define only CrossSection or layer")

    if layer is not None and width is None:
        raise ValueError("Need to define layer width")
    elif width:
        s = Section(
            width=width,
            layer=layer,
            port_names=("o1", "o2"),
            port_types=("optical", "optical"),
        )
        cross_section = CrossSection(sections=(s,))

    xsection_points = []
    c = Component()

    x = get_cross_section(cross_section)

    if isinstance(x, Transition):
        return extrude_transition(
            p,
            transition=x,
            shear_angle_start=shear_angle_start,
            shear_angle_end=shear_angle_end,
        )

    for section in x.sections:
        p_sec = p.copy()
        width = section.width
        offset = section.offset
        layer = get_layer(section.layer)
        port_names = section.port_names
        port_types = section.port_types
        hidden = section.hidden
        width_function = section.width_function
        offset_function = section.offset_function

        if isinstance(width, int | float) and isinstance(offset, int | float):
            xsection_points.append([width, offset])
        if isinstance(layer, int):
            layer = (layer, 0)
        if (
            isinstance(layer, Iterable)
            and len(layer) == 2
            and isinstance(layer[0], int)
            and isinstance(layer[1], int)
        ):
            xsection_points.append([layer[0], layer[1]])

        if section.insets and section.insets != (0, 0):
            p_pts = p_sec.points

            new_x_start = p.xmin + section.insets[0]
            new_x_stop = p.xmax - section.insets[1]

            if new_x_start > np.max(p_pts[:, 0]) or new_x_stop < np.min(p_pts[:, 0]):
                warnings.warn(
                    f"Cannot apply delay to Section '{section.name}', delay results in points outside of original path.",
                    stacklevel=3,
                )
                continue

            new_start_idx = np.argwhere(p_pts[:, 0] > new_x_start)[0, 0]
            new_stop_idx = np.argwhere(p_pts[:, 0] < new_x_stop)[-1, 0]

            new_start_point = [new_x_start, p_pts[new_start_idx, 1]]
            new_stop_point = [new_x_stop, p_pts[new_stop_idx, 1]]

            p_sec = Path(
                [new_start_point, *p_pts[new_start_idx:new_stop_idx], new_stop_point]
            )

        if callable(offset_function):
            p_sec.offset(offset_function)
            offset = 0
        end_angle = p_sec.end_angle
        start_angle = p_sec.start_angle
        points = p_sec.points
        points = np.round(points, 3)
        if callable(width_function):
            # Compute lengths
            dx = np.diff(p_sec.points[:, 0])
            dy = np.diff(p_sec.points[:, 1])
            lengths = np.cumsum(np.sqrt(dx**2 + dy**2))
            lengths = np.concatenate([[0], lengths])
            width = width_function(lengths / lengths[-1])
        dy = offset + width / 2
        # _points = _shear_face(points, dy, shear_angle_start, shear_angle_end)

        points1 = p_sec._centerpoint_offset_curve(
            points,
            offset_distance=dy,
            start_angle=start_angle,
            end_angle=end_angle,
        )
        dy = offset - width / 2
        # _points = _shear_face(points, dy, shear_angle_start, shear_angle_end)

        points2 = p_sec._centerpoint_offset_curve(
            points,
            offset_distance=dy,
            start_angle=start_angle,
            end_angle=end_angle,
        )
        if shear_angle_start or shear_angle_end:
            _face_angle_start = (
                start_angle + shear_angle_start - 90 if shear_angle_start else None
            )
            _face_angle_end = (
                end_angle + shear_angle_end + 90 if shear_angle_end else None
            )
            points1 = _cut_path_with_ray(
                start_point=points[0],
                start_angle=_face_angle_start,
                end_point=points[-1],
                end_angle=_face_angle_end,
                path=points1,
            )
            points2 = _cut_path_with_ray(
                start_point=points[0],
                start_angle=_face_angle_start,
                end_point=points[-1],
                end_angle=_face_angle_end,
                path=points2,
            )

        # angle = start_angle + shear_angle_start + 90
        # points2 = _cut_path_with_ray(points[0], angle, points2, start=True)
        # Simplify lines using the Ramer–Douglas–Peucker algorithm
        if isinstance(simplify, bool):
            raise ValueError("simplify argument must be a number (e.g. 1e-3) or None")

        with_simplify = section.simplify or simplify

        if with_simplify:
            points1 = _simplify(points1, tolerance=with_simplify)
            points2 = _simplify(points2, tolerance=with_simplify)

        # Join points together
        points_poly = np.concatenate([points1, points2[::-1, :]])

        layers = layer if hidden else [layer, layer]
        if not hidden and p_sec.length() > 1e-3:
            c.add_polygon(points_poly, layer=layer)

        # Add port_names if they were specified
        if port_names[0] is not None:
            port_width = width if np.isscalar(width) else width[0]
            port_orientation = (p_sec.start_angle + 180) % 360
            center = points[0]
            face = [points1[0], points2[0]]
            face = [_rotated_delta(point, center, port_orientation) for point in face]

            c.add_port(
                port=Port(
                    name=port_names[0],
                    layer=get_layer(layers[0]),
                    port_type=port_types[0],
                    width=port_width,
                    orientation=port_orientation,
                    center=center,
                    cross_section=x,
                    shear_angle=shear_angle_start,
                    enforce_ports_on_grid=enforce_ports_on_grid,
                )
            )
            # port1.info["face"] = face
        if port_names[1] is not None:
            port_width = width if np.isscalar(width) else width[-1]
            port_orientation = (p_sec.end_angle) % 360
            center = points[-1]
            face = [points1[-1], points2[-1]]
            face = [_rotated_delta(point, center, port_orientation) for point in face]

            c.add_port(
                port=Port(
                    name=port_names[1],
                    layer=get_layer(layers[1]),
                    port_type=port_types[1],
                    width=port_width,
                    center=center,
                    orientation=port_orientation,
                    cross_section=x,
                    shear_angle=shear_angle_end,
                    enforce_ports_on_grid=enforce_ports_on_grid,
                )
            )
            # port2.info["face"] = face

    c.info["length"] = float(np.round(p.length(), 3))

    for via in x.components_along_path:
        if via.offset:
            points_offset = p._centerpoint_offset_curve(
                points,
                offset_distance=via.offset,
                start_angle=start_angle,
                end_angle=end_angle,
            )
            _p = Path(points_offset)
        else:
            _p = p
        _ = c << along_path(
            p=_p, component=via.component, spacing=via.spacing, padding=via.padding
        )
    if add_pins:
        x.add_pins(c)
    return c


def _get_named_sections(sections: tuple[Section, ...]) -> dict[str, Section]:
    from gdsfactory.pdk import get_layer

    named_sections = {}
    for section in sections:
        name = section.name or get_layer(section.layer)
        if name in named_sections:
            raise ValueError(
                f"Duplicate name or layer '{name}' of section used for cross-section in transition. Cross-sections with multiple Sections for a single layer must have unique names for each section"
            )
        named_sections[name] = section
    return named_sections


@cell
def extrude_transition(
    p: Path,
    transition: Transition,
    shear_angle_start: float | None = None,
    shear_angle_end: float | None = None,
) -> Component:
    """Extrudes a path along a transition.

    Args:
        p: path to extrude.
        transition: transition to extrude along.
        shear_angle_start: angle to shear the start of the path.
        shear_angle_end: angle to shear the end of the path.
    """

    from gdsfactory.pdk import get_cross_section, get_layer

    c = Component()

    x1 = get_cross_section(transition.cross_section1)
    x2 = get_cross_section(transition.cross_section2)
    width_type = transition.width_type

    # if named, prefer name over layer
    named_sections1 = _get_named_sections(x1.sections)
    named_sections2 = _get_named_sections(x2.sections)

    names1 = list(named_sections1.keys())
    names2 = list(named_sections2.keys())

    common_sections = set(names1).intersection(names2)
    if len(common_sections) == 0:
        raise ValueError(
            f"transition() found no common layers X1 {names1} and X2 {names2}"
        )

    for section_name in common_sections:
        section1 = named_sections1[section_name]
        section2 = named_sections2[section_name]
        port_names = section1.port_names
        port_types = section1.port_types

        p_sec = p.copy()
        offset1 = section1.offset
        offset2 = section2.offset
        width1 = section1.width
        width2 = section2.width

        if callable(offset1):
            offset1 = offset1(1)
        if callable(offset2):
            offset2 = offset2(0)
        if callable(width1):
            width1 = width1(1)
        if callable(width2):
            width2 = width2(0)

        offset = _sinusoidal_transition(offset1, offset2)

        if width_type == "linear":
            width = _linear_transition(width1, width2)
        elif width_type == "sine":
            width = _sinusoidal_transition(width1, width2)
        elif width_type == "parabolic":
            width = _parabolic_transition(width1, width2)
        elif width_type == "elliptical":
            width = _elliptical_transition(width1, width2)
        elif callable(width_type):

            def width_func(t):
                return width_type(t, width1, width2)  # noqa: B023

            width = width_func
        else:
            raise ValueError(
                f"width_type={width_type!r} must be {'sine','linear','parabolic'}, or a Callable w(t, width1, width2) returning the transition profile as a function of path position t."
            )

        if section1.layer != section2.layer:
            hidden = True
            layer1 = get_layer(section1.layer)
            layer2 = get_layer(section2.layer)
            layer = (layer1, layer2)
        else:
            hidden = False
            layer = get_layer(section1.layer)

        p_sec.offset(offset)
        offset = 0
        end_angle = p_sec.end_angle
        start_angle = p_sec.start_angle
        points = p_sec.points
        points = np.round(points, 3)
        if callable(width):
            # Compute lengths
            dx = np.diff(p_sec.points[:, 0])
            dy = np.diff(p_sec.points[:, 1])
            lengths = np.cumsum(np.sqrt(dx**2 + dy**2))
            lengths = np.concatenate([[0], lengths])
            width = width(lengths / lengths[-1])
        dy = offset + width / 2
        # _points = _shear_face(points, dy, shear_angle_start, shear_angle_end)

        points1 = p_sec._centerpoint_offset_curve(
            points,
            offset_distance=dy,
            start_angle=start_angle,
            end_angle=end_angle,
        )
        dy = offset - width / 2
        # _points = _shear_face(points, dy, shear_angle_start, shear_angle_end)

        points2 = p_sec._centerpoint_offset_curve(
            points,
            offset_distance=dy,
            start_angle=start_angle,
            end_angle=end_angle,
        )
        if shear_angle_start or shear_angle_end:
            _face_angle_start = (
                start_angle + shear_angle_start - 90 if shear_angle_start else None
            )
            _face_angle_end = (
                end_angle + shear_angle_end + 90 if shear_angle_end else None
            )
            points1 = _cut_path_with_ray(
                start_point=points[0],
                start_angle=_face_angle_start,
                end_point=points[-1],
                end_angle=_face_angle_end,
                path=points1,
            )
            points2 = _cut_path_with_ray(
                start_point=points[0],
                start_angle=_face_angle_start,
                end_point=points[-1],
                end_angle=_face_angle_end,
                path=points2,
            )

        with_simplify = section1.simplify and section2.simplify

        if with_simplify:
            tolerance = min([section1.simplify, section2.simplify])
            points1 = _simplify(points1, tolerance=tolerance)
            points2 = _simplify(points2, tolerance=tolerance)

        # Join points together
        points_poly = np.concatenate([points1, points2[::-1, :]])

        layers = layer if hidden else [layer, layer]
        if not hidden and p_sec.length() > 1e-3:
            c.add_polygon(points_poly, layer=layer)

        # Add port_names if they were specified
        if port_names[0] is not None:
            port_width = width1
            port_orientation = (p_sec.start_angle + 180) % 360
            center = points[0]
            face = [points1[0], points2[0]]
            face = [_rotated_delta(point, center, port_orientation) for point in face]

            c.add_port(
                port=Port(
                    name=port_names[0],
                    layer=get_layer(layers[0]),
                    port_type=port_types[0],
                    width=port_width,
                    orientation=port_orientation,
                    center=center,
                    cross_section=x1,
                    shear_angle=shear_angle_start,
                )
            )
            # port1.info["face"] = face
        if port_names[1] is not None:
            port_width = width2
            port_orientation = (p_sec.end_angle) % 360
            center = points[-1]
            face = [points1[-1], points2[-1]]
            face = [_rotated_delta(point, center, port_orientation) for point in face]

            c.add_port(
                port=Port(
                    name=port_names[1],
                    layer=get_layer(layers[1]),
                    port_type=port_types[1],
                    width=port_width,
                    center=center,
                    orientation=port_orientation,
                    cross_section=x2,
                    shear_angle=shear_angle_end,
                )
            )
            # port2.info["face"] = face

    c.info["length"] = float(np.round(p.length(), 3))
    return c


def _rotated_delta(
    point: np.ndarray, center: np.ndarray, orientation: float
) -> np.ndarray:
    """Gets the rotated distance of a point from a center.

    Args:
        point: the initial point.
        center: a center point to use as a reference.
        orientation: the rotation, in degrees.

    Returns: the normalized delta between the point and center, accounting for rotation
    """
    ca = np.cos(orientation * np.pi / 180)
    sa = np.sin(orientation * np.pi / 180)
    rot_mat = np.array([[ca, -sa], [sa, ca]])
    delta = point - center
    return np.dot(delta, rot_mat)


def _cut_path_with_ray(
    start_point: np.ndarray,
    start_angle: float | None,
    end_point: np.ndarray,
    end_angle: float | None,
    path: np.ndarray,
) -> np.ndarray:
    """Cuts or extends a path given a point and angle to project."""
    import shapely.geometry as sg
    import shapely.ops

    # a distance to approximate infinity to find ray-segment intersections
    far_distance = 10000

    path_cmp = np.copy(path)
    # pad start
    dp = path[0] - path[1]
    d_ext = far_distance / np.sqrt(np.sum(dp**2)) * np.array([dp[0], dp[1]])
    path_cmp[0] += d_ext
    # pad end
    dp = path[-1] - path[-2]
    d_ext = far_distance / np.sqrt(np.sum(dp**2)) * np.array([dp[0], dp[1]])
    path_cmp[-1] += d_ext

    intersections = [sg.Point(path[0]), sg.Point(path[-1])]
    distances = []
    ls = sg.LineString(path_cmp)
    for i, angle, point in [(0, start_angle, start_point), (1, end_angle, end_point)]:
        if angle:
            # get intersection
            angle_rad = np.deg2rad(angle)
            dx_far = np.cos(angle_rad) * far_distance
            dy_far = np.sin(angle_rad) * far_distance
            d_far = np.array([dx_far, dy_far])
            ls_ray = sg.LineString([point - d_far, point + d_far])
            intersection = ls.intersection(ls_ray)

            if not isinstance(intersection, sg.Point):
                if not isinstance(intersection, sg.MultiPoint):
                    raise ValueError(
                        f"Expected intersection to be a point, but got {intersection}"
                    )
                _, nearest = shapely.ops.nearest_points(sg.Point(point), intersection)
                intersection = nearest
            intersections[i] = intersection
        else:
            intersection = intersections[i]
        distance = ls.project(intersection)
        distances.append(distance)
    # when trimming the start, start counting at the intersection point, then
    # add all subsequent points
    points = [np.array(intersections[0].coords[0])]
    for point in path[1:-1]:
        if distances[0] < ls.project(sg.Point(point)) < distances[1]:
            points.append(point)
    points.append(np.array(intersections[1].coords[0]))
    return np.array(points)


def arc(
    radius: float = 10.0,
    angle: float = 90,
    npoints: int | None = None,
    start_angle: float | None = -90,
) -> Path:
    """Returns a radial arc.

    Args:
        radius: minimum radius of curvature.
        angle: total angle of the curve.
        npoints: Number of points used per 360 degrees. Defaults to pdk.bend_points_distance.
        start_angle: initial angle of the curve for drawing, default -90 degrees.

    .. plot::
        :include-source:

        import gdsfactory as gf

        p = gf.path.arc(radius=10, angle=45)
        p.plot()

    """
    from gdsfactory.pdk import get_active_pdk

    PDK = get_active_pdk()

    npoints = npoints or abs(int(angle / 360 * radius / PDK.bend_points_distance / 2))
    npoints = max(int(npoints), int(360 / angle) + 1)

    t = np.linspace(
        start_angle * np.pi / 180, (angle + start_angle) * np.pi / 180, npoints
    )
    x = radius * np.cos(t)
    y = radius * (np.sin(t) + 1)
    points = np.array((x, y)).T * np.sign(angle)

    P = Path()
    # Manually add points & adjust start and end angles
    P.points = points
    P.start_angle = start_angle + 90
    P.end_angle = start_angle + angle + 90
    return P


def _cumtrapz(x):
    """Numpy-based implementation of the cumulative trapezoidal integration \
    function usually found in scipy (scipy.integrate.cumtrapz)."""
    return np.cumsum((x[1:] + x[:-1]) / 2)


def _fresnel(R0, s, num_pts, n_iter=8):
    """Fresnel integral using a series expansion."""
    t = np.linspace(0, s / (np.sqrt(2) * R0), num_pts)
    x = np.zeros(num_pts)
    y = np.zeros(num_pts)

    for n in range(n_iter):
        x += (-1) ** n * t ** (4 * n + 1) / (math.factorial(2 * n) * (4 * n + 1))
        y += (-1) ** n * t ** (4 * n + 3) / (math.factorial(2 * n + 1) * (4 * n + 3))

    return np.array([np.sqrt(2) * R0 * x, np.sqrt(2) * R0 * y])


def euler(
    radius: float = 10,
    angle: float = 90,
    p: float = 0.5,
    use_eff: bool = False,
    npoints: int | None = None,
) -> Path:
    """Returns an euler bend that adiabatically transitions from straight to curved.

    `radius` is the minimum radius of curvature of the bend.
    However, if `use_eff` is set to True, `radius` corresponds to the effective
    radius of curvature (making the curve a drop-in replacement for an arc).
    If p < 1.0, will create a "partial euler" curve as described in Vogelbacher et. al.
    https://dx.doi.org/10.1364/oe.27.031394

    Args:
        radius: minimum radius of curvature.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        use_eff: If False: `radius` is the minimum radius of curvature of the bend. \
                If True: The curve will be scaled such that the endpoints match an \
                arc with parameters `radius` and `angle`.
        npoints: Number of points used per 360 degrees.

    .. plot::
        :include-source:

        import gdsfactory as gf

        p = gf.path.euler(radius=10, angle=45, p=1, use_eff=True, npoints=720)
        p.plot()

    """
    from gdsfactory.pdk import get_active_pdk

    if (p < 0) or (p > 1):
        raise ValueError("euler requires argument `p` be between 0 and 1")
    if p == 0:
        P = arc(radius=radius, angle=angle, npoints=npoints)
        P.info["Reff"] = radius
        P.info["Rmin"] = radius
        return P

    if angle < 0:
        mirror = True
        angle = np.abs(angle)
    else:
        mirror = False

    R0 = 1
    alpha = np.radians(angle)
    Rp = R0 / (np.sqrt(p * alpha))
    sp = R0 * np.sqrt(p * alpha)
    s0 = 2 * sp + Rp * alpha * (1 - p)

    pdk = get_active_pdk()
    npoints = npoints or abs(int(angle / 360 * radius / pdk.bend_points_distance / 2))
    npoints = max(npoints, int(360 / angle) + 1)

    num_pts_euler = int(np.round(sp / (s0 / 2) * npoints))
    num_pts_arc = npoints - num_pts_euler

    # Ensure a minimum of 2 points for each euler/arc section
    if npoints <= 2:
        num_pts_euler = 0
        num_pts_arc = 2

    if num_pts_euler > 0:
        xbend1, ybend1 = _fresnel(R0, sp, num_pts_euler)
        xp, yp = xbend1[-1], ybend1[-1]
        dx = xp - Rp * np.sin(p * alpha / 2)
        dy = yp - Rp * (1 - np.cos(p * alpha / 2))
    else:
        xbend1 = ybend1 = np.asfarray([])
        dx = 0
        dy = 0

    s = np.linspace(sp, s0 / 2, num_pts_arc)
    xbend2 = Rp * np.sin((s - sp) / Rp + p * alpha / 2) + dx
    ybend2 = Rp * (1 - np.cos((s - sp) / Rp + p * alpha / 2)) + dy

    x = np.concatenate([xbend1, xbend2[1:]])
    y = np.concatenate([ybend1, ybend2[1:]])
    points1 = np.array([x, y]).T
    points2 = np.flipud(np.array([x, -y]).T)

    points2 = _rotate_points(points2, angle - 180)
    points2 += -points2[0, :] + points1[-1, :]

    points = np.concatenate([points1[:-1], points2])

    # Find y-axis intersection point to compute Reff
    start_angle = 180 * (angle < 0)
    end_angle = start_angle + angle
    dy = np.tan(np.radians(end_angle - 90)) * points[-1][0]
    Reff = points[-1][1] - dy
    Rmin = Rp

    # Fix degenerate condition at angle == 180
    if np.abs(180 - angle) < 1e-3:
        Reff = points[-1][1] / 2

    # Scale curve to either match Reff or Rmin
    scale = radius / Reff if use_eff else radius / Rmin
    points *= scale

    P = Path()

    # Manually add points & adjust start and end angles
    P.points = points
    P.start_angle = start_angle
    P.end_angle = end_angle
    P.info["Reff"] = Reff * scale
    P.info["Rmin"] = Rmin * scale
    if mirror:
        P.mirror((1, 0))
    return P


def straight(length: float = 10.0, npoints: int = 2) -> Path:
    """Returns a straight path.

    For transitions you should increase have at least 100 points

    Args:
        length: of straight.
        npoints: number of points.

    """
    if length < 0:
        raise ValueError(f"length = {length} needs to be > 0")
    x = np.linspace(0, length, npoints)
    y = x * 0
    points = np.array((x, y)).T

    p = Path()
    p.append(points)
    return p


def spiral_archimedean(
    min_bend_radius: float, separation: float, number_of_loops: float, npoints: int
) -> Path:
    """Returns an Archimedean spiral.

    Args:
        min_bend_radius: Inner radius of the spiral.
        separation: Separation between the loops in um.
        number_of_loops: number of loops.
        npoints: number of Points.

    .. plot::
        :include-source:

        import gdsfactory as gf

        p = gf.path.spiral_archimedean(min_bend_radius=5, separation=2, number_of_loops=3, npoints=200)
        p.plot()

    """
    return Path(
        [
            (separation / np.pi * theta + min_bend_radius)
            * np.array((np.sin(theta), np.cos(theta)))
            for theta in np.linspace(0, number_of_loops * 2 * np.pi, npoints)
        ]
    )


def _compute_segments(points):
    points = np.asfarray(points)
    normals = np.diff(points, axis=0)
    normals = (normals.T / np.linalg.norm(normals, axis=1)).T
    dx = np.diff(points[:, 0])
    dy = np.diff(points[:, 1])
    ds = np.sqrt(dx**2 + dy**2)
    theta = np.degrees(np.arctan2(dy, dx))
    dtheta = np.diff(theta)
    dtheta = dtheta - 360 * np.floor((dtheta + 180) / 360)
    return points, normals, ds, theta, dtheta


def smooth(
    points: Coordinates,
    radius: float = 4.0,
    bend: PathFactory = euler,
    **kwargs,
) -> Path:
    """Returns a smooth Path from a series of waypoints.

    Args:
        points: array-like[N][2] List of waypoints for the path to follow.
        radius: radius of curvature, passed to `bend`.
        bend: bend function that returns a path that round corners.
        kwargs: Extra keyword arguments that will be passed to `bend`.

    .. plot::
        :include-source:

        import gdsfactory as gf

        p = gf.path.smooth(([0, 0], [0, 10], [10, 10]))
        p.plot()

    """
    if isinstance(points, Path):
        points = points.points

    points, normals, ds, theta, dtheta = _compute_segments(points)
    colinear_elements = np.concatenate([[False], np.abs(dtheta) < 1e-6, [False]])
    if np.any(colinear_elements):
        new_points = points[~colinear_elements, :]
        points, normals, ds, theta, dtheta = _compute_segments(new_points)

    if np.any(np.abs(np.abs(dtheta) - 180) < 1e-6):
        raise ValueError(
            "smooth() received points which double-back on themselves"
            "--turns cannot be computed when going forwards then exactly backwards."
        )

    # FIXME add caching
    # Create arcs
    paths = []
    radii = []
    for dt in dtheta:
        P = bend(radius=radius, angle=dt, **kwargs)
        chord = np.linalg.norm(P.points[-1, :] - P.points[0, :])
        r = (chord / 2) / np.sin(np.radians(dt / 2))
        r = np.abs(r)
        radii.append(r)
        paths.append(P)

    d = np.abs(np.array(radii) / np.tan(np.radians(180 - dtheta) / 2))
    encroachment = np.concatenate([[0], d]) + np.concatenate([d, [0]])
    if np.any(encroachment > ds):
        raise ValueError(
            "smooth(): Not enough distance between points to to fit curves."
            "Try reducing the radius or spacing the points out farther"
        )
    p1 = points[1:-1, :] - normals[:-1, :] * d[:, np.newaxis]

    # Move arcs into position
    new_points = []
    new_points.append([points[0, :]])
    for n in range(len(dtheta)):
        P = paths[n]
        P.rotate(theta[n] - 0)
        P.move(p1[n])
        new_points.append(P.points)
    new_points.append([points[-1, :]])
    new_points = np.concatenate(new_points)

    P = Path()
    P.rotate(theta[0])
    P.append(new_points)
    P.move(points[0, :])
    return P


__all__ = [
    "Path",
    "arc",
    "along_path",
    "euler",
    "extrude",
    "extrude_transition",
    "smooth",
    "spiral_archimedean",
    "straight",
    "transition",
    "transition_adiabatic",
]

if __name__ == "__main__":
    import gdsfactory as gf

    P = gf.path.straight(length=10)
    s0 = gf.Section(
        width=0.415, offset=0, layer=(1, 0), name="core", port_names=("o1", "o2")
    )
    s1 = gf.Section(width=3, offset=0, layer=(3, 0), name="slab")
    X1 = gf.CrossSection(sections=(s0, s1))
    s2 = gf.Section(
        width=0.5, offset=0, layer=(1, 0), name="core", port_names=("o1", "o2")
    )
    s3 = gf.Section(width=2.0, offset=0, layer=(3, 0), name="slab")
    X2 = gf.CrossSection(sections=(s2, s3))

    def width_type_function(t, w1, w2):
        return w1 + (w2 - w1) * (t + 1) / 2

    # t = gf.path.transition(X1, X2, width_type=width_type_function)
    # c = gf.path.extrude(P, t, shear_angle_start=10, shear_angle_end=45)
    # c = gf.path.extrude(P, t)

    w1 = 1
    w2 = 5
    x1 = gf.get_cross_section("xs_sc", width=w1)
    x2 = gf.get_cross_section("xs_sc", width=w2)
    trans = gf.path.transition(
        x1, x2, width_type=lambda t: width_type_function(t, w1, w2)
    )
    c = gf.components.bend_euler(radius=10, cross_section=trans)
    # xs = gf.cross_section.pn(slab_inset=-0.2)
    # c = gf.c.straight(cross_section=xs)
    c.show(show_ports=True)
