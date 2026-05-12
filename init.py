# Nuke 启动初始化脚本 / Nuke startup initialization script.
"""Nuke package initialization for Nuke RefBoard."""

import os
import sys


PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)
