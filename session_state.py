# 会话级运行时设置 / Session-scoped runtime settings.
import copy


DEFAULT_SETTINGS = {
    "autosave_enabled": True,
    "autosave_interval_minutes": 10,
    "use_custom_cache_directory": False,
    "cache_directory": "",
    "clean_cache_on_exit": True,
    "max_undo_steps": 50,
    "default_panel_width": 1280,
    "default_panel_height": 720,
    "debug_mode": False,
    "default_note_font_family": "Verdana",
    "default_note_font_size": 18,
    "default_note_text_color": "#F2F2F2",
    "default_note_background_color": "#202124",
    "default_note_transparent_background": False,
    "auto_enter_edit_mode_for_new_text": True,
    "continue_checklist_on_new_line": True,
    "nodemark_link_style": "Hyperlink text",
    "nodemark_missing_behavior": "Show warning",
    "nodemark_backdrop_color": "#2F4F6F",
}


_runtime_settings = copy.deepcopy(DEFAULT_SETTINGS)


def default_settings():
    return copy.deepcopy(DEFAULT_SETTINGS)


def current_settings():
    return copy.deepcopy(_runtime_settings)


def update_settings(settings):
    global _runtime_settings
    merged = copy.deepcopy(DEFAULT_SETTINGS)
    merged.update(settings or {})
    _runtime_settings = merged
    return current_settings()


def reset_settings():
    return update_settings(DEFAULT_SETTINGS)
