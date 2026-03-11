# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_active_color_attribute,
)
from .base_operators import BaseColorOperator

_WHITE = (1, 1, 1, 1)


class MC_OT_reset_color(BaseColorOperator):
    """Resets vertex colors to white (selection-aware in edit mode)"""

    bl_label = "Reset Vertex Colors"
    bl_idname = "morecolors.reset_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                self._reset_colors(obj, color_attribute, select_mode)
                obj.data.update()

        self.report({"INFO"}, "Vertex colors have been reset!")
        return {"FINISHED"}

    @staticmethod
    def _reset_colors(obj, color_attribute, select_mode):
        # Object-mode fast path: reset everything
        if select_mode is None:
            for data in color_attribute.data:
                data.color_srgb = _WHITE
            return

        match color_attribute.domain:
            case "CORNER":
                vert_to_loops = build_vertex_loop_map(obj)

                if select_mode[0]:
                    for vert in obj.data.vertices:
                        if vert.select:
                            for li in vert_to_loops.get(vert.index, []):
                                color_attribute.data[li].color_srgb = _WHITE

                if select_mode[1]:
                    for edge in obj.data.edges:
                        if edge.select:
                            for vi in edge.vertices:
                                for li in vert_to_loops.get(vi, []):
                                    color_attribute.data[li].color_srgb = _WHITE

                if select_mode[2]:
                    for poly in obj.data.polygons:
                        if poly.select:
                            for li in poly.loop_indices:
                                color_attribute.data[li].color_srgb = _WHITE

            case "POINT":
                for vert in obj.data.vertices:
                    if vert.select:
                        color_attribute.data[vert.index].color_srgb = _WHITE
