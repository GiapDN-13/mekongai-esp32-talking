"""Shared fixtures for xiaozhi-server tests.

Sets up sys.path and creates a minimal data/.config.yaml so that the logger /
config_loader chain does not crash during import-time initialisation.
"""

import sys
import os

# Add the xiaozhi-server root to sys.path so `core.*`, `config.*`, `plugins_func.*` resolve.
_SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SERVER_ROOT not in sys.path:
    sys.path.insert(0, _SERVER_ROOT)

# Skip calling manager-api when loading config
os.environ.setdefault("XIAOZHI_LOCAL_CONFIG_ONLY", "1")

# Ensure data/.config.yaml exists (required by settings.check_config_file)
_data_dir = os.path.join(_SERVER_ROOT, "data")
_custom_cfg = os.path.join(_data_dir, ".config.yaml")
if not os.path.exists(_custom_cfg):
    os.makedirs(_data_dir, exist_ok=True)
    with open(_custom_cfg, "w", encoding="utf-8") as _f:
        _f.write("# Auto-created by test conftest — safe to delete\nlog:\n  log_dir: tmp\n  data_dir: data\n")
