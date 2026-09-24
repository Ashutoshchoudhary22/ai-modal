"""Build bounded browser observations."""

from __future__ import annotations

from agent.config import BrowserSettings
from ai_platform_protocol.browser import BrowserElement, BrowserObservation


def build_observation(
    *,
    observation_id: str,
    url: str,
    title: str | None,
    elements: list[BrowserElement],
    visible_text: str,
    settings: BrowserSettings,
    screenshot_reference: str | None = None,
) -> BrowserObservation:
    truncated = False
    max_elements = settings.max_elements
    if len(elements) > max_elements:
        elements = elements[:max_elements]
        truncated = True

    text = visible_text
    if len(text) > settings.max_visible_text_chars:
        text = text[: settings.max_visible_text_chars] + "\n...[truncated]"
        truncated = True

    masked_elements = [_mask_sensitive(el) for el in elements]
    a11y = _accessibility_summary(masked_elements)

    return BrowserObservation(
        observation_id=observation_id,
        url=url,
        title=title,
        viewport={"width": 1280, "height": 720},
        elements=masked_elements,
        visible_text=text,
        accessibility_summary=a11y,
        screenshot_reference=screenshot_reference,
        truncated=truncated,
    )


def _mask_sensitive(element: BrowserElement) -> BrowserElement:
    if element.sensitive and element.value:
        return element.model_copy(update={"value": "[REDACTED]"})
    return element


def _accessibility_summary(elements: list[BrowserElement]) -> str:
    lines: list[str] = []
    for el in elements[:50]:
        label = el.name or el.text or el.placeholder or el.role or el.tag or "element"
        state = []
        if not el.visible:
            state.append("hidden")
        if not el.enabled:
            state.append("disabled")
        suffix = f" ({', '.join(state)})" if state else ""
        lines.append(f"[{el.element_id}] {el.role or el.tag}: {label}{suffix}")
    return "\n".join(lines)
