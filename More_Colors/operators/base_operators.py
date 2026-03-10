# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator


class BaseOperator(Operator):
    bl_label = ""


class BaseColorOperator(BaseOperator):
    """Base operator for vertex color operations.

    Contains a poll method that prevents using the operator when no mesh is selected.
    """

    @classmethod
    def poll(cls, context):
        return any(obj.type == "MESH" for obj in context.selected_objects)
