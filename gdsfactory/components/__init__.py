"""Each component factory component returns a component.

Make sure your components get imported here so the PDK registers them.
"""

from __future__ import annotations

import sys

from gdsfactory.components.add_fiber_array_optical_south_electrical_north import (
    add_fiber_array_optical_south_electrical_north,
)
from gdsfactory.components.add_termination import add_termination
from gdsfactory.components.add_trenches import add_trenches, add_trenches90
from gdsfactory.components.align import add_frame, align_wafer
from gdsfactory.components.array_component import array
from gdsfactory.components.awg import awg
from gdsfactory.components.bbox import bbox
from gdsfactory.components.bend_circular import (
    bend_circular,
    bend_circular180,
    bend_circular_all_angle,
)
from gdsfactory.components.bend_circular_heater import bend_circular_heater
from gdsfactory.components.bend_euler import (
    bend_euler,
    bend_euler180,
    bend_euler_all_angle,
    bend_euler_s,
)
from gdsfactory.components.bend_s import bend_s
from gdsfactory.components.bezier import bezier
from gdsfactory.components.C import C
from gdsfactory.components.cavity import cavity
from gdsfactory.components.cdsem_all import cdsem_all
from gdsfactory.components.cdsem_bend180 import cdsem_bend180
from gdsfactory.components.cdsem_coupler import cdsem_coupler
from gdsfactory.components.cdsem_straight import cdsem_straight
from gdsfactory.components.cdsem_straight_density import cdsem_straight_density
from gdsfactory.components.circle import circle
from gdsfactory.components.coh_rx_single_pol import coh_rx_single_pol
from gdsfactory.components.coh_tx_dual_pol import coh_tx_dual_pol
from gdsfactory.components.coh_tx_single_pol import coh_tx_single_pol
from gdsfactory.components.compass import compass
from gdsfactory.components.component_sequence import component_sequence
from gdsfactory.components.copy_layers import copy_layers
from gdsfactory.components.coupler import coupler
from gdsfactory.components.coupler90 import coupler90, coupler90circular
from gdsfactory.components.coupler90bend import coupler90bend
from gdsfactory.components.coupler_adiabatic import coupler_adiabatic
from gdsfactory.components.coupler_asymmetric import coupler_asymmetric
from gdsfactory.components.coupler_bent import coupler_bent
from gdsfactory.components.coupler_broadband import coupler_broadband
from gdsfactory.components.coupler_full import coupler_full
from gdsfactory.components.coupler_ring import coupler_ring
from gdsfactory.components.coupler_straight import coupler_straight
from gdsfactory.components.coupler_straight_asymmetric import (
    coupler_straight_asymmetric,
)
from gdsfactory.components.coupler_symmetric import coupler_symmetric
from gdsfactory.components.cross import cross
from gdsfactory.components.crossing_waveguide import (
    crossing,
    crossing45,
    crossing_arm,
    crossing_etched,
    crossing_from_taper,
)
from gdsfactory.components.cutback_2x2 import cutback_2x2
from gdsfactory.components.cutback_bend import (
    cutback_bend,
    cutback_bend90,
    cutback_bend90circular,
    cutback_bend180,
    cutback_bend180circular,
    staircase,
)
from gdsfactory.components.cutback_component import (
    cutback_component,
    cutback_component_mirror,
)
from gdsfactory.components.cutback_loss import (
    cutback_loss,
    cutback_loss_bend90,
    cutback_loss_bend180,
    cutback_loss_mmi1x2,
    cutback_loss_spirals,
)
from gdsfactory.components.cutback_splitter import cutback_splitter
from gdsfactory.components.dbr import dbr
from gdsfactory.components.dbr_tapered import dbr_tapered
from gdsfactory.components.delay_snake import delay_snake
from gdsfactory.components.delay_snake2 import delay_snake2
from gdsfactory.components.delay_snake_sbend import delay_snake_sbend
from gdsfactory.components.dicing_lane import dicing_lane
from gdsfactory.components.die import die
from gdsfactory.components.die_bbox import die_bbox
from gdsfactory.components.die_with_pads import die_with_pads
from gdsfactory.components.disk import disk, disk_heater
from gdsfactory.components.edge_coupler_array import (
    edge_coupler_array,
    edge_coupler_array_with_loopback,
    edge_coupler_silicon,
)
from gdsfactory.components.ellipse import ellipse
from gdsfactory.components.extend_ports_list import extend_ports_list
from gdsfactory.components.extension import extend_ports
from gdsfactory.components.fiber import fiber
from gdsfactory.components.fiber_array import fiber_array
from gdsfactory.components.fiducial_squares import fiducial_squares
from gdsfactory.components.ge_detector_straight_si_contacts import (
    ge_detector_straight_si_contacts,
)
from gdsfactory.components.grating_coupler_array import grating_coupler_array
from gdsfactory.components.grating_coupler_dual_pol import grating_coupler_dual_pol
from gdsfactory.components.grating_coupler_elliptical import (
    ellipse_arc,
    grating_coupler_elliptical,
    grating_coupler_elliptical_te,
    grating_coupler_elliptical_tm,
    grating_taper_points,
    grating_tooth_points,
)
from gdsfactory.components.grating_coupler_elliptical_arbitrary import (
    grating_coupler_elliptical_arbitrary,
    grating_coupler_elliptical_uniform,
)
from gdsfactory.components.grating_coupler_elliptical_lumerical import (
    grating_coupler_elliptical_lumerical,
)
from gdsfactory.components.grating_coupler_elliptical_trenches import (
    grating_coupler_elliptical_trenches,
    grating_coupler_te,
    grating_coupler_tm,
)
from gdsfactory.components.grating_coupler_loss import (
    grating_coupler_loss_fiber_array,
    grating_coupler_loss_fiber_array4,
    loss_deembedding_ch12_34,
    loss_deembedding_ch13_24,
    loss_deembedding_ch14_23,
)
from gdsfactory.components.grating_coupler_rectangular import (
    grating_coupler_rectangular,
)
from gdsfactory.components.grating_coupler_rectangular_arbitrary import (
    grating_coupler_rectangular_arbitrary,
)
from gdsfactory.components.grating_coupler_tree import grating_coupler_tree
from gdsfactory.components.greek_cross import (
    greek_cross,
    greek_cross_with_pads,
)
from gdsfactory.components.hline import hline
from gdsfactory.components.interdigital_capacitor import interdigital_capacitor
from gdsfactory.components.L import L
from gdsfactory.components.litho_calipers import litho_calipers
from gdsfactory.components.litho_ruler import litho_ruler
from gdsfactory.components.litho_steps import litho_steps
from gdsfactory.components.loop_mirror import loop_mirror
from gdsfactory.components.mmi import mmi
from gdsfactory.components.mmi1x2 import mmi1x2
from gdsfactory.components.mmi1x2_with_sbend import mmi1x2_with_sbend
from gdsfactory.components.mmi2x2 import mmi2x2
from gdsfactory.components.mmi2x2_with_sbend import mmi2x2_with_sbend
from gdsfactory.components.mmi_90degree_hybrid import mmi_90degree_hybrid
from gdsfactory.components.mmi_tapered import mmi_tapered
from gdsfactory.components.mode_converter import mode_converter
from gdsfactory.components.mzi import (
    mzi,
    mzi1x2_2x2,
    mzi2x2_2x2,
    mzi2x2_2x2_phase_shifter,
    mzi_coupler,
    mzi_phase_shifter,
    mzi_phase_shifter_top_heater_metal,
    mzi_pin,
    mzm,
)
from gdsfactory.components.mzi_arm import mzi_arm
from gdsfactory.components.mzi_arms import mzi_arms
from gdsfactory.components.mzi_lattice import mzi_lattice, mzi_lattice_mmi
from gdsfactory.components.mzi_pads_center import mzi_pads_center
from gdsfactory.components.mzit import mzit
from gdsfactory.components.mzit_lattice import mzit_lattice
from gdsfactory.components.nxn import nxn
from gdsfactory.components.optimal_90deg import optimal_90deg
from gdsfactory.components.optimal_hairpin import optimal_hairpin
from gdsfactory.components.optimal_step import optimal_step
from gdsfactory.components.pack_doe import generate_doe, pack_doe, pack_doe_grid
from gdsfactory.components.pad import (
    pad,
    pad_array,
    pad_array0,
    pad_array90,
    pad_array180,
    pad_array270,
    pad_rectangular,
    pad_small,
)
from gdsfactory.components.pad_gsg import pad_gsg_open, pad_gsg_short
from gdsfactory.components.pads_shorted import pads_shorted
from gdsfactory.components.polarization_splitter_rotator import (
    polarization_splitter_rotator,
)
from gdsfactory.components.ramp import ramp
from gdsfactory.components.rectangle import rectangle, rectangles
from gdsfactory.components.rectangle_with_slits import rectangle_with_slits
from gdsfactory.components.regular_polygon import hexagon, octagon, regular_polygon
from gdsfactory.components.resistance_meander import resistance_meander
from gdsfactory.components.resistance_sheet import resistance_sheet
from gdsfactory.components.ring import ring
from gdsfactory.components.ring_crow import ring_crow
from gdsfactory.components.ring_crow_couplers import ring_crow_couplers
from gdsfactory.components.ring_double import ring_double
from gdsfactory.components.ring_double_pn import ring_double_pn
from gdsfactory.components.ring_heater import ring_double_heater, ring_single_heater
from gdsfactory.components.ring_single import ring_single
from gdsfactory.components.ring_single_array import ring_single_array
from gdsfactory.components.ring_single_bend_coupler import (
    coupler_bend,
    ring_single_bend_coupler,
)
from gdsfactory.components.ring_single_dut import ring_single_dut, taper2
from gdsfactory.components.ring_single_pn import ring_single_pn
from gdsfactory.components.seal_ring import seal_ring, seal_ring_segmented
from gdsfactory.components.snspd import snspd
from gdsfactory.components.spiral import spiral
from gdsfactory.components.spiral_double import spiral_double
from gdsfactory.components.spiral_heater import (
    spiral_racetrack,
    spiral_racetrack_fixed_length,
    spiral_racetrack_heater_doped,
    spiral_racetrack_heater_metal,
)
from gdsfactory.components.spiral_inductor import spiral_inductor
from gdsfactory.components.splitter_chain import splitter_chain
from gdsfactory.components.splitter_tree import splitter_tree, switch_tree
from gdsfactory.components.straight import straight, straight_all_angle
from gdsfactory.components.straight_array import straight_array
from gdsfactory.components.straight_heater_doped import (
    straight_heater_doped_rib,
    straight_heater_doped_strip,
)
from gdsfactory.components.straight_heater_meander import straight_heater_meander
from gdsfactory.components.straight_heater_meander_doped import (
    straight_heater_meander_doped,
)
from gdsfactory.components.straight_heater_metal import (
    straight_heater_metal,
    straight_heater_metal_90_90,
    straight_heater_metal_simple,
    straight_heater_metal_undercut,
    straight_heater_metal_undercut_90_90,
)
from gdsfactory.components.straight_pin import straight_pin, straight_pn
from gdsfactory.components.straight_pin_slot import straight_pin_slot
from gdsfactory.components.taper import (
    taper,
    taper_electrical,
    taper_nc_sc,
    taper_sc_nc,
    taper_strip_to_ridge,
    taper_strip_to_ridge_trenches,
)
from gdsfactory.components.taper_adiabatic import taper_adiabatic
from gdsfactory.components.taper_cross_section import (
    taper_cross_section,
    taper_cross_section_linear,
    taper_cross_section_parabolic,
    taper_cross_section_sine,
)
from gdsfactory.components.taper_from_csv import taper_from_csv
from gdsfactory.components.taper_parabolic import taper_parabolic
from gdsfactory.components.terminator import terminator
from gdsfactory.components.text import text, text_klayout, text_lines
from gdsfactory.components.text_freetype import text_freetype
from gdsfactory.components.text_rectangular import (
    text_rectangular,
    text_rectangular_mini,
    text_rectangular_multi_layer,
)
from gdsfactory.components.triangles import triangle, triangle2, triangle4
from gdsfactory.components.verniers import verniers
from gdsfactory.components.version_stamp import pixel, qrcode, version_stamp
from gdsfactory.components.via import via, via1, via2, viac
from gdsfactory.components.via_chain import via_chain
from gdsfactory.components.via_corner import via_corner
from gdsfactory.components.via_stack import (
    via_stack,
    via_stack_corner45,
    via_stack_corner45_extended,
    via_stack_heater_m3,
    via_stack_heater_mtop,
    via_stack_heater_mtop_mini,
    via_stack_m1_mtop,
    via_stack_npp_m1,
    via_stack_slab_m1_horizontal,
    via_stack_slab_m3,
    via_stack_slab_npp_m3,
)
from gdsfactory.components.via_stack_with_offset import via_stack_with_offset
from gdsfactory.components.wafer import wafer
from gdsfactory.components.wire import wire_corner, wire_corner45, wire_straight
from gdsfactory.get_factories import get_cells

