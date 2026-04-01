from __future__ import annotations

import shutil
from pathlib import Path

from ..engines import (
    convert_pdf_to_csv_with_tabula,
    convert_with_pandoc_direct,
    detect_tooling,
    extract_with_docling,
    extract_with_native,
    extract_with_pandoc,
    extract_with_pymupdf,
    render_with_native,
    render_with_pandoc_from_ir,
)
from .types import (
    ConversionPlan,
    ConversionRequest,
    DocumentFormat,
    PANDOC_READ_FORMATS,
    PANDOC_WRITE_FORMATS,
    PlanStep,
    ToolAvailability,
)


class ConversionRouter:
    def __init__(self, tooling: dict[str, ToolAvailability] | None = None) -> None:
        self.tooling = tooling or detect_tooling()

    def _available(self, name: str) -> bool:
        return self.tooling.get(name, ToolAvailability(name, False, "")).available

    def rank_plans(self, request: ConversionRequest) -> list[ConversionPlan]:
        plans: list[ConversionPlan] = []

        if request.source_format == request.target_format:
            plans.append(
                ConversionPlan(
                    route_name="copy",
                    score=100,
                    direct_engine="copy",
                    steps=[PlanStep("copy", "copy-file", "Source and target formats are identical")],
                )
            )

        if (
            request.source_format == DocumentFormat.PDF
            and request.target_format == DocumentFormat.CSV
            and self._available("tabula")
        ):
            plans.append(
                ConversionPlan(
                    route_name="pdf-to-csv-tabula",
                    score=98,
                    direct_engine="tabula",
                    steps=[PlanStep("tabula", "extract-csv", "Use tabula-py for PDF table extraction")],
                )
            )

        if self._can_use_pandoc_direct(request):
            score = 96
            if request.target_format == DocumentFormat.PDF:
                score = 95
            plans.append(
                ConversionPlan(
                    route_name="pandoc-direct",
                    score=score,
                    direct_engine="pandoc",
                    steps=[
                        PlanStep(
                            "pandoc",
                            "direct-convert",
                            "Use Pandoc for a direct text-like conversion",
                        )
                    ],
                )
            )

        if request.target_format == DocumentFormat.CSV:
            if request.source_format == DocumentFormat.JSON:
                plans.append(
                    ConversionPlan(
                        route_name="native-json-to-csv",
                        score=88,
                        extractor="native",
                        renderer="native",
                        steps=[
                            PlanStep("native", "extract-ir", "Read JSON natively"),
                            PlanStep("native", "render-csv", "Serialize list-of-dicts as CSV"),
                        ],
                    )
                )
            return self._sort_plans(plans, request.prefer_engine)

        extractors = self._extractor_candidates(request)
        renderers = self._renderer_candidates(request)
        for extractor_name, extractor_score in extractors:
            for renderer_name, renderer_score in renderers:
                score = min(extractor_score, renderer_score)
                steps = [
                    PlanStep(extractor_name, "extract-ir", f"Extract {request.source_format.value} into IR"),
                    PlanStep(renderer_name, "render-output", f"Render IR as {request.target_format.value}"),
                ]
                plans.append(
                    ConversionPlan(
                        route_name=f"{extractor_name}-to-{renderer_name}",
                        score=score,
                        extractor=extractor_name,
                        renderer=renderer_name,
                        steps=steps,
                    )
                )

        return self._sort_plans(plans, request.prefer_engine)

    def convert(self, request: ConversionRequest) -> ConversionPlan:
        errors: list[str] = []
        for plan in self.rank_plans(request):
            try:
                self._execute_plan(plan, request)
                return plan
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{plan.route_name}: {exc}")
        error_text = "\n".join(f"- {line}" for line in errors) or "- no valid conversion path found"
        raise RuntimeError(f"All conversion routes failed:\n{error_text}")

    def _sort_plans(
        self,
        plans: list[ConversionPlan],
        preferred_engine: str | None,
    ) -> list[ConversionPlan]:
        unique: dict[tuple[str, str | None, str | None, str | None], ConversionPlan] = {}
        for plan in plans:
            key = (plan.route_name, plan.direct_engine, plan.extractor, plan.renderer)
            existing = unique.get(key)
            if existing is None or plan.score > existing.score:
                unique[key] = plan
        ranked = list(unique.values())
        if preferred_engine:
            preferred = preferred_engine.lower()
            for plan in ranked:
                if plan.uses_engine(preferred):
                    plan.score += 25
        ranked.sort(key=lambda plan: plan.score, reverse=True)
        return ranked

    def _extractor_candidates(self, request: ConversionRequest) -> list[tuple[str, int]]:
        source = request.source_format
        candidates: list[tuple[str, int]] = []

        if source in {
            DocumentFormat.MARKDOWN,
            DocumentFormat.TEXT,
            DocumentFormat.JSON,
            DocumentFormat.CSV,
            DocumentFormat.HTML,
        }:
            candidates.append(("native", 90))

        if source in PANDOC_READ_FORMATS and self._available("pandoc"):
            candidates.append(("pandoc", 89))

        if source == DocumentFormat.PDF and self._available("pymupdf4llm"):
            score = 95 if request.target_format in {
                DocumentFormat.MARKDOWN,
                DocumentFormat.TEXT,
                DocumentFormat.HTML,
                DocumentFormat.JSON,
            } else 94
            candidates.append(("pymupdf4llm", score))

        if source in {
            DocumentFormat.PDF,
            DocumentFormat.DOCX,
            DocumentFormat.PPTX,
            DocumentFormat.XLSX,
            DocumentFormat.HTML,
            DocumentFormat.TEXT,
        } and self._available("docling"):
            candidates.append(("docling", 92 if source == DocumentFormat.PDF else 90))

        return candidates

    def _renderer_candidates(self, request: ConversionRequest) -> list[tuple[str, int]]:
        target = request.target_format
        candidates: list[tuple[str, int]] = []

        if target in {
            DocumentFormat.MARKDOWN,
            DocumentFormat.TEXT,
            DocumentFormat.JSON,
            DocumentFormat.HTML,
        }:
            score = 92 if target != DocumentFormat.HTML else 88
            candidates.append(("native", score))

        if target in PANDOC_WRITE_FORMATS and self._available("pandoc"):
            candidates.append(("pandoc", 94))

        if target == DocumentFormat.PDF and self._available("pandoc") and self._available("pdf_engine"):
            candidates.append(("pandoc", 93))

        return candidates

    def _can_use_pandoc_direct(self, request: ConversionRequest) -> bool:
        if not self._available("pandoc"):
            return False
        if request.source_format not in PANDOC_READ_FORMATS:
            return False
        if request.target_format == DocumentFormat.PDF:
            return self._available("pdf_engine")
        return request.target_format in PANDOC_WRITE_FORMATS

    def _execute_plan(self, plan: ConversionPlan, request: ConversionRequest) -> None:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        if plan.route_name == "copy":
            shutil.copy2(request.input_path, request.output_path)
            return

        if plan.direct_engine == "tabula":
            convert_pdf_to_csv_with_tabula(request.input_path, request.output_path)
            return

        if plan.direct_engine == "pandoc":
            convert_with_pandoc_direct(
                request.input_path,
                request.output_path,
                request.source_format,
                request.target_format,
            )
            return

        ir = self._extract(request, plan.extractor)
        self._render(ir, request.output_path, request.target_format, plan.renderer)

    def _extract(self, request: ConversionRequest, extractor: str | None):
        if extractor == "native":
            return extract_with_native(request.input_path, request.source_format)
        if extractor == "pandoc":
            return extract_with_pandoc(request.input_path, request.source_format)
        if extractor == "pymupdf4llm":
            return extract_with_pymupdf(request.input_path, force_ocr=request.force_ocr)
        if extractor == "docling":
            return extract_with_docling(request.input_path, request.source_format)
        raise RuntimeError(f"Unknown extractor: {extractor}")

    def _render(
        self,
        ir,
        output_path: Path,
        target_format: DocumentFormat,
        renderer: str | None,
    ) -> None:
        if renderer == "native":
            render_with_native(ir, output_path, target_format)
            return
        if renderer == "pandoc":
            render_with_pandoc_from_ir(ir, output_path, target_format)
            return
        raise RuntimeError(f"Unknown renderer: {renderer}")
