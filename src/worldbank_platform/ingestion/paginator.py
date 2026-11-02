"""Reusable paginator. Supports page/per_page (World Bank) and cursor styles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator


@dataclass
class Page:
    items: list[dict]
    page: int
    pages: int
    total: int
    per_page: int


@dataclass
class Paginator:
    """Iterate all pages. `fetch_page(page)` returns (items, total_pages, total)."""
    fetch_page: Callable[[int], tuple[list[dict], int, int]]
    start_page: int = 1

    def pages(self) -> Iterator[Page]:
        page = self.start_page
        while True:
            items, total_pages, total = self.fetch_page(page)
            yield Page(items=items, page=page, pages=total_pages,
                       total=total, per_page=len(items))
            if page >= total_pages or not items:
                break
            page += 1

    def items(self) -> Iterator[dict]:
        for pg in self.pages():
            yield from pg.items


@dataclass
class CursorPaginator:
    """Cursor-style pagination for future APIs (IMF/OECD SDMX-JSON style)."""
    fetch: Callable[[str | None], tuple[list[dict], str | None]]

    def items(self) -> Iterator[dict]:
        cursor: str | None = None
        while True:
            items, cursor = self.fetch(cursor)
            yield from items
            if not cursor:
                break
