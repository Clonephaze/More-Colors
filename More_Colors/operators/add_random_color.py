# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utilities.color_utilities import (
    build_vertex_loop_map, ensure_object_mode,
    get_masked_color, get_random_color, get_active_color_attribute, get_distinct_random_colors
)
from .base_operators import BaseColorOperator


def _build_selected_loops(obj, select_mode):
    """Build set of selected loop indices based on current selection mode."""
    selected = set()
    if select_mode[0]:  # Vertex
        vert_to_loops = build_vertex_loop_map(obj)
        for vert in obj.data.vertices:
            if vert.select:
                selected.update(vert_to_loops.get(vert.index, []))
    if select_mode[1]:  # Edge
        vert_to_loops = build_vertex_loop_map(obj)
        for edge in obj.data.edges:
            if edge.select:
                for vi in edge.vertices:
                    selected.update(vert_to_loops.get(vi, []))
    if select_mode[2]:  # Face
        for poly in obj.data.polygons:
            if poly.select:
                selected.update(poly.loop_indices)
    return selected


class MC_OT_add_random_color(BaseColorOperator):
    """Adds a random color per chosen element (point, vertex, face) for each selected mesh object"""

    bl_label = "Add Random Color"
    bl_idname = "morecolors.add_random_color"
    bl_options = {'REGISTER', 'UNDO'}

    def add_random_color_per_face(self, obj, color_attribute, global_color_settings, random_color_tool,
                                  palette, selected_only=True):
        mask = global_color_settings.get_mask()
        for poly in obj.data.polygons:
            if selected_only and not poly.select:
                continue
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            for loop_index in poly.loop_indices:
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_point(self, obj, color_attribute, global_color_settings, random_color_tool,
                                   palette, selected_only=True):
        vert_to_loops = build_vertex_loop_map(obj)
        mask = global_color_settings.get_mask()
        for vert in obj.data.vertices:
            if selected_only and not vert.select:
                continue
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            for loop_index in vert_to_loops.get(vert.index, []):
                data = color_attribute.data[loop_index]
                data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_vertex(self, obj, color_attribute, global_color_settings,
                                    random_color_tool, palette, select_mode):
        mask = global_color_settings.get_mask()
        if select_mode is not None:
            selected_loops = _build_selected_loops(obj, select_mode)
        else:
            selected_loops = None
        for idx, data in enumerate(color_attribute.data):
            if selected_loops is not None and idx not in selected_loops:
                continue
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_island(self, obj, color_attribute, global_color_settings, random_color_tool,
                                    palette, selected_only=True):
        def get_connected_faces(face_index, visited_faces, adjacency_list):
            connected_faces = {face_index}
            faces_to_check = [face_index]

            while faces_to_check:
                current_face = faces_to_check.pop()
                for neighbor in adjacency_list[current_face]:
                    if neighbor not in visited_faces:
                        visited_faces.add(neighbor)
                        connected_faces.add(neighbor)
                        faces_to_check.append(neighbor)

            return connected_faces

        # Determine which faces to consider
        if selected_only:
            candidate_faces = {
                i for i, poly in enumerate(obj.data.polygons) if poly.select
            }
        else:
            candidate_faces = set(range(len(obj.data.polygons)))

        # Build edge_key -> face list from candidate faces
        edge_to_faces = {}
        for poly_index in candidate_faces:
            poly = obj.data.polygons[poly_index]
            for edge_key in poly.edge_keys:
                edge_to_faces.setdefault(edge_key, []).append(poly_index)

        # Build adjacency from edge_to_faces
        adjacency_list = {i: [] for i in candidate_faces}
        for face_list in edge_to_faces.values():
            for i in range(len(face_list)):
                for j in range(i + 1, len(face_list)):
                    adjacency_list[face_list[i]].append(face_list[j])
                    adjacency_list[face_list[j]].append(face_list[i])

        mask = global_color_settings.get_mask()
        visited_faces = set()
        for face_index in candidate_faces:
            if face_index not in visited_faces:
                connected_faces = get_connected_faces(face_index, visited_faces, adjacency_list)
                random_color = get_random_color(random_color_tool.color_mode, palette=palette)

                for connected_face_index in connected_faces:
                    poly = obj.data.polygons[connected_face_index]
                    for loop_index in poly.loop_indices:
                        data = color_attribute.data[loop_index]
                        data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

    def add_random_color_per_face_set(self, obj, color_attribute, global_color_settings, random_color_tool,
                                      palette, selected_only=True):
        face_set_attr = obj.data.attributes.get(".sculpt_face_set")
        if face_set_attr is None:
            return False

        # Group face indices by face set ID
        face_sets = {}
        for i, poly in enumerate(obj.data.polygons):
            if selected_only and not poly.select:
                continue
            fs_id = face_set_attr.data[i].value
            face_sets.setdefault(fs_id, []).append(i)

        mask = global_color_settings.get_mask()
        for face_indices in face_sets.values():
            random_color = get_random_color(random_color_tool.color_mode, palette=palette)
            for fi in face_indices:
                poly = obj.data.polygons[fi]
                for loop_index in poly.loop_indices:
                    data = color_attribute.data[loop_index]
                    data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)
        return True

    def execute(self, context):
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings
        in_edit = context.mode == 'EDIT_MESH'
        select_mode = context.tool_settings.mesh_select_mode if in_edit else None

        palette = None
        if random_color_tool.random_palette and len(random_color_tool.random_palette.colors) > 0:
            palette = [
                (*pc.color, 1.0) for pc in random_color_tool.random_palette.colors
            ]

        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if random_color_tool.element_type == "Object":
            self._apply_per_object(mesh_objects, global_color_settings, random_color_tool, palette)
        else:
            self._apply_per_element(
                mesh_objects, global_color_settings, random_color_tool, palette, select_mode)

        self.report({"INFO"}, "Random vertex color applied!")
        return {"FINISHED"}

    def _apply_per_object(self, mesh_objects, global_color_settings, random_color_tool, palette):
        colors = get_distinct_random_colors(
            len(mesh_objects), random_color_tool.color_mode, palette=palette
        )
        mask = global_color_settings.get_mask()

        for obj, color in zip(mesh_objects, colors):
            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                for data in color_attribute.data:
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)

                obj.data.update()

    def _apply_per_element(self, mesh_objects, global_color_settings, random_color_tool,
                           palette, select_mode):
        for obj in mesh_objects:
            with ensure_object_mode(obj):
                self._color_single_object(
                    obj, global_color_settings, random_color_tool, palette, select_mode)

    def _color_single_object(self, obj, global_color_settings, random_color_tool,
                             palette, select_mode):
        color_attribute = get_active_color_attribute(obj)
        selected_only = select_mode is not None

        match color_attribute.domain:
            # On point domain color is stored per point, not per corner,
            # so element_type selection doesn't apply
            case "POINT":
                mask = global_color_settings.get_mask()
                for p in obj.data.vertices:
                    if selected_only and not p.select:
                        continue
                    data = color_attribute.data[p.index]
                    random_color = get_random_color(random_color_tool.color_mode, palette=palette)
                    data.color_srgb = get_masked_color(data.color_srgb, random_color, mask)

            case "CORNER":
                match random_color_tool.element_type:
                    case "Point":
                        self.add_random_color_per_point(
                            obj, color_attribute, global_color_settings,
                            random_color_tool, palette, selected_only)
                    case "Vertex":
                        self.add_random_color_per_vertex(
                            obj, color_attribute, global_color_settings,
                            random_color_tool, palette, select_mode)
                    case "Face":
                        self.add_random_color_per_face(
                            obj, color_attribute, global_color_settings,
                            random_color_tool, palette, selected_only)
                    case "Island":
                        self.add_random_color_per_island(
                            obj, color_attribute, global_color_settings,
                            random_color_tool, palette, selected_only)
                    case "FaceSet":
                        if not self.add_random_color_per_face_set(
                            obj, color_attribute, global_color_settings,
                            random_color_tool, palette, selected_only
                        ):
                            self.report({"ERROR"}, "No face sets found. Use Sculpt Mode to create face sets.")
                            return

        obj.data.update()


class MC_OT_add_random_color_by_object(BaseColorOperator):
    """Assigns a unique random color to each selected mesh object"""

    bl_label = "Add Random Color Per Object"
    bl_idname = "morecolors.add_random_color_by_object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        random_color_tool = scene.more_colors_random_color_tool
        global_color_settings = scene.more_colors_global_color_settings

        palette = None
        if random_color_tool.random_palette and len(random_color_tool.random_palette.colors) > 0:
            palette = [
                (*pc.color, 1.0) for pc in random_color_tool.random_palette.colors
            ]

        mesh_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        colors = get_distinct_random_colors(
            len(mesh_objects), random_color_tool.color_mode, palette=palette
        )
        mask = global_color_settings.get_mask()

        for obj, color in zip(mesh_objects, colors):
            with ensure_object_mode(obj):
                color_attribute = get_active_color_attribute(obj)
                for data in color_attribute.data:
                    data.color_srgb = get_masked_color(data.color_srgb, color, mask)
                obj.data.update()

        self.report({"INFO"}, "Random color per object applied!")
        return {"FINISHED"}
