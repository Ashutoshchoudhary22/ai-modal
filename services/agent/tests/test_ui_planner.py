import shutil
from pathlib import Path

from agent.ui.context import build_ui_context
from agent.ui.detector import detect_framework_profile
from agent.ui.planner import create_implementation_plan, create_ui_spec
from ai_platform_protocol.ui import ComponentSpec, UIGenerationRequest, UIGenerationTarget

FIXTURES = Path(__file__).parent / "fixtures" / "ui"


def test_component_reuse_plan(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    profile = detect_framework_profile(root)
    context = build_ui_context(root, profile=profile)
    request = UIGenerationRequest(
        workspace_id="ws",
        prompt="Create login page",
        target=UIGenerationTarget.PAGE,
        route="/login",
    )
    spec = create_ui_spec(request, context)
    spec.components = [
        ComponentSpec(name="Button", purpose="submit"),
        ComponentSpec(name="LoginForm", purpose="form"),
    ]
    plan = create_implementation_plan(spec, context, request)
    reuse = [item for item in plan.items if item.action == "reuse_component"]
    assert reuse
    assert any("Button" in (item.reuse or "") for item in reuse)


def test_spec_serialization(tmp_path):
    root = tmp_path / "vite"
    shutil.copytree(FIXTURES / "vite-react", root)
    context = build_ui_context(root)
    request = UIGenerationRequest(
        workspace_id="ws",
        prompt="Dashboard page",
        target=UIGenerationTarget.PAGE,
    )
    spec = create_ui_spec(request, context)
    data = spec.model_dump()
    assert data["name"]
    assert data["responsive"] is True
