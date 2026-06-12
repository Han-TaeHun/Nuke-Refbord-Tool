# 세션 범위 런타임 설정
import copy
import json
import os
from pathlib import Path


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


def _settings_directory() -> Path:
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA")
        return (Path(base_dir) if base_dir else Path.home()) / "NukeRefBoard"
    return Path.home() / ".nuke" / "NukeRefBoard"


def settings_file_path() -> Path:
    return _settings_directory() / "settings.json"


def default_settings():
    return copy.deepcopy(DEFAULT_SETTINGS)


def _load_settings_from_disk():
    file_path = settings_file_path()
    if not file_path.exists():
        return default_settings()
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return default_settings()
    merged = default_settings()
    merged.update(payload)
    return merged


def _save_settings_to_disk(settings):
    file_path = settings_file_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")


_runtime_settings = _load_settings_from_disk()


def current_settings():
    return copy.deepcopy(_runtime_settings)


def update_settings(settings, persist=True):
    global _runtime_settings
    merged = default_settings()
    merged.update(settings or {})
    _runtime_settings = merged
    if persist:
        try:
            _save_settings_to_disk(_runtime_settings)
        except Exception:
            pass
    return current_settings()


def reset_settings(persist=False):
    return update_settings(DEFAULT_SETTINGS, persist=persist)


def reload_settings():
    global _runtime_settings
    _runtime_settings = _load_settings_from_disk()
    return current_settings()
