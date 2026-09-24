"""Convert VisualAnalysis to Phase 7 UISpec."""

from __future__ import annotations

from ai_platform_protocol.ui import ComponentSpec, PageSpec, UISpec
from ai_platform_protocol.vision import ConfidenceLevel, VisualAnalysis, VisualElement


def visual_analysis_to_ui_spec(
    analysis: VisualAnalysis,
    *,
    prompt: str | None = None,
    route: str | None = None,
) -> UISpec:
    page_name = _derive_page_name(analysis, prompt)
    components = _extract_components(analysis.regions)
    page_sections = [r.label or r.element_type for r in analysis.regions if r.region]

    page = PageSpec(
        name=page_name,
        route=route,
        sections=page_sections,
        components=[c.name for c in components],
        responsive=True,
        accessibility=analysis.accessibility_notes or ["semantic_html", "labels"],
    )

    theme: dict = {}
    if analysis.design_tokens.colors:
        theme["colors"] = analysis.design_tokens.colors
    if analysis.design_tokens.typography:
        theme["typography"] = analysis.design_tokens.typography
    if analysis.design_tokens.spacing:
        theme["spacing"] = analysis.design_tokens.spacing

    return UISpec(
        name=page_name,
        description=prompt or analysis.page_title or "Screenshot-derived UI",
        pages=[page],
        components=components,
        theme=theme,
        responsive=True,
        accessibility=True,
        constraints=analysis.responsive_hints,
        screenshot_metadata={
            "source_image_id": analysis.source_image_id,
            "visual_confidence": analysis.overall_confidence,
            "page_type": analysis.page_type,
            "provider": analysis.provider,
            "layout": analysis.layout.model_dump() if analysis.layout else None,
        },
    )


def _derive_page_name(analysis: VisualAnalysis, prompt: str | None) -> str:
    if analysis.page_title:
        words = [w.capitalize() for w in analysis.page_title.split() if w.isalnum()]
        if words:
            return "".join(words[:3])
    if prompt:
        words = [w.capitalize() for w in prompt.split() if w.isalnum()]
        if words:
            return "".join(words[:3])
    return "ScreenshotPage"


def _extract_components(regions: list[VisualElement]) -> list[ComponentSpec]:
    components: list[ComponentSpec] = []
    seen: set[str] = set()

    def walk(elements: list[VisualElement]) -> None:
        for el in elements:
            comp_type = el.element_type
            if comp_type in {
                "button",
                "input",
                "card",
                "navbar",
                "sidebar",
                "form",
                "table",
                "modal",
                "hero",
                "footer",
                "header",
            }:
                name = _component_name(comp_type, el.label)
                if name not in seen:
                    seen.add(name)
                    components.append(
                        ComponentSpec(
                            name=name,
                            purpose=el.label or comp_type,
                            props=_infer_props(el),
                            states=_infer_states(el),
                            accessibility=[el.accessibility_hint] if el.accessibility_hint else [],
                            responsive=el.confidence != ConfidenceLevel.UNCERTAIN,
                        )
                    )
            walk(el.children)

    walk(regions)
    return components


def _component_name(comp_type: str, label: str | None) -> str:
    if label:
        cleaned = "".join(w.capitalize() for w in label.split() if w.isalnum())
        if cleaned:
            return cleaned
    return comp_type.capitalize()


def _infer_props(el: VisualElement) -> list[str]:
    if el.element_type in {"button", "input"}:
        return ["label", "onClick"] if el.element_type == "button" else ["label", "value"]
    if el.element_type == "card":
        return ["title", "children"]
    return []


def _infer_states(el: VisualElement) -> list[str]:
    if el.element_type == "button":
        return ["default", "hover", "focus", "disabled"]
    if el.element_type == "input":
        return ["default", "focus", "error"]
    return ["default"]