__all__ = [
    "awg",
    "add_termination",
    "C",
    "L",
    "add_fiber_array_optical_south_electrical_north",
    "add_frame",
    "add_trenches",
    "add_trenches90",
    "align_wafer",
    "array",
    "bbox",
    "bend_circular",
    "bend_circular180",
    "bend_circular_heater",
    "bend_circular_all_angle",
    "bend_euler",
    "bend_euler_all_angle",
    "bend_euler180",
    "bend_euler_s",
    "bend_s",
    "bezier",
    "cavity",
    "cdsem_all",
    "cdsem_straight",
    "cdsem_straight_density",
    "cdsem_coupler",
    "cdsem_bend180",
    "circle",
    "coh_rx_single_pol",
    "coh_tx_dual_pol",
    "coh_tx_single_pol",
    "compass",
    "component_sequence",
    "copy_layers",
    "coupler",
    "coupler90",
    "coupler90bend",
    "coupler90circular",
    "coupler_adiabatic",
    "coupler_asymmetric",
    "coupler_bend",
    "coupler_bent",
    "coupler_broadband",
    "coupler_full",
    "coupler_ring",
    "coupler_straight",
    "coupler_straight_asymmetric",
    "coupler_symmetric",
    "cross",
    "crossing",
    "crossing45",
    "crossing_arm",
    "crossing_etched",
    "crossing_from_taper",
    "cutback_2x2",
    "cutback_bend",
    "cutback_bend180",
    "cutback_bend180circular",
    "cutback_bend90",
    "cutback_bend90circular",
    "cutback_component",
    "cutback_component_mirror",
    "cutback_loss",
    "cutback_loss_bend90",
    "cutback_loss_bend180",
    "cutback_loss_mmi1x2",
    "cutback_loss_spirals",
    "cutback_splitter",
    "dbr",
    "dbr_tapered",
    "delay_snake",
    "delay_snake2",
    "delay_snake_sbend",
    "dicing_lane",
    "die",
    "die_bbox",
    "die_with_pads",
    "disk",
    "disk_heater",
    "edge_coupler_array",
    "edge_coupler_array_with_loopback",
    "edge_coupler_silicon",
    "ellipse",
    "ellipse_arc",
    "extend_ports",
    "extend_ports_list",
    "fiber",
    "fiber_array",
    "fiducial_squares",
    "ge_detector_straight_si_contacts",
    "generate_doe",
    "grating_coupler_array",
    "grating_coupler_dual_pol",
    "grating_coupler_elliptical",
    "grating_coupler_elliptical_arbitrary",
    "grating_coupler_elliptical_lumerical",
    "grating_coupler_elliptical_te",
    "grating_coupler_elliptical_tm",
    "grating_coupler_elliptical_trenches",
    "grating_coupler_elliptical_uniform",
    "grating_coupler_loss_fiber_array",
    "grating_coupler_loss_fiber_array4",
    "grating_coupler_rectangular",
    "grating_coupler_rectangular_arbitrary",
    "grating_coupler_te",
    "grating_coupler_tm",
    "grating_coupler_tree",
    "grating_taper_points",
    "grating_tooth_points",
    "greek_cross",
    "greek_cross_with_pads",
    "hline",
    "interdigital_capacitor",
    "litho_calipers",
    "litho_ruler",
    "litho_steps",
    "loop_mirror",
    "loss_deembedding_ch12_34",
    "loss_deembedding_ch13_24",
    "loss_deembedding_ch14_23",
    "mmi",
    "mmi_tapered",
    "mmi1x2",
    "mmi1x2_with_sbend",
    "mmi2x2",
    "mmi2x2_with_sbend",
    "mmi_90degree_hybrid",
    "mode_converter",
    "mzi",
    "mzi1x2_2x2",
    "mzi2x2_2x2",
    "mzi2x2_2x2_phase_shifter",
    "mzi_arm",
    "mzi_arms",
    "mzi_coupler",
    "mzi_lattice",
    "mzi_lattice_mmi",
    "mzi_pads_center",
    "mzi_phase_shifter",
    "mzi_phase_shifter_top_heater_metal",
    "mzi_pin",
    "mzit",
    "mzit_lattice",
    "mzm",
    "nxn",
    "optimal_90deg",
    "optimal_hairpin",
    "optimal_step",
    "pack_doe",
    "pack_doe_grid",
    "pad",
    "pad_array",
    "pad_array0",
    "pad_array180",
    "pad_array270",
    "pad_array90",
    "pad_gsg_open",
    "pad_gsg_short",
    "pad_rectangular",
    "pad_small",
    "pads_shorted",
    "pixel",
    "polarization_splitter_rotator",
    "qrcode",
    "ramp",
    "rectangle",
    "rectangle_with_slits",
    "rectangles",
    "regular_polygon",
    "resistance_meander",
    "resistance_sheet",
    "ring",
    "ring_crow",
    "ring_crow_couplers",
    "ring_double",
    "ring_double_heater",
    "ring_double_pn",
    "ring_single",
    "ring_single_array",
    "ring_single_bend_coupler",
    "ring_single_dut",
    "ring_single_heater",
    "ring_single_pn",
    "seal_ring",
    "seal_ring_segmented",
    "snspd",
    "spiral",
    "spiral_inductor",
    "spiral_double",
    "spiral_racetrack",
    "spiral_racetrack_fixed_length",
    "spiral_racetrack_heater_doped",
    "spiral_racetrack_heater_metal",
    "splitter_chain",
    "splitter_tree",
    "staircase",
    "straight",
    "straight_all_angle",
    "straight_array",
    "straight_heater_doped_rib",
    "straight_heater_doped_strip",
    "straight_heater_meander",
    "straight_heater_meander_doped",
    "straight_heater_metal",
    "straight_heater_metal_90_90",
    "straight_heater_metal_simple",
    "straight_heater_metal_undercut",
    "straight_heater_metal_undercut_90_90",
    "straight_pin",
    "straight_pin_slot",
    "straight_pn",
    "switch_tree",
    "taper",
    "taper2",
    "taper_adiabatic",
    "taper_cross_section",
    "taper_cross_section_linear",
    "taper_cross_section_parabolic",
    "taper_cross_section_sine",
    "taper_from_csv",
    "taper_parabolic",
    "taper_sc_nc",
    "taper_nc_sc",
    "taper_strip_to_ridge",
    "taper_strip_to_ridge_trenches",
    "taper_electrical",
    "terminator",
    "text",
    "text_klayout",
    "text_freetype",
    "text_lines",
    "text_rectangular",
    "text_rectangular_multi_layer",
    "text_rectangular_mini",
    "triangle",
    "triangle2",
    "triangle4",
    "verniers",
    "version_stamp",
    "via",
    "via1",
    "via2",
    "via_chain",
    "via_corner",
    "via_stack",
    "via_stack_heater_m3",
    "via_stack_m1_mtop",
    "via_stack_slab_m1_horizontal",
    "via_stack_heater_mtop",
    "via_stack_heater_mtop_mini",
    "via_stack_slab_m3",
    "via_stack_slab_npp_m3",
    "via_stack_with_offset",
    "via_stack_npp_m1",
    "via_stack_corner45",
    "via_stack_corner45_extended",
    "viac",
    "wafer",
    "wire_corner",
    "wire_corner45",
    "wire_straight",
    "hexagon",
    "octagon",
]

cells = get_cells(sys.modules[__name__])
