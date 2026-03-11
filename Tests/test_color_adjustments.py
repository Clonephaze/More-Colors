# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for the color adjustments math helpers.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_repo_root = _tests_dir.parent
_addon_root = _repo_root / "More_Colors"
for p in (_tests_dir, _repo_root, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import numpy as np

from More_Colors.operators.color_adjustments import (
    _apply_brightness_contrast,
    _apply_hue_saturation,
    _apply_levels,
    _hsv_to_rgb,
    _rgb_to_hsv,
)


class TestApplyLevels(unittest.TestCase):
    """Tests for the _apply_levels helper."""

    def test_identity(self):
        """Default parameters produce no change."""
        rgb = np.array([[0.0, 0.25, 0.5], [0.75, 1.0, 0.1]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 1.0, 0.0, 1.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_invert_via_output(self):
        """Swapping output black/white inverts the value."""
        rgb = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 1.0, 1.0, 0.0)
        np.testing.assert_array_almost_equal(result, [[1.0, 0.5, 0.0]], decimal=5)

    def test_input_range_clamp(self):
        """Input black/white remaps and clamps the range."""
        rgb = np.array([[0.0, 0.25, 0.5, 0.75, 1.0]], dtype=np.float32)
        result = _apply_levels(rgb, 0.25, 0.75, 1.0, 0.0, 1.0)
        self.assertAlmostEqual(float(result[0, 0]), 0.0, places=4)
        self.assertAlmostEqual(float(result[0, 2]), 0.5, places=4)
        self.assertAlmostEqual(float(result[0, 4]), 1.0, places=4)

    def test_gamma(self):
        """Gamma > 1 lightens midtones."""
        rgb = np.array([[0.25, 0.5, 0.75]], dtype=np.float32)
        result = _apply_levels(rgb, 0.0, 1.0, 2.0, 0.0, 1.0)
        self.assertGreater(float(result[0, 0]), 0.25)
        self.assertGreater(float(result[0, 1]), 0.5)


class TestApplyBrightnessContrast(unittest.TestCase):
    """Tests for _apply_brightness_contrast."""

    def test_identity(self):
        rgb = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.0, 0.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_brightness_offset(self):
        rgb = np.array([[0.5, 0.5, 0.5]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.1, 0.0)
        np.testing.assert_array_almost_equal(result, [[0.6, 0.6, 0.6]], decimal=5)

    def test_contrast_increases_spread(self):
        rgb = np.array([[0.25, 0.5, 0.75]], dtype=np.float32)
        result = _apply_brightness_contrast(rgb, 0.0, 1.0)
        # Contrast=1 → factor=2, so (x-0.5)*2+0.5
        np.testing.assert_array_almost_equal(result, [[0.0, 0.5, 1.0]], decimal=5)


class TestRgbHsvRoundTrip(unittest.TestCase):
    """Tests for _rgb_to_hsv and _hsv_to_rgb."""

    def test_round_trip(self):
        rgb = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.5],
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
        ], dtype=np.float32)
        result = _hsv_to_rgb(_rgb_to_hsv(rgb))
        np.testing.assert_array_almost_equal(result, rgb, decimal=5)

    def test_red_hue(self):
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 0]), 0.0, places=4)
        self.assertAlmostEqual(float(hsv[0, 1]), 1.0, places=4)
        self.assertAlmostEqual(float(hsv[0, 2]), 1.0, places=4)

    def test_green_hue(self):
        rgb = np.array([[0.0, 1.0, 0.0]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 0]), 1.0 / 3.0, places=4)

    def test_grey_has_zero_saturation(self):
        rgb = np.array([[0.5, 0.5, 0.5]], dtype=np.float32)
        hsv = _rgb_to_hsv(rgb)
        self.assertAlmostEqual(float(hsv[0, 1]), 0.0, places=4)


class TestApplyHueSaturation(unittest.TestCase):
    """Tests for _apply_hue_saturation."""

    def test_identity(self):
        rgb = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 0.5, 1.0, 1.0)
        np.testing.assert_array_almost_equal(result, rgb, decimal=4)

    def test_desaturate(self):
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 0.5, 0.0, 1.0)
        # Fully desaturated red → grey
        self.assertAlmostEqual(float(result[0, 0]), float(result[0, 1]), places=4)
        self.assertAlmostEqual(float(result[0, 1]), float(result[0, 2]), places=4)

    def test_hue_shift_180(self):
        """Shifting hue by 0.5 (180°) turns red to cyan."""
        rgb = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        result = _apply_hue_saturation(rgb, 1.0, 1.0, 1.0)
        # hue_shift=1.0 → +0.5 from centre → red→cyan
        self.assertAlmostEqual(float(result[0, 0]), 0.0, places=3)
        self.assertGreater(float(result[0, 1]), 0.9)
        self.assertGreater(float(result[0, 2]), 0.9)


if __name__ == "__main__":
    unittest.main()
