"""Adapter layer for Strands-based recommendation generation."""

from __future__ import annotations


class StrandsAdapter:
    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = provider
        self.model = model

    def generate_summary(self, *, skills: list[str], job_title: str) -> dict[str, object]:
        return {
            "job_title": job_title,
            "matched_skills": skills,
            "provider": self.provider or "local-fallback",
            "model": self.model or "fallback-overlap",
        }
