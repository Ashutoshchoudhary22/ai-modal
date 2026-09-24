import shutil
from pathlib import Path

from agent.ui.detector import detect_framework_profile
from ai_platform_protocol.ui import StylingSystem, UIFramework

FIXTURES = Path(__file__).parent / "fixtures" / "ui"


def test_detect_vite_react(tmp_path):
    target = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", target)
    profile = detect_framework_profile(target)
    assert profile.framework == UIFramework.VITE_REACT
    assert profile.styling_system == StylingSystem.TAILWIND
    assert profile.component_directory == "src/components"
    assert profile.build_command == "npm run build"


def test_detect_nextjs_app(tmp_path):
    target = tmp_path / "next"
    shutil.copytree(FIXTURES / "nextjs-app", target)
    profile = detect_framework_profile(target)
    assert profile.framework == UIFramework.NEXTJS_APP
    assert profile.page_directory == "app"


def test_detect_unknown(tmp_path):
    profile = detect_framework_profile(tmp_path)
    assert profile.framework == UIFramework.UNKNOWN
