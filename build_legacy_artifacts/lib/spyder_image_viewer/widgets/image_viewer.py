"""Dock widget that renders NumPy arrays as images."""

from __future__ import annotations

import numpy as np
from qtpy.QtCore import QEvent, QRectF, Qt, Signal
from qtpy.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStyle,
    QStyleOption,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from spyder.api.widgets.main_widget import PluginMainWidget

from ..utils.array_validator import is_image_array, normalize_image_array


class _FastImageLabel(QLabel):
    """Image label that paints only the visible source area at current zoom."""

    def __init__(self, text: str):
        super().__init__(text)
        self._base_pixmap = None
        self._zoom_factor = 1.0
        self.setAttribute(Qt.WA_StyledBackground, True)

    def set_base_pixmap(self, pixmap):
        self._base_pixmap = pixmap
        if pixmap is not None:
            self.setText("")
        self.update()

    def set_zoom_factor(self, zoom_factor: float):
        self._zoom_factor = max(0.01, float(zoom_factor))
        self.update()

    def pixmap(self):
        """Compatibility shim used by overlay logic."""
        return self._base_pixmap

    def paintEvent(self, event):
        if self._base_pixmap is None:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        try:
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

            target_rect = QRectF(event.rect())
            zoom = self._zoom_factor
            src_rect = QRectF(
                target_rect.left() / zoom,
                target_rect.top() / zoom,
                max(1.0, target_rect.width() / zoom),
                max(1.0, target_rect.height() / zoom),
            )
            painter.drawPixmap(target_rect, self._base_pixmap, src_rect)
        finally:
            painter.end()


class _OverlayWidget(QWidget):
    """Transparent viewport overlay for pixel-value painting."""

    def __init__(self, viewer: "ImageViewerWidget", parent: QWidget):
        super().__init__(parent)
        self.viewer = viewer
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_AlwaysStackOnTop, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            self.viewer._paint_overlay(painter)
        finally:
            painter.end()
        super().paintEvent(event)


