"""Spyder plugin entrypoint for the image viewer."""

from __future__ import annotations

from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow
from spyder.api.plugin_registration.decorators import on_plugin_available
from spyder.api.plugins import Plugins, SpyderDockablePlugin

from .widgets.image_viewer import ImageViewerWidget
from .utils.array_validator import is_image_array


class ImageViewerPlugin(SpyderDockablePlugin):
    """Spyder plugin for viewing NumPy arrays as images."""

    # Variable Explorer integration switches.
    ENABLE_VARIABLE_EXPLORER_CONTEXT_INTEGRATION = True
    ENABLE_VARIABLE_EXPLORER_INTEGRATION = True

    NAME = "image_viewer"
    REQUIRES = [Plugins.VariableExplorer]
    OPTIONAL = []
    TABIFY = [Plugins.VariableExplorer]
    WIDGET_CLASS = ImageViewerWidget

    CONF_SECTION = NAME
    CONF_FILE = True
    CONF_DEFAULTS = [
        (
            NAME,
            {
                "max_width": 512,
                "max_height": 512,
                "show_pixel_values": False,
            },
        ),
    ]

    @staticmethod
    def get_name():
        return "Image Viewer"

    @staticmethod
    def get_description():
        return "Lightweight NumPy image viewer for Spyder."

    @classmethod
    def get_icon(cls):
        return QIcon()

    def on_initialize(self):
        """Initialize plugin state."""
        self._variable_explorer = None
        self._ve_widget = None
        self._open_in_image_viewer_action = None
        self._menu_action_registered = False
        self._popup_windows = []
        self._popup_counter = 0

    @on_plugin_available(plugin=Plugins.VariableExplorer)
    def on_variable_explorer_available(self):
        """Create widget and connect Variable Explorer signals."""
        if not self.ENABLE_VARIABLE_EXPLORER_INTEGRATION:
            return

        variable_explorer = self.get_plugin(Plugins.VariableExplorer)
        self._variable_explorer = variable_explorer
        self._ve_widget = (
            variable_explorer.get_widget()
            if hasattr(variable_explorer, "get_widget")
            else None
        )

        # Different Spyder versions expose different event surfaces.
        candidates = [variable_explorer]
        if hasattr(variable_explorer, "get_widget"):
            candidates.append(variable_explorer.get_widget())

        for source in candidates:
            for signal_name in ("sig_var_selected", "sig_var_changed"):
                signal = getattr(source, signal_name, None)
                if signal is not None:
                    signal.connect(self.on_var_event)

        self._install_variable_explorer_context_action()

    def on_mainwindow_visible(self):
        """Ensure context action is present once all panes are visible."""
        self._install_variable_explorer_context_action()

    def _install_variable_explorer_context_action(self):
        """Add custom context action while preserving default Spyder actions."""
        if not self.ENABLE_VARIABLE_EXPLORER_CONTEXT_INTEGRATION:
            return

        if self._ve_widget is None:
            return

        context_menu = getattr(self._ve_widget, "context_menu", None)
        if context_menu is None:
            return

        if self._open_in_image_viewer_action is None:
            self._open_in_image_viewer_action = self._ve_widget.create_action(
                "open_in_image_viewer_action",
                "Open in Image Viewer",
                icon=self._ve_widget.create_icon("imshow"),
                triggered=self.open_selected_variable_in_popup,
            )
            self._open_in_image_viewer_action.setToolTip(
                "Open selected variable in Image Viewer popup"
            )

        if not self._menu_action_registered:
            from spyder.plugins.variableexplorer.widgets.main_widget import (
                VariableExplorerContextMenuSections,
            )

            self._ve_widget.add_item_to_menu(
                self._open_in_image_viewer_action,
                menu=context_menu,
                section=VariableExplorerContextMenuSections.View,
            )
            self._menu_action_registered = True
            
            # Connect to menu aboutToShow to check if selected var is valid image array
            context_menu.aboutToShow.connect(self._on_context_menu_about_to_show)

    def _on_context_menu_about_to_show(self):
        """Show/hide action based on whether selected variable is a valid image array."""
        if self._open_in_image_viewer_action is None or self._ve_widget is None:
            return
        
        # Try to get currently selected variable
        editor = getattr(self._ve_widget, "_current_editor", None)
        if editor is None:
            self._open_in_image_viewer_action.setVisible(False)
            return
        
        index = editor.currentIndex()
        if not index.isValid():
            self._open_in_image_viewer_action.setVisible(False)
            return
        
        # Get variable name from model
        if getattr(editor, "proxy_model", None) is not None:
            source_index = editor.proxy_model.mapToSource(index)
            var_name = editor.source_model.get_key(source_index)
        else:
            var_name = editor.source_model.get_key(index)
        
        # Get variable value
        try:
            value = editor.get_value(var_name)
        except Exception:
            self._open_in_image_viewer_action.setVisible(False)
            return
        
        # Show action only if value is a valid image array
        is_valid = is_image_array(value)
        self._open_in_image_viewer_action.setVisible(is_valid)

    def on_var_event(self, *args, **kwargs):
        """Handle Variable Explorer updates with safe argument parsing."""
        widget = self.get_widget()

        # Best effort extraction to remain compatible across Spyder versions.
        variable = kwargs.get("value") or kwargs.get("variable")
        name = kwargs.get("name", "")

        if variable is None and args:
            for arg in reversed(args):
                if hasattr(arg, "shape") and hasattr(arg, "dtype"):
                    variable = arg
                    break
            if not name and args:
                for arg in args:
                    if isinstance(arg, str):
                        name = arg
                        break

        widget.update_from_variable_explorer(variable=variable, name=name)

    def open_selected_variable_in_popup(self):
        """Open currently selected Variable Explorer item in popup viewer."""
        if self._ve_widget is None:
            return

        editor = getattr(self._ve_widget, "_current_editor", None)
        if editor is None:
            return

        index = editor.currentIndex()
        if not index.isValid():
            return

        if getattr(editor, "proxy_model", None) is not None:
            source_index = editor.proxy_model.mapToSource(index)
            var_name = editor.source_model.get_key(source_index)
        else:
            var_name = editor.source_model.get_key(index)

        try:
            value = editor.get_value(var_name)
        except Exception:
            return

        # Keep dock widget behavior as-is.
        widget = self.get_widget()
        widget.set_array(value, array_name=var_name)

        # Open a fresh popup every time to support multiple concurrent viewers.
        self._open_array_in_new_popup(value, var_name)

    def _open_array_in_new_popup(self, value, var_name: str):
        """Create and show a new popup window with an independent viewer."""
        self._popup_counter += 1

        popup = QMainWindow(self.main)
        popup.setAttribute(Qt.WA_DeleteOnClose, True)
        popup.setWindowTitle(f"Image Viewer - {var_name}" if var_name else "Image Viewer")
        popup.resize(900, 700)

        viewer_name = f"image_viewer_popup_{self._popup_counter}"
        popup_widget = ImageViewerWidget(name=viewer_name, plugin=self, parent=popup)
        popup.setCentralWidget(popup_widget)
        popup_widget.set_array(value, array_name=var_name)

        self._popup_windows.append(popup)
        popup.destroyed.connect(lambda _=None, w=popup: self._on_popup_destroyed(w))

        popup.show()
        popup.raise_()
        popup.activateWindow()

    def _on_popup_destroyed(self, popup_window):
        """Drop closed popup reference to avoid retaining dead windows."""
        self._popup_windows = [w for w in self._popup_windows if w is not popup_window]
