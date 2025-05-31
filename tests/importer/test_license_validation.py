# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

import bpy

from io_scene_vrm.importer import license_validation


class TestLicenseValidation(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def setUp(self) -> None:
        bpy.ops.wm.read_homefile(use_empty=True)

    def test_validate_license_url(self) -> None:
        for url, confirmation_required in [
            ("", False),
            ("test", True),
            ("https://example.com", True),
            (
                "https://hub.vroid.com/en/license?allowed_to_use_user=everyone&"
                + "characterization_allowed_user=everyone&"
                + "corporate_commercial_use=allow&credit=unnecessary&"
                + "modification=allow&personal_commercial_use=profit&"
                + "redistribution=allow&sexual_expression=allow&version=1&"
                + "violent_expression=allow",
                False,
            ),
            (
                "https://hub.vroid.com/en/license?allowed_to_use_user=everyone&"
                + "characterization_allowed_user=everyone&"
                + "corporate_commercial_use=allow&credit=unnecessary&"
                + "modification=disallow&personal_commercial_use=profit&"
                + "redistribution=allow&sexual_expression=allow&version=1&"
                + "violent_expression=allow",
                True,
            ),
            ("https://uv-license.com/en/license?utf8=%E2%9C%93&pcu=true", False),
            (
                "https://uv-license.com/en/license?utf8=%E2%9C%93&pcu=true&remarks=true",
                True,
            ),
        ]:
            with self.subTest(url):
                confirmation_props: list[
                    license_validation.LicenseConfirmationRequiredProp
                ] = []
                license_validation.validate_license_url(url, "key", confirmation_props)
                if confirmation_required:
                    self.assertEqual(1, len(confirmation_props))
                else:
                    self.assertEqual([], confirmation_props)
