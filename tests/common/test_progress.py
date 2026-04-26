# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase
from unittest.mock import MagicMock, patch

from io_scene_vrm.common.progress import Progress, create_progress


class TestProgress(TestCase):
    def test_create_progress(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        # Initial state
        Progress.active_progress_uuid = None

        with create_progress(context, show_progress=True) as progress:
            self.assertEqual(Progress.active_progress_uuid, progress.uuid)
            context.window_manager.progress_begin.assert_called_once_with(0, 9999)

        self.assertIsNone(Progress.active_progress_uuid)
        context.window_manager.progress_end.assert_called_once()

    def test_create_progress_no_show(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None

        with create_progress(context, show_progress=False) as progress:
            self.assertEqual(Progress.active_progress_uuid, progress.uuid)
            context.window_manager.progress_begin.assert_not_called()

        self.assertIsNone(Progress.active_progress_uuid)
        context.window_manager.progress_end.assert_not_called()

    def test_create_progress_nested(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None

        with create_progress(context, show_progress=True) as progress1:
            self.assertEqual(Progress.active_progress_uuid, progress1.uuid)
            context.window_manager.progress_begin.assert_called_once_with(0, 9999)
            context.window_manager.progress_begin.reset_mock()

            with create_progress(context, show_progress=True) as progress2:
                self.assertEqual(Progress.active_progress_uuid, progress2.uuid)
                # progress_begin should not be called for nested progress if already
                # active
                context.window_manager.progress_begin.assert_not_called()

            self.assertEqual(Progress.active_progress_uuid, progress1.uuid)
            context.window_manager.progress_end.assert_not_called()

        self.assertIsNone(Progress.active_progress_uuid)
        context.window_manager.progress_end.assert_called_once()

    def test_progress_update_v4(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with patch("io_scene_vrm.common.progress.bpy") as mock_bpy:
            mock_bpy.app.version = (4, 2, 0)
            with create_progress(context, show_progress=True) as progress:
                progress.update(0.5)
                # math.floor(0.5 * 99) = 49
                context.window_manager.progress_update.assert_called_once_with(49)

    def test_progress_update_v5(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with patch("io_scene_vrm.common.progress.bpy") as mock_bpy:
            mock_bpy.app.version = (5, 0, 0)
            with create_progress(context, show_progress=True) as progress:
                progress.update(0.5)
                # 0.5 * 9999 = 4999.5
                context.window_manager.progress_update.assert_called_once_with(4999.5)

    def test_progress_update_clamping(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with patch("io_scene_vrm.common.progress.bpy") as mock_bpy:
            mock_bpy.app.version = (4, 2, 0)
            with create_progress(context, show_progress=True) as progress:
                progress.update(1.5)
                context.window_manager.progress_update.assert_called_with(99)
                progress.update(-0.5)
                context.window_manager.progress_update.assert_called_with(0)

    def test_progress_update_no_show(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with create_progress(context, show_progress=False) as progress:
            progress.update(0.5)
            context.window_manager.progress_update.assert_not_called()

    def test_progress_update_mismatched_uuid(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with create_progress(context, show_progress=True) as progress:
            Progress.active_progress_uuid = "mismatched"
            with patch("io_scene_vrm.common.progress._logger") as mock_logger:
                progress.update(0.5)
                mock_logger.error.assert_called_once()
                context.window_manager.progress_update.assert_not_called()

    def test_partial_progress(self) -> None:
        context = MagicMock()
        context.window_manager = MagicMock()

        Progress.active_progress_uuid = None
        with patch("io_scene_vrm.common.progress.bpy") as mock_bpy:
            mock_bpy.app.version = (4, 2, 0)
            with create_progress(context, show_progress=True) as progress:
                progress.update(0.2)
                context.window_manager.progress_update.reset_mock()

                partial = progress.partial_progress(0.6)
                partial.update(0.5)
                # ratio = 0.2 + 0.5 * (0.6 - 0.2) = 0.2 + 0.5 * 0.4 = 0.2 + 0.2 = 0.4
                # progress_value = math.floor(0.4 * 99) = 39
                context.window_manager.progress_update.assert_called_once_with(39)