class ImageViewerWidget(PluginMainWidget):
    """Lightweight image viewer for NumPy arrays."""

    sig_image_loaded = Signal(str)

    def __init__(self, name: str, plugin, parent=None):
        super().__init__(name, plugin, parent=parent)
        self.current_array = None
        self.display_array = None
        self.current_array_name = ""
        self.original_pixmap = None
        self._pixel_value_zoom_required = 3000
        self._pixel_value_max_drawn_cells = 20000
        self._temp_zoom_previous_value = None
        self._zoom_anchor_override = None
        self._placeholder_style = "background-color: #f0f0f0; border: 1px solid #ccc;"
        self._image_style = "border: 1px solid #ccc;"
        self.setup_ui()

    def get_title(self) -> str:
        return "Image Viewer"

    def setup(self) -> None:
        """Create plugin actions if needed."""
        return

    def update_actions(self) -> None:
        """Update exposed actions; none for now."""
        return

    def setup_ui(self) -> None:
        """Create the dock widget UI."""
        widget = QWidget()
        root_layout = QVBoxLayout()

        self.image_label = _FastImageLabel("Select a NumPy image array in Variable Explorer")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.image_label.setStyleSheet(self._placeholder_style)
        self.image_label.setMinimumHeight(240)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self._on_viewport_changed)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_viewport_changed)
        self.scroll_area.viewport().setMouseTracking(True)
        self.scroll_area.viewport().installEventFilter(self)
        self.overlay_widget = _OverlayWidget(self, self.scroll_area.viewport())
        self.overlay_widget.setGeometry(self.scroll_area.viewport().rect())
        self.overlay_widget.show()
        root_layout.addWidget(self.scroll_area)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Zoom:"))

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(3000)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        controls.addWidget(self.zoom_slider)

        self.zoom_value_label = QLabel("100%")
        controls.addWidget(self.zoom_value_label)

        self.temp_zoom_button = QPushButton("Show Pixels")
        self.temp_zoom_button.setCheckable(True)
        self.temp_zoom_button.toggled.connect(self._on_temp_zoom_toggled)
        self.temp_zoom_button.setToolTip("Temporarily switch to 3000%; turn off to restore the previous zoom.")
        controls.addWidget(self.temp_zoom_button)

        self.channel_label = QLabel("Channel:")
        self.channel_label.setVisible(False)
        controls.addWidget(self.channel_label)

        self.channel_combo = QComboBox()
        self.channel_combo.setVisible(False)
        self.channel_combo.currentIndexChanged.connect(self._on_channel_changed)
        controls.addWidget(self.channel_combo)

        self.color_order_label = QLabel("Order:")
        self.color_order_label.setVisible(False)
        controls.addWidget(self.color_order_label)

        self.color_order_combo = QComboBox()
        self.color_order_combo.setVisible(False)
        self.color_order_combo.addItems(["RGB", "BGR"])
        self.color_order_combo.currentIndexChanged.connect(self._on_color_order_changed)
        controls.addWidget(self.color_order_combo)

        root_layout.addLayout(controls)

        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Courier", 9))
        self.info_label.setWordWrap(True)
        root_layout.addWidget(self.info_label)

        widget.setLayout(root_layout)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        self.setLayout(layout)

    def set_array(self, array: np.ndarray, array_name: str = "") -> None:
        """Set and render a new ndarray."""
        if not is_image_array(array):
            self.image_label.setText("Not a valid image array")
            self.image_label.setStyleSheet(self._placeholder_style)
            self.image_label.setMinimumHeight(240)
            self.info_label.setText("")
            self.current_array = None
            self.display_array = None
            self.original_pixmap = None
            self.image_label.set_base_pixmap(None)
            self.current_array_name = ""
            self._hide_channel_selector()
            self._hide_color_order_selector()
            return

        self.current_array = np.asarray(array)
        self.current_array_name = array_name
        self.update_display()

        if array_name:
            self.sig_image_loaded.emit(array_name)

    def clear(self) -> None:
        """Clear current image from the viewer."""
        self.current_array = None
        self.display_array = None
        self.current_array_name = ""
        self.original_pixmap = None
        self.image_label.set_base_pixmap(None)
        self.image_label.clear()
        self.image_label.setText("Select a NumPy image array in Variable Explorer")
        self.image_label.setStyleSheet(self._placeholder_style)
        self.image_label.setMinimumHeight(240)
        self.image_label.adjustSize()
        self.info_label.setText("")
        self._hide_channel_selector()
        self._hide_color_order_selector()
        self.overlay_widget.update()

    def update_display(self) -> None:
        """Render the current image array."""
        if self.current_array is None:
            return

        self.display_array = normalize_image_array(self.current_array)
        if self.display_array.ndim == 2:
            self._hide_channel_selector()
            self._hide_color_order_selector()
        elif self.display_array.ndim == 3 and self.display_array.shape[2] >= 1:
            channel_count = int(self.display_array.shape[2])
            self._update_channel_selector([str(i) for i in range(channel_count)])
            self._update_color_order_visibility()
        else:
            self.image_label.set_base_pixmap(None)
            self.image_label.setText("Unsupported image shape")
            self.display_array = None
            self._hide_channel_selector()
            self._hide_color_order_selector()
            return

        self._refresh_original_pixmap_from_selection()
        self.display_pixmap()
        self._update_info()

    def display_pixmap(self) -> None:
        """Display image using current zoom value."""
        if self.original_pixmap is None:
            return

        zoom_factor = self.zoom_slider.value() / 100.0
        target_width = max(1, int(self.original_pixmap.width() * zoom_factor))
        target_height = max(1, int(self.original_pixmap.height() * zoom_factor))

        self.image_label.set_base_pixmap(self.original_pixmap)
        self.image_label.setStyleSheet(self._image_style)
        self.image_label.setMinimumHeight(0)
        self.image_label.set_zoom_factor(zoom_factor)
        self.image_label.resize(target_width, target_height)
        self.overlay_widget.update()

    def on_zoom_changed(self, value: int) -> None:
        """Update zoom indicator and redraw image."""
        zoom_anchor = self._zoom_anchor_override
        self._zoom_anchor_override = None
        if zoom_anchor is None:
            zoom_anchor = self._compute_viewport_center_anchor()

        if self.temp_zoom_button.isChecked() and value != self._pixel_value_zoom_required:
            self._temp_zoom_previous_value = None
            self.temp_zoom_button.blockSignals(True)
            self.temp_zoom_button.setChecked(False)
            self.temp_zoom_button.blockSignals(False)

        self.zoom_value_label.setText(f"{value}%")
        self.display_pixmap()
        self._restore_viewport_center_from_anchor(zoom_anchor)

    def _on_viewport_changed(self, _value: int) -> None:
        """Refresh only viewport overlay when scrolling."""
        if self.original_pixmap is None:
            return
        self.overlay_widget.update()

    def _compute_viewport_center_anchor(self):
        """Return center anchor with image-relative and viewport coordinates."""
        if self.original_pixmap is None:
            return None

        view_w = max(1, self.image_label.width())
        view_h = max(1, self.image_label.height())
        viewport = self.scroll_area.viewport()
        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()

        anchor_vx = viewport.width() / 2.0
        anchor_vy = viewport.height() / 2.0
        anchor_img_x = hbar.value() + anchor_vx
        anchor_img_y = vbar.value() + anchor_vy

        return {
            "rx": anchor_img_x / float(view_w),
            "ry": anchor_img_y / float(view_h),
            "vx": anchor_vx,
            "vy": anchor_vy,
        }

    def _restore_viewport_center_from_anchor(self, anchor) -> None:
        """Restore viewport so the same image point stays under the same viewport point."""
        if anchor is None:
            return

        view_w = max(1, self.image_label.width())
        view_h = max(1, self.image_label.height())
        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()

        target_img_x = float(anchor["rx"]) * view_w
        target_img_y = float(anchor["ry"]) * view_h
        target_h = int(round(target_img_x - float(anchor["vx"])))
        target_v = int(round(target_img_y - float(anchor["vy"])))

        hbar.setValue(max(hbar.minimum(), min(hbar.maximum(), target_h)))
        vbar.setValue(max(vbar.minimum(), min(vbar.maximum(), target_v)))

    def _apply_mouse_wheel_zoom(self, delta: int) -> bool:
        """Apply nonlinear wheel zoom and keep viewport center stable."""
        if self.original_pixmap is None or delta == 0:
            return False

        notches = int(delta / 120)
        if notches == 0:
            notches = 1 if delta > 0 else -1

        current = float(self.zoom_slider.value())
        # Nonlinear wheel zoom: adjust in sqrt space, then square back.
        # This makes low zoom changes fine-grained and high zoom changes larger.
        sqrt_zoom = current ** 0.5
        sqrt_step = 0.8
        new_sqrt_zoom = max(1.0, sqrt_zoom + notches * sqrt_step)
        new_value = int(round(new_sqrt_zoom * new_sqrt_zoom))
        new_value = max(self.zoom_slider.minimum(), min(self.zoom_slider.maximum(), new_value))

        if new_value == int(current):
            return False

        self.zoom_slider.setValue(new_value)
        return True

    def _compute_anchor_from_viewport_pos(self, pos):
        """Return image-relative anchor from viewport position when valid."""
        if self.original_pixmap is None:
            return None

        view_w = self.image_label.width()
        view_h = self.image_label.height()
        if view_w <= 0 or view_h <= 0:
            return None

        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()
        img_x = hbar.value() + int(pos.x())
        img_y = vbar.value() + int(pos.y())

        if not (0 <= img_x < view_w and 0 <= img_y < view_h):
            return None

        return {
            "rx": img_x / float(view_w),
            "ry": img_y / float(view_h),
            "vx": float(pos.x()),
            "vy": float(pos.y()),
        }

    def _image_coords_from_viewport_pos(self, pos):
        """Convert a viewport position to integer image pixel coordinates."""
        if self.display_array is None:
            return None

        display_w = self.image_label.width()
        display_h = self.image_label.height()
        if display_w <= 0 or display_h <= 0:
            return None

        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()
        img_pos_x = hbar.value() + int(pos.x())
        img_pos_y = vbar.value() + int(pos.y())

        if not (0 <= img_pos_x < display_w and 0 <= img_pos_y < display_h):
            return None

        arr = np.asarray(self.display_array)
        img_h, img_w = arr.shape[:2]
        px = self._display_coord_to_pixel_index(img_pos_x, display_w, img_w)
        py = self._display_coord_to_pixel_index(img_pos_y, display_h, img_h)
        return px, py

    @staticmethod
    def _display_coord_to_pixel_index(display_pos: int, display_len: int, image_len: int) -> int:
        """Map display-space coordinate to source pixel index using overlay rounding rules."""
        if image_len <= 1 or display_len <= 1:
            return 0

        cell = display_len / float(image_len)
        guess = int(display_pos / cell)
        guess = max(0, min(image_len - 1, guess))

        start = max(0, guess - 2)
        end = min(image_len - 1, guess + 2)
        for idx in range(start, end + 1):
            top = int(round(idx * cell))
            bottom = int(round((idx + 1) * cell))
            if top <= display_pos < bottom:
                return idx

        return guess

    def _get_brightness_at(self, x: int, y: int):
        """Return tooltip value at pixel coordinates in display array."""
        if self.display_array is None:
            return None

        arr = np.asarray(self.display_array)
        if arr.ndim == 2:
            return arr[y, x]

        if arr.ndim == 3:
            channel_index = self._get_selected_channel_index()
            if channel_index is not None:
                return arr[y, x, channel_index]

            # Full-color mode: show all channel values in tooltip.
            return arr[y, x, :]

        return None

    def _update_hover_tooltip(self, event) -> None:
        """Show pixel coordinate and brightness tooltip while hovering image."""
        pos = event.position() if hasattr(event, "position") else event.pos()
        coords = self._image_coords_from_viewport_pos(pos)
        if coords is None:
            QToolTip.hideText()
            return

        x, y = coords
        value = self._get_brightness_at(x, y)
        if value is None:
            QToolTip.hideText()
            return

        value_text = self._format_pixel_value(value)
        value_label = "Value"
        arr_value = np.asarray(value)
        if arr_value.ndim == 0:
            value_label = "Intensity"

        tooltip_text = f"Coord: ({x}, {y})\n{value_label}: {value_text}"
        global_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
        QToolTip.showText(global_pos, tooltip_text, self.scroll_area.viewport())

    def _on_channel_changed(self, _index: int) -> None:
        """Refresh image/overlay when selected channel changes."""
        self._update_color_order_visibility()
        self._refresh_original_pixmap_from_selection()
        self.display_pixmap()

    def _on_color_order_changed(self, _index: int) -> None:
        """Refresh full-color display when RGB/BGR order changes."""
        self._refresh_original_pixmap_from_selection()
        self.display_pixmap()

    def _on_temp_zoom_toggled(self, checked: bool) -> None:
        """Temporarily switch to 2500% and restore previous zoom when disabled."""
        if checked:
            if self.zoom_slider.value() != self._pixel_value_zoom_required:
                self._temp_zoom_previous_value = self.zoom_slider.value()
                self.zoom_slider.setValue(self._pixel_value_zoom_required)
            else:
                self._temp_zoom_previous_value = None
            return

        if self._temp_zoom_previous_value is not None:
            previous = self._temp_zoom_previous_value
            self._temp_zoom_previous_value = None
            self.zoom_slider.setValue(previous)

    def _update_channel_selector(self, labels) -> None:
        """Show channel selector and keep current index when possible."""
        previous = self.channel_combo.currentIndex()
        self.channel_combo.blockSignals(True)
        self.channel_combo.clear()
        self.channel_combo.addItem("full")
        self.channel_combo.addItems(labels)
        max_index = len(labels)
        if 0 <= previous <= max_index:
            self.channel_combo.setCurrentIndex(previous)
        else:
            self.channel_combo.setCurrentIndex(0)
        self.channel_combo.blockSignals(False)
        self.channel_label.setVisible(True)
        self.channel_combo.setVisible(True)

    def _hide_channel_selector(self) -> None:
        """Hide channel selector when image is single-channel."""
        self.channel_combo.blockSignals(True)
        self.channel_combo.clear()
        self.channel_combo.addItem("Gray")
        self.channel_combo.setCurrentIndex(0)
        self.channel_combo.blockSignals(False)
        self.channel_label.setVisible(False)
        self.channel_combo.setVisible(False)

    def _update_color_order_visibility(self) -> None:
        """Show RGB/BGR selector only for 3D arrays with 3+ channels in full mode."""
        if self.display_array is None:
            self._hide_color_order_selector()
            return

        arr = np.asarray(self.display_array)
        selected = self._get_selected_channel_index()
        visible = arr.ndim == 3 and arr.shape[2] >= 3 and selected is None
        self.color_order_label.setVisible(visible)
        self.color_order_combo.setVisible(visible)

    def _hide_color_order_selector(self) -> None:
        """Hide RGB/BGR selector and reset to default order."""
        self.color_order_combo.blockSignals(True)
        self.color_order_combo.setCurrentIndex(0)
        self.color_order_combo.blockSignals(False)
        self.color_order_label.setVisible(False)
        self.color_order_combo.setVisible(False)

    def _get_color_order(self) -> str:
        """Return current full-color channel order."""
        if self.color_order_combo.currentIndex() == 1:
            return "BGR"
        return "RGB"

    def _refresh_original_pixmap_from_selection(self) -> None:
        """Build the base pixmap from current array and channel selection."""
        if self.display_array is None:
            self.original_pixmap = None
            return

        arr = np.asarray(self.display_array)
        q_image = None

        if arr.ndim == 2:
            q_image = self._grayscale_to_qimage(arr)
        elif arr.ndim == 3 and arr.shape[2] >= 1:
            selected = self._get_selected_channel_index()
            if selected is None:
                if arr.shape[2] >= 3:
                    color_arr = arr[:, :, :3]
                    if self._get_color_order() == "BGR":
                        color_arr = color_arr[:, :, ::-1]
                    q_image = self._rgb_to_qimage(color_arr)
                else:
                    q_image = self._grayscale_to_qimage(arr[:, :, 0])
            else:
                q_image = self._grayscale_to_qimage(arr[:, :, selected])

        self.original_pixmap = QPixmap.fromImage(q_image) if q_image is not None else None

    def _get_selected_channel_index(self):
        """Return selected channel index; None means original color mode."""
        if self.display_array is None:
            return None

        arr = np.asarray(self.display_array)
        if arr.ndim != 3:
            return None

        combo_index = self.channel_combo.currentIndex()
        if combo_index <= 0:
            return None

        return max(0, min(combo_index - 1, arr.shape[2] - 1))

    def eventFilter(self, watched, event):
        """Keep overlay geometry synced with viewport size."""
        if watched is self.scroll_area.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                pos = event.position() if hasattr(event, "position") else event.pos()
                self._zoom_anchor_override = self._compute_anchor_from_viewport_pos(pos)
                if self._apply_mouse_wheel_zoom(event.angleDelta().y()):
                    event.accept()
                    return True

                self._zoom_anchor_override = None
                return False

        if watched is self.scroll_area.viewport() and event.type() == QEvent.MouseMove:
            self._update_hover_tooltip(event)

        if watched is self.scroll_area.viewport() and event.type() == QEvent.Leave:
            QToolTip.hideText()

        if watched is self.scroll_area.viewport() and event.type() == QEvent.Resize:
            self.overlay_widget.setGeometry(self.scroll_area.viewport().rect())
        return super().eventFilter(watched, event)

    def _update_info(self) -> None:
        """Show shape/type/range summary for current array."""
        if self.current_array is None:
            self.info_label.setText("")
            return

        arr = self.current_array
        shape_str = " x ".join(str(dim) for dim in arr.shape)
        dtype_str = str(arr.dtype)
        min_val = float(np.nanmin(arr))
        max_val = float(np.nanmax(arr))
        mean_val = float(np.nanmean(arr))

        if arr.ndim == 2:
            channel_info = "Grayscale"
        elif arr.ndim == 3 and arr.shape[2] == 3:
            channel_info = "RGB"
        elif arr.ndim == 3 and arr.shape[2] == 4:
            channel_info = "RGBA"
        elif arr.ndim == 3:
            channel_info = f"{arr.shape[2]} channels"
        else:
            channel_info = "Unknown"

        name_line = f"Name: {self.current_array_name}\n" if self.current_array_name else ""
        info = (
            f"{name_line}"
            f"Shape: {shape_str}\n"
            f"Type: {dtype_str}\n"
            f"Range: [{min_val:.3f}, {max_val:.3f}]\n"
            f"Mean: {mean_val:.3f}\n"
            f"Channels: {channel_info}"
        )
        self.info_label.setText(info)

    @staticmethod
    def _grayscale_to_qimage(arr: np.ndarray) -> QImage:
        """Convert HxW uint8 image to QImage."""
        contiguous = np.ascontiguousarray(arr)
        height, width = contiguous.shape
        bytes_per_line = width
        image = QImage(
            contiguous.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_Grayscale8,
        )
        return image.copy()

    @staticmethod
    def _rgb_to_qimage(arr: np.ndarray) -> QImage:
        """Convert HxWx3 uint8 image to QImage."""
        contiguous = np.ascontiguousarray(arr)
        height, width, _ = contiguous.shape
        bytes_per_line = width * 3
        image = QImage(
            contiguous.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        )
        return image.copy()

    @staticmethod
    def _rgba_to_qimage(arr: np.ndarray) -> QImage:
        """Convert HxWx4 uint8 image to QImage."""
        contiguous = np.ascontiguousarray(arr)
        height, width, _ = contiguous.shape
        bytes_per_line = width * 4
        image = QImage(
            contiguous.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGBA8888,
        )
        return image.copy()

    def _paint_overlay(self, painter: QPainter) -> None:
        """Paint pixel-value overlay directly on the viewport."""
        pixmap = self.image_label.pixmap()
        if pixmap is None or self.display_array is None:
            return

        display_width = self.image_label.width()
        display_height = self.image_label.height()
        if display_width <= 0 or display_height <= 0:
            return

        if self.zoom_slider.value() != self._pixel_value_zoom_required:
            return

        display_arr = np.asarray(self.display_array)
        is_full_mode = display_arr.ndim == 3 and self._get_selected_channel_index() is None

        arr = None
        if is_full_mode:
            # In full mode, draw only grid (no pixel text).
            height, width = display_arr.shape[:2]
        else:
            arr = self._get_overlay_channel_array()
            if arr is None:
                return
            height, width = arr.shape

        cell_w = display_width / float(width)
        cell_h = display_height / float(height)
        if min(cell_w, cell_h) < 14.0:
            return

        x_start, x_end, y_start, y_end = self._visible_cell_bounds(
            display_width,
            display_height,
            width,
            height,
            cell_w,
            cell_h,
        )
        drawn_cells = max(0, x_end - x_start) * max(0, y_end - y_start)
        if drawn_cells == 0 or drawn_cells > self._pixel_value_max_drawn_cells:
            return

        x_offset = self.scroll_area.horizontalScrollBar().value()
        y_offset = self.scroll_area.verticalScrollBar().value()

        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, False)

        font = QFont("Courier", max(3, min(9, int(min(cell_w, cell_h) * 0.14))))
        painter.setFont(font)

        grid_pen = QPen(QColor(220, 220, 220, 130))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        for y in range(y_start, y_end + 1):
            y_pos = int(round(y * cell_h - y_offset))
            x0 = int(round(x_start * cell_w - x_offset))
            x1 = int(round(x_end * cell_w - x_offset))
            painter.drawLine(x0, y_pos, x1, y_pos)
        for x in range(x_start, x_end + 1):
            x_pos = int(round(x * cell_w - x_offset))
            y0 = int(round(y_start * cell_h - y_offset))
            y1 = int(round(y_end * cell_h - y_offset))
            painter.drawLine(x_pos, y0, x_pos, y1)

        if arr is None:
            return

        for y in range(y_start, y_end):
            top = int(round(y * cell_h - y_offset))
            bottom = int(round((y + 1) * cell_h - y_offset))
            h_px = max(1, bottom - top)
            for x in range(x_start, x_end):
                left = int(round(x * cell_w - x_offset))
                right = int(round((x + 1) * cell_w - x_offset))
                w_px = max(1, right - left)

                value_text = self._format_pixel_value(arr[y, x])
                if not value_text:
                    continue

                painter.setPen(QColor(0, 0, 0))
                painter.drawText(left + 1, top + 1, w_px, h_px, Qt.AlignCenter, value_text)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(left, top, w_px, h_px, Qt.AlignCenter, value_text)

    def _get_overlay_channel_array(self):
        """Return a 2D array used for pixel-value overlay."""
        if self.display_array is None:
            return None

        arr = np.asarray(self.display_array)
        if arr.ndim == 2:
            return arr

        if arr.ndim == 3:
            channel_index = self._get_selected_channel_index()
            if channel_index is None:
                return None
            return arr[:, :, channel_index]

        return None

    def _visible_cell_bounds(
        self,
        pixmap_width: int,
        pixmap_height: int,
        img_width: int,
        img_height: int,
        cell_w: float,
        cell_h: float,
    ):
        """Compute visible image-cell bounds from scrollbars/viewport."""
        hbar = self.scroll_area.horizontalScrollBar()
        vbar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()

        x0 = max(0, hbar.value())
        y0 = max(0, vbar.value())
        x1 = min(pixmap_width, x0 + viewport.width())
        y1 = min(pixmap_height, y0 + viewport.height())

        x_start = max(0, int(np.floor(x0 / cell_w)))
        y_start = max(0, int(np.floor(y0 / cell_h)))
        x_end = min(img_width, int(np.ceil(x1 / cell_w)))
        y_end = min(img_height, int(np.ceil(y1 / cell_h)))

        return x_start, x_end, y_start, y_end

    @staticmethod
    def _format_pixel_value(value) -> str:
        """Format pixel values for text overlay."""
        arr = np.asarray(value)

        if arr.ndim == 0:
            scalar = arr.item()
            if isinstance(scalar, (float, np.floating)):
                return f"{float(scalar):.3g}"
            if isinstance(scalar, (int, np.integer)):
                return str(int(scalar))
            return str(scalar)

        flat = arr.ravel()
        if flat.size >= 1:
            parts = []
            for item in flat:
                if isinstance(item, (float, np.floating)):
                    parts.append(f"{float(item):.2g}")
                else:
                    parts.append(str(int(item)))
            return "(" + ",".join(parts) + ")"

        return ""

    def update_from_variable_explorer(self, variable=None, name: str = "") -> None:
        """Compatibility hook for variable explorer signal handlers."""
        if variable is None:
            return

        if is_image_array(variable):
            self.set_array(variable, array_name=name)
