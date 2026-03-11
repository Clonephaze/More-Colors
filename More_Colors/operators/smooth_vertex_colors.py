# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode, get_active_color_attribute
)
from .base_operators import BaseColorOperator


class MC_OT_smooth_vertex_colors(BaseColorOperator):
    """Smooths vertex colors by averaging with neighboring vertices"""

    bl_label = "Smooth Colors"
    bl_idname = "morecolors.smooth_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tool = context.scene.more_colors_smooth_tool
        mask = context.scene.more_colors_global_color_settings.get_mask()

        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue
            with ensure_object_mode(obj):
                self._smooth_object(obj, tool.iterations, tool.factor, mask)

        self.report({"INFO"}, "Vertex colors smoothed!")
        return {"FINISHED"}

    @staticmethod
    def _smooth_object(obj, iterations, factor, mask):
        mesh = obj.data
        color_attribute = get_active_color_attribute(obj)
        num_verts = len(mesh.vertices)

        # Build vertex adjacency from edges
        neighbors = [[] for _ in range(num_verts)]
        for edge in mesh.edges:
            v0, v1 = edge.vertices
            neighbors[v0].append(v1)
            neighbors[v1].append(v0)

        # Read current per-vertex colors depending on domain
        match color_attribute.domain:
            case "CORNER":
                vert_to_loops = build_vertex_loop_map(obj)
                # Average all loop colors per vertex to get one color per vert
                colors = []
                for vi in range(num_verts):
                    loops = vert_to_loops.get(vi, [])
                    if loops:
                        r = sum(color_attribute.data[li].color_srgb[0] for li in loops) / len(loops)
                        g = sum(color_attribute.data[li].color_srgb[1] for li in loops) / len(loops)
                        b = sum(color_attribute.data[li].color_srgb[2] for li in loops) / len(loops)
                        a = sum(color_attribute.data[li].color_srgb[3] for li in loops) / len(loops)
                        colors.append([r, g, b, a])
                    else:
                        colors.append([0.0, 0.0, 0.0, 1.0])
            case "POINT":
                vert_to_loops = None
                colors = [list(color_attribute.data[vi].color_srgb) for vi in range(num_verts)]

        # Iterative smoothing
        for _ in range(iterations):
            new_colors = []
            for vi in range(num_verts):
                nbs = neighbors[vi]
                if not nbs:
                    new_colors.append(colors[vi][:])
                    continue
                # Average neighbor colors
                avg = [0.0, 0.0, 0.0, 0.0]
                for ni in nbs:
                    for ch in range(4):
                        avg[ch] += colors[ni][ch]
                for ch in range(4):
                    avg[ch] /= len(nbs)
                # Lerp original toward average by factor
                blended = [
                    colors[vi][ch] + (avg[ch] - colors[vi][ch]) * factor
                    for ch in range(4)
                ]
                new_colors.append(blended)
            colors = new_colors

        # Write back with mask
        match color_attribute.domain:
            case "CORNER":
                for vi in range(num_verts):
                    for li in vert_to_loops.get(vi, []):
                        old = color_attribute.data[li].color_srgb
                        color_attribute.data[li].color_srgb = [
                            colors[vi][ch] if mask[ch] else old[ch]
                            for ch in range(4)
                        ]
            case "POINT":
                for vi in range(num_verts):
                    old = color_attribute.data[vi].color_srgb
                    color_attribute.data[vi].color_srgb = [
                        colors[vi][ch] if mask[ch] else old[ch]
                        for ch in range(4)
                    ]

        obj.data.update()
