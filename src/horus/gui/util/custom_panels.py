# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2015 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import wx._core
from collections import OrderedDict

from horus.util import profile, resources


class ExpandableCollection(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.expandable_panels = OrderedDict()

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.vbox)
        self.Layout()

    def add_panel(self, name, panel):
        panel = panel(self)
        panel.content.Disable()
        panel.set_expand_callback(self._expand_callback)
        self.expandable_panels.update({name: panel})
        self.vbox.Add(panel, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 5)

    def init_panels_layout(self):
        values = self.expandable_panels.values()
        if len(values) > 0:
            for panel in values:
                panel.hide_content()
            values[0].show_content()

    def _expand_callback(self, selected_panel):
        for panel in self.expandable_panels.values():
            panel.hide_content()
        selected_panel.show_content()
        self.Layout()

    # Engine callbacks
    def update_callbacks(self):
        for panel in self.expandable_panels.values():
            panel.content.update_callbacks()

    def enable_content(self):
        for panel in self.expandable_panels.values():
            panel.content.Enable()

    def disable_content(self):
        for panel in self.expandable_panels.values():
            panel.content.Disable()

    def update_from_profile(self):
        for panel in self.expandable_panels.values():
            panel.content.update_from_profile()


class ExpandablePanel(wx.Panel):

    def __init__(self, parent, title="", has_undo=True, has_restore=True):
        wx.Panel.__init__(self, parent, size=(-1, -1))

        # Elements
        self.expand_callback = None
        self.undo_objects = []
        self.title = title
        self.title_text = TitleText(self, title, bold=True)
        self.has_undo = has_undo
        self.has_restore = has_restore
        if self.has_undo:
            self.undo_button = wx.BitmapButton(
                self, wx.NewId(),
                wx.Bitmap(resources.get_path_for_image("undo.png"), wx.BITMAP_TYPE_ANY))
            self.undo_button.Disable()
        if self.has_restore:
            self.restore_button = wx.BitmapButton(
                self, wx.NewId(),
                wx.Bitmap(resources.get_path_for_image("restore.png"), wx.BITMAP_TYPE_ANY))

        self.content = ControlCollection(self, self.append_undo, self.release_undo)
        self.SetBackgroundColour(wx.GREEN)

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.title_text, 1, wx.ALIGN_CENTER_VERTICAL)
        if self.has_undo:
            self.hbox.Add(
                self.undo_button, 0, wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        if self.has_restore:
            self.hbox.Add(
                self.restore_button, 0, wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.vbox.Add(self.hbox, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)
        self.vbox.Add(self.content, 1, wx.ALL ^ wx.TOP ^ wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(self.vbox)
        self.Layout()

        # Events
        if self.has_undo:
            self.undo_button.Bind(wx.EVT_BUTTON, self.on_undo_button_clicked)
        if self.has_restore:
            self.restore_button.Bind(wx.EVT_BUTTON, self.on_restore_button_clicked)
        self.title_text.title.Bind(wx.EVT_LEFT_DOWN, self.on_title_clicked)

        # Initialize
        self.add_controls()
        self.update_callbacks()

    def add_control(self, _name, _type, tooltip=None):
        self.content.add_control(_name, _type, tooltip)

    def get_control(self, _name):
        return self.content[_name]

    def update_callback(self, _name, _callback):
        self.content.update_callback(_name, _callback)

    def add_controls(self):
        raise NotImplementedError

    def update_callbacks(self):
        raise NotImplementedError

    def on_selected(self):
        pass

    def set_expand_callback(self, expand_callback):
        self.expand_callback = expand_callback

    def on_title_clicked(self, event):
        if self.expand_callback is not None:
            self.expand_callback(self)
            self.on_selected()

    def on_undo_button_clicked(self, event):
        if self.undo():
            self.undo_button.Enable()
        else:
            self.undo_button.Disable()

    def show_content(self):
        self.content.Show()
        if self.has_undo:
            self.undo_button.Show()
        if self.has_restore:
            self.restore_button.Show()

    def hide_content(self):
        self.content.Hide()
        if self.has_undo:
            self.undo_button.Hide()
        if self.has_restore:
            self.restore_button.Hide()

    def append_undo(self, _object):
        if self.has_undo:
            self.undo_objects.append(_object)

    def release_undo(self, undo=False, restore=False):
        if self.has_undo and undo:
            self.undo_button.Enable()
        if self.has_restore and restore:
            self.restore_button.Enable()

    def undo(self):
        if len(self.undo_objects) > 0:
            object_to_undo = self.undo_objects.pop()
            object_to_undo.undo()
        return len(self.undo_objects) > 0

    def on_restore_button_clicked(self, event):
        dlg = wx.MessageDialog(
            self,
            _("This will reset all section settings to defaults.\n"
              "Unless you have saved your current profile, all section settings will be lost!\n"
              "Do you really want to reset?"), self.title, wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal() == wx.ID_YES
        dlg.Destroy()
        if result:
            self.restore_button.Disable()
            self.content.reset_profile()
            if self.has_undo:
                del self.undo_objects[:]
                self.undo_button.Disable()

    def enable_restore(self, value):
        if hasattr(self, 'restore_button'):
            if value:
                self.restore_button.Enable()
            else:
                self.restore_button.Disable()


class TitleText(wx.Panel):

    def __init__(self, parent, title, bold=True, hand_cursor=True):
        wx.Panel.__init__(self, parent)

        # Elements
        self.title = wx.StaticText(self, label=title)
        if bold:
            font_weight = wx.FONTWEIGHT_BOLD
        else:
            font_weight = wx.FONTWEIGHT_NORMAL
        self.title.SetFont((wx.Font(wx.SystemSettings.GetFont(
            wx.SYS_ANSI_VAR_FONT).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, font_weight)))
        self.line = wx.StaticLine(self)

        if hand_cursor:
            self.title.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
            self.line.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.title, 0, wx.ALL ^ wx.BOTTOM | wx.EXPAND, 10)
        vbox.Add(self.line, 1, wx.ALL ^ wx.BOTTOM | wx.EXPAND, 5)
        self.SetSizer(vbox)
        self.Layout()


class ControlCollection(wx.Panel):

    def __init__(self, parent, append_undo_callback=None, release_undo_callback=None):
        wx.Panel.__init__(self, parent, size=(100, 100))

        self.SetBackgroundColour(wx.RED)

        # Elements
        self.control_panels = OrderedDict()
        self.append_undo_callback = append_undo_callback
        self.release_undo_callback = release_undo_callback

        # Layout
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.vbox)
        self.Layout()

    def __getitem__(self, key):
        return self.control_panels[key]

    def add_control(self, _name, _type, tooltip=None):
        control = _type(self, _name, tooltip)
        control.set_undo_callbacks(self.append_undo_callback, self.release_undo_callback)
        self.control_panels.update({_name: control})
        self.vbox.Add(control, 0, wx.BOTTOM | wx.EXPAND, 5)

    def update_callback(self, _name, _callback):
        self.control_panels[_name].set_engine_callback(_callback)

    def reset_profile(self):
        for control in self.control_panels.values():
            control.reset_profile()

    def enable(self, _name):
        self.items[_name].Enable()

    def disable(self, _name):
        self.items[_name].Disable()

    def update_from_profile(self):
        for control in self.control_panels.values():
            control.update_from_profile()

    def show_item(self, _name):
        self.control_panels[_name].Show()
        self.Layout()

    def hide_item(self, _name):
        self.control_panels[_name].Hide()
        self.Layout()


class ControlPanel(wx.Panel):

    def __init__(self, parent, name, tooltip=None):
        wx.Panel.__init__(self, parent)
        self.name = name
        self.setting = profile.settings.get_setting(self.name)
        if tooltip:
            self.SetToolTip(wx.ToolTip(tooltip))

        self.control = None
        self.undo_values = []
        self.engine_callback = None
        self.append_undo_callback = None
        self.release_undo_callback = None

    def set_engine_callback(self, engine_callback=None):
        self.engine_callback = engine_callback

    def set_undo_callbacks(self, append_undo_callback, release_undo_callback):
        self.append_undo_callback = append_undo_callback
        self.release_undo_callback = release_undo_callback

    def append_undo(self):
        if self.append_undo_callback is not None:
            self.append_undo_callback(self)
            self.undo_values.append(profile.settings[self.name])

    def release_undo(self):
        if self.release_undo_callback is not None:
            self.release_undo_callback(undo=True, restore=True)

    def release_restore(self):
        if self.release_undo_callback is not None:
            self.release_undo_callback(restore=True)

    def undo(self):
        if len(self.undo_values) > 0:
            value = self.undo_values.pop()
            self.update_to_profile(value)
            self.control.SetValue(value)
            self.set_engine(value)

    def reset_profile(self):
        profile.settings.reset_to_default(self.name)
        self.update_from_profile()
        del self.undo_values[:]

    def update_from_profile(self):
        value = profile.settings[self.name]
        # TODO:
        if self.control is not None and \
           not isinstance(self.control, wx.Button) and \
           not isinstance(self.control, wx.ToggleButton):
            self.control.SetValue(value)
            self.set_engine(value)

    def update_to_profile(self, value):
        profile.settings[self.name] = value

    def set_engine(self, value):
        if self.engine_callback is not None:
            self.engine_callback(value)


class Slider(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        self.flag_first_move = True

        # Elements
        self.label = wx.StaticText(self, label=self.setting._label, size=(130, -1))
        self.control = wx.Slider(self, value=profile.settings[name],
                                 minValue=profile.settings.get_min_value(name),
                                 maxValue=profile.settings.get_max_value(name),
                                 size=(150, -1),
                                 style=wx.SL_LABELS)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_COMMAND_SCROLL_LINEUP, self._on_slider)
        self.control.Bind(wx.EVT_COMMAND_SCROLL_LINEDOWN, self._on_slider)
        self.control.Bind(wx.EVT_SCROLL_THUMBRELEASE, self._on_slider_released)
        self.control.Bind(wx.EVT_SCROLL_THUMBTRACK, self._on_slider_tracked)

    def _on_slider(self, event):
        self.append_undo()
        self.release_undo()
        value = self.control.GetValue()
        self.update_to_profile(value)
        self.set_engine(value)

    def _on_slider_released(self, event):
        self.flag_first_move = True
        self.release_undo()
        self.update_to_profile(self.control.GetValue())

    def _on_slider_tracked(self, event):
        if self.flag_first_move:
            self.append_undo()
            self.flag_first_move = False
        self.set_engine(self.control.GetValue())


class ComboBox(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        choices = self.setting._possible_values
        _choices = [_(i) for i in choices]

        self.key_dict = dict(zip(_choices, choices))

        # Elements
        label = wx.StaticText(self, label=self.setting._label, size=(130, -1))
        self.control = wx.ComboBox(self, wx.ID_ANY,
                                   value=_(profile.settings[self.name]),
                                   choices=_choices,
                                   size=(150, -1),
                                   style=wx.CB_READONLY)

        self.control.SetValue_original = self.control.SetValue
        self.control.SetValue = self.SetValue_overwrite

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_COMBOBOX, self._on_combo_box_changed)

    def SetValue_overwrite(self, value):
        self.control.SetValue_original(str(value))

    def _on_combo_box_changed(self, event):
        value = self.key_dict[self.control.GetValue()]
        self.update_to_profile(value)
        self.set_engine(value)
        self.release_restore()


class CheckBox(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        label = wx.StaticText(self, label=self.setting._label, size=(130, -1))
        self.control = wx.CheckBox(self, size=(150, -1))

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_CHECKBOX, self._on_check_box_changed)

    def _on_check_box_changed(self, event):
        value = self.control.GetValue()
        self.update_to_profile(value)
        self.set_engine(value)
        self.release_restore()


class RadioButton(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        label = wx.StaticText(self, label=self.setting._label)
        self.control = wx.RadioButton(self, style=wx.ALIGN_RIGHT)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.TOP | wx.RIGHT | wx.EXPAND, 15)
        hbox.Add(self.control, 1, wx.TOP | wx.EXPAND, 16)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_RADIOBUTTON, self._on_radio_button_changed)

    def _on_radio_button_changed(self, event):
        value = self.control.GetValue()
        self.update_to_profile(value)
        self.set_engine(value)
        self.release_restore()


class TextBox(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        label = wx.StaticText(self, size=(140, -1), label=self.setting._label)
        self.control = wx.TextCtrl(self, size=(120, -1), style=wx.TE_RIGHT)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_KILL_FOCUS, self._on_text_box_changed)

    def _on_text_box_changed(self, event):
        value = self.control.GetValue()
        self.update_to_profile(value)
        self.set_engine(value)
        self.release_restore()


class FloatTextBox(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        label = wx.StaticText(self, size=(140, -1), label=self.setting._label)
        self.control = wx.TextCtrl(self, size=(120, -1), style=wx.TE_RIGHT)
        self.control.SetValue_original = self.control.SetValue
        self.control.SetValue = self.SetValue_overwrite
        self.control.GetValue_original = self.control.GetValue
        self.control.GetValue = self.GetValue_overwrite
        self.control.SetValue(profile.settings[self.name])

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox.AddStretchSpacer()
        hbox.Add(self.control, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_KILL_FOCUS, self._on_text_box_lost_focus)

    def SetValue_overwrite(self, value):
        self.control.SetValue_original(str(value))

    def GetValue_overwrite(self):
        try:
            value = float(self.control.GetValue_original())
        except:
            value = profile.settings[self.name]
            self.control.SetValue(value)
            return value
        else:
            self.control.SetValue(value)
            return value

    def _on_text_box_lost_focus(self, event):
        value = self.control.GetValue()
        self.update_to_profile(value)
        self.set_engine(value)
        self.release_restore()


class FloatTextBoxArray(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)


class Button(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        self.control = wx.Button(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_BUTTON, self._on_button_clicked)

    def _on_button_clicked(self, event):
        if self.engine_callback is not None:
            self.engine_callback()


class CallbackButton(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        self.control = wx.Button(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_BUTTON, self._on_button_clicked)

    def _on_button_clicked(self, event):
        if self.engine_callback is not None:
            self.control.Disable()
            self.waitCursor = wx.BusyCursor()
            self.engine_callback(lambda r: wx.CallAfter(self._on_finish_callback, r))

    def _on_finish_callback(self, ret):
        self.control.Enable()
        del self.waitCursor


class ToggleButton(ControlPanel):

    def __init__(self, parent, name, engine_callback=None):
        ControlPanel.__init__(self, parent, name, engine_callback)

        # Elements
        self.control = wx.ToggleButton(self, label=self.setting._label)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.control, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        self.SetSizer(hbox)
        self.Layout()

        # Events
        self.control.Bind(wx.EVT_TOGGLEBUTTON, self._on_button_toggle)

    def _on_button_toggle(self, event):
        if self.engine_callback is not None:
            if event.IsChecked():
                function = 0
            else:
                function = 1

            if self.engine_callback[function] is not None:
                self.engine_callback[function]()
