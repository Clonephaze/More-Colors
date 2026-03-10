# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import EnumProperty, FloatVectorProperty
from bpy.types import PropertyGroup


_ELEMENT_TYPE_BASE = [
    ("Point", "Per Point", "Points are shared across faces", "DECORATE", 1),
    ("Vertex", "Per Vertex", "Vertices are unique per face", "VERTEXSEL", 2),
    ("Face", "Per Face", "Faces are well... faces", "SNAP_FACE", 3),
    ("Island", "Per Island", "All mesh parts that are connected", "FACE_MAPS", 4),
]

_ELEMENT_TYPE_WITH_OBJECT = _ELEMENT_TYPE_BASE + [
    ("Object", "Per Object", "Each selected object gets a unique random color", "OBJECT_DATA", 5),
]

# Cache prevents garbage collection of dynamic enum items
_element_type_cache = _ELEMENT_TYPE_BASE


def _get_element_type_items(self, context):
    global _element_type_cache
    if context:
        mesh_count = sum(1 for obj in context.selected_objects if obj.type == "MESH")
        if mesh_count > 1:
            _element_type_cache = _ELEMENT_TYPE_WITH_OBJECT
            return _element_type_cache
    _element_type_cache = _ELEMENT_TYPE_BASE
    return _element_type_cache


class RandomColorToolProperties(PropertyGroup):
    element_type: EnumProperty(
        name="Element",
        description="Elements to generate colors on",
        items=_get_element_type_items,
    )

    color_mode: EnumProperty(
        name="Random Color Mode",
        description="Color generation method",
        items=[
            ("RGBA", "RGB", "Randomizes color by RGBA values."),
            ("Hue", "Hue", "Randomizes color only by hue. Saturation and alpha will be 1, lightness will be 0.5"),
            ("Palette", "Palette", "Randomly selects colors from the 4-color palette"),
        ]
    )

    palette_color_1: FloatVectorProperty(
        name="Palette Color 1",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.050, 0.078, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_2: FloatVectorProperty(
        name="Palette Color 2",
        description="Choose a color",
        subtype="COLOR",
        default=(1.000, 0.743, 0.050, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_3: FloatVectorProperty(
        name="Palette Color 3",
        description="Choose a color",
        subtype="COLOR",
        default=(0.498, 0.788, 0.039, 1.000),
        min=0,
        max=1,
        size=4,
    )

    palette_color_4: FloatVectorProperty(
        name="Palette Color 4",
        description="Choose a color",
        subtype="COLOR",
        default=(0.038, 0.490, 0.768, 1.000),
        min=0,
        max=1,
        size=4,
    )
