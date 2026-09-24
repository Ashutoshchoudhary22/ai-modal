"""Generate the multimodal-mini development dataset."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "data" / "examples" / "multimodal-mini"
COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 128, 128),
    (64, 64, 64),
]


def main() -> None:
    img_dir = ROOT / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for index, color in enumerate(COLORS, start=1):
        Image.new("RGB", (16, 16), color).save(img_dir / f"sample-{index:03d}.png")

    records = [
        (
            "mm-001",
            "Describe this interface.",
            "sample-001.png",
            "A red dashboard panel.",
            "screenshot_analysis",
        ),
        (
            "mm-002",
            "What color is shown?",
            "sample-002.png",
            "Green interface.",
            "image_understanding",
        ),
        ("mm-003", "Analyze UI.", "sample-003.png", "Blue layout.", "visual_question_answering"),
        (
            "mm-004",
            "Generate UI spec.",
            "sample-004.png",
            "Yellow header component.",
            "ui_generation",
        ),
        (
            "mm-005",
            "Screenshot to code.",
            "sample-005.png",
            "<div class=panel></div>",
            "screenshot_to_code",
        ),
        ("mm-006", "Describe panel.", "sample-006.png", "Cyan sidebar.", "screenshot_analysis"),
        (
            "mm-007",
            "Summarize view.",
            "sample-007.png",
            "Gray neutral panel.",
            "image_understanding",
        ),
        (
            "mm-008",
            "Dark theme check.",
            "sample-008.png",
            "Dark gray theme.",
            "visual_question_answering",
        ),
    ]
    lines: list[str] = []
    for record_id, prompt, image_name, answer, task in records:
        escaped_answer = answer.replace('"', '\\"')
        assistant_content = f'[{{"type": "text", "text": "{escaped_answer}"}}]'
        lines.append(
            f'{{"id": "{record_id}", "messages": [{{"role": "user", "content": ['
            f'{{"type": "text", "text": "{prompt}"}}, '
            f'{{"type": "image", "image": "images/{image_name}"}}]}}, '
            f'{{"role": "assistant", "content": {assistant_content}}}], '
            f'"metadata": {{"task_type": "{task}"}}}}'
        )
    (ROOT / "raw.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote dataset to {ROOT}")


if __name__ == "__main__":
    main()
