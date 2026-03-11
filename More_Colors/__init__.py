# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from . import operators, property_groups, ui
from .utilities.palette_utilities import register_handlers, unregister_handlers

packages = [property_groups, operators, ui]


def register():
    for package in packages:
        package.register()
    register_handlers()


def unregister():
    unregister_handlers()
    for package in reversed(packages):
        package.unregister()
