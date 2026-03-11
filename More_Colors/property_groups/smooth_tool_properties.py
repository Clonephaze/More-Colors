# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import FloatProperty, IntProperty
from bpy.types import PropertyGroup


class SmoothToolProperties(PropertyGroup):
    iterations: IntProperty(
        name="Iterations",
        description="Number of smoothing passes",
        default=1,
        min=1,
        max=50,
    )

    factor: FloatProperty(
        name="Factor",
        description="Blend strength per pass (0 = no change, 1 = full neighbor average)",
        default=0.5,
        min=0.0,
        max=1.0,
    )
