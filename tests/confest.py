# tests/conftest.py
import sys
import os
from pathlib import Path

# プロジェクトルートディレクトリをPythonパスに追加
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))