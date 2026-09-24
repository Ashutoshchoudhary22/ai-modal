"""UI implementation planning."""

from __future__ import annotations

import re

from ai_platform_protocol.ui import (
    ImplementationPlan,
    ImplementationPlanItem,
    UIGenerationRequest,
    UIGenerationTarget,
    UIRepositoryContext,
    UISpec,
)


def create_implementation_plan(
    spec: UISpec,
    context: UIRepositoryContext,
    request: UIGenerationRequest,
) -> ImplementationPlan:
    items: list[ImplementationPlanItem] = []
    files_create: list[str] = []
    files_modify: list[str] = []
    step = 1
    profile = context.framework
    ext = "tsx" if profile.language == "typescript" else "jsx"

    for component in spec.components:
        reuse = _find_reuse(component.name, context.components)
        if reuse:
            items.append(
                ImplementationPlanItem(
                    step=step,
                    action="reuse_component",
                    target=component.name,
                    reuse=reuse,
                )
            )
        else:
            comp_path = _component_path(profile, component.name, ext)
            files_create.append(comp_path)
            items.append(
                ImplementationPlanItem(step=step, action="create_component", target=comp_path)
            )
        step += 1

    if request.target in {UIGenerationTarget.PAGE, UIGenerationTarget.LAYOUT}:
        for page in spec.pages:
            page_path = _page_path(profile, page, ext, request.route or page.route)
            files_create.append(page_path)
            items.append(ImplementationPlanItem(step=step, action="create_page", target=page_path))
            step += 1
            if page.route and profile.framework.value.startswith("nextjs"):
                items.append(
                    ImplementationPlanItem(
                        step=step, action="add_route", target=page.route or page.name
                    )
                )
                step += 1

    validation_commands = _validation_commands(context, request.validation_mode.value)
    for cmd in validation_commands:
        items.append(ImplementationPlanItem(step=step, action="validate", target=cmd))
        step += 1

    return ImplementationPlan(
        items=items,
        files_to_create=list(dict.fromkeys(files_create)),
        files_to_modify=list(dict.fromkeys(files_modify)),
        validation_commands=validation_commands,
    )


def create_ui_spec(request: UIGenerationRequest, context: UIRepositoryContext) -> UISpec:
    name = _derive_name(request.prompt)
    if request.target == UIGenerationTarget.ANALYSIS:
        return UISpec(
            name="ui_analysis",
            description=request.prompt,
            framework=context.framework.framework,
            styling_system=context.framework.styling_system,
            constraints=["read_only"],
        )

    from ai_platform_protocol.ui import PageSpec

    page = PageSpec(
        name=name,
        route=request.route,
        responsive=request.responsive,
        accessibility=["semantic_html", "labels", "keyboard"] if request.accessibility else [],
    )
    return UISpec(
        name=name,
        description=request.prompt,
        framework=request.framework or context.framework.framework,
        styling_system=request.styling_system or context.framework.styling_system,
        pages=[page] if request.target == UIGenerationTarget.PAGE else [],
        components=[],
        responsive=request.responsive,
        accessibility=request.accessibility,
    )


def _find_reuse(name: str, existing: list[str]) -> str | None:
    pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
    for item in existing:
        if pattern.search(item):
            return item
    return None


def _component_path(profile, name: str, ext: str) -> str:
    base = profile.component_directory or "src/components"
    return f"{base}/{name}.{ext}"


def _page_path(profile, page, ext: str, route: str | None) -> str:
    if profile.framework.value == "nextjs_app":
        route_part = (route or page.route or page.name).strip("/").replace("/", "/")
        return f"app/{route_part}/page.{ext}"
    if profile.framework.value == "nextjs_pages":
        route_part = (route or page.route or page.name).strip("/")
        return f"pages/{route_part}.{ext}"
    base = profile.page_directory or "src/pages"
    return f"{base}/{page.name}.{ext}"


def _validation_commands(context: UIRepositoryContext, mode: str) -> list[str]:
    profile = context.framework
    commands: list[str] = []
    if mode in {"diagnostics", "build", "test", "full"}:
        commands.append("diagnostics")
    if mode in {"build", "full"} and profile.build_command:
        commands.append(profile.build_command)
    if mode in {"test", "full"} and profile.test_command:
        commands.append(profile.test_command)
    return commands


def _derive_name(prompt: str) -> str:
    words = re.findall(r"[A-Za-z]+", prompt)
    if not words:
        return "GeneratedPage"
    return "".join(word.capitalize() for word in words[:3])
