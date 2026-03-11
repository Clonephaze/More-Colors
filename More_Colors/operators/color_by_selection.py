# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_active_color_attribute, get_masked_color,
)
from .base_operators import BaseColorOperator


class MC_OT_color_by_selection(BaseColorOperator):
    """Colors selected elements one color and unselected another"""

    bl_label = "Color By Selection"
    bl_idname = "morecolors.color_by_selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_color_by_selection_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()
        sel_color = tool.selected_color
        unsel_color = tool.unselected_color
        select_mode = context.tool_settings.mesh_select_mode

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                self._apply(obj, sel_color, unsel_color, mask, select_mode)

        self.report({"INFO"}, "Selection colors applied!")
        return {"FINISHED"}

    @staticmethod
    def _apply(obj, sel_color, unsel_color, mask, select_mode):
        color_attribute = get_active_color_attribute(obj)

        match color_attribute.domain:
            case "CORNER":
                vert_to_loops = build_vertex_loop_map(obj)

                # Build set of selected vertex indices based on select mode
                selected_verts = set()
                if select_mode[0]:  # Vertex
                    for vert in obj.data.vertices:
                        if vert.select:
                            selected_verts.add(vert.index)
                if select_mode[1]:  # Edge
                    for edge in obj.data.edges:
                        if edge.select:
                            selected_verts.update(edge.vertices)
                if select_mode[2]:  # Face
                    for poly in obj.data.polygons:
                        if poly.select:
                            for li in poly.loop_indices:
                                data = color_attribute.data[li]
                                data.color_srgb = get_masked_color(data.color_srgb, sel_color, mask)
                            # Face mode: mark remaining loops as unselected below
                    # In face mode, handle unselected faces
                    if select_mode[2]:
                        for poly in obj.data.polygons:
                            if not poly.select:
                                for li in poly.loop_indices:
                                    data = color_attribute.data[li]
                                    data.color_srgb = get_masked_color(data.color_srgb, unsel_color, mask)
                        obj.data.update()
                        return

                # Vertex/Edge mode: apply per-vertex
                if select_mode[0] or select_mode[1]:
                    for vi in range(len(obj.data.vertices)):
                        color = sel_color if vi in selected_verts else unsel_color
                        for li in vert_to_loops.get(vi, []):
                            data = color_attribute.data[li]
                            data.color_srgb = get_masked_color(data.color_srgb, color, mask)

            case "POINT":
                for vert in obj.data.vertices:
                    color = sel_color if vert.select else unsel_color
                    data = color_attribute.data[vert.index]
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)

        obj.data.update()
