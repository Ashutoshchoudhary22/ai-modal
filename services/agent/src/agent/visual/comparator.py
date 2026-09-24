"""Deterministic visual screenshot comparison."""

from __future__ import annotations

import io
import time

from ai_platform_protocol.vision import (
    RegionComparisonResult,
    VisualAnalysis,
    VisualValidationResult,
)
from PIL import Image, ImageChops


class VisualComparator:
    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def compare(
        self,
        reference_bytes: bytes,
        generated_bytes: bytes,
        *,
        analysis: VisualAnalysis | None = None,
        threshold: float | None = None,
    ) -> VisualValidationResult:
        started = time.perf_counter()
        effective_threshold = threshold if threshold is not None else self.threshold

        ref = self._load_image(reference_bytes)
        gen = self._load_image(generated_bytes)
        gen = self._resize_to_match(ref, gen)

        diff = ImageChops.difference(ref, gen)
        diff_pixels = sum(1 for px in diff.get_flattened_data() if any(c > 10 for c in px[:3]))
        total_pixels = ref.size[0] * ref.size[1]
        pixel_diff_ratio = diff_pixels / total_pixels if total_pixels else 1.0
        structural = 1.0 - pixel_diff_ratio

        region_results = self._compare_regions(ref, gen, analysis)
        score = structural
        if region_results:
            score = sum(r.score for r in region_results) / len(region_results)

        passed = score >= effective_threshold
        differences: list[str] = []
        if not passed:
            differences.append(
                f"Overall similarity {score:.3f} below threshold {effective_threshold:.3f}"
            )
            if pixel_diff_ratio > 0.15:
                differences.append(f"Pixel difference ratio: {pixel_diff_ratio:.3f}")

        duration = int((time.perf_counter() - started) * 1000)
        return VisualValidationResult(
            passed=passed,
            score=round(score, 4),
            threshold=effective_threshold,
            pixel_difference_ratio=round(pixel_diff_ratio, 4),
            structural_similarity=round(structural, 4),
            region_results=region_results,
            differences=differences,
            duration_ms=duration,
        )

    def _load_image(self, data: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img

    def _resize_to_match(self, ref: Image.Image, gen: Image.Image) -> Image.Image:
        if gen.size != ref.size:
            return gen.resize(ref.size, Image.Resampling.LANCZOS)
        return gen

    def _compare_regions(
        self,
        ref: Image.Image,
        gen: Image.Image,
        analysis: VisualAnalysis | None,
    ) -> list[RegionComparisonResult]:
        if not analysis:
            return []
        results: list[RegionComparisonResult] = []
        w, h = ref.size
        for region_el in analysis.regions:
            if not region_el.region:
                continue
            label = region_el.region.label or region_el.element_type
            box = (
                int(region_el.region.x * w),
                int(region_el.region.y * h),
                int((region_el.region.x + region_el.region.width) * w),
                int((region_el.region.y + region_el.region.height) * h),
            )
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            ref_crop = ref.crop(box)
            gen_crop = gen.crop(box)
            diff = ImageChops.difference(ref_crop, gen_crop)
            diff_pixels = sum(1 for px in diff.get_flattened_data() if any(c > 10 for c in px[:3]))
            total = ref_crop.size[0] * ref_crop.size[1]
            ratio = diff_pixels / total if total else 1.0
            score = 1.0 - ratio
            results.append(
                RegionComparisonResult(
                    region=label,
                    score=round(score, 4),
                    passed=score >= self.threshold,
                    differences=[f"{label} mismatch"] if score < self.threshold else [],
                )
            )
        return results
