"""Application-wide constants and helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional


# User-facing date configuration (DD/MM/YY)
DATE_DISPLAY_FORMAT = "%d/%m/%y"
DATE_USER_FORMAT_LABEL = "DD/MM/YY"
DATE_INPUT_FORMATS: tuple[str, ...] = ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d")


def format_user_date(value: datetime) -> str:
	"""Return a DD/MM/YY string for a datetime value."""
	return value.strftime(DATE_DISPLAY_FORMAT)


def parse_user_date(value: str, extra_formats: Optional[Iterable[str]] = None) -> Optional[datetime]:
	"""Parse a user-provided date string using tolerant formats."""
	if not value:
		return None
	candidates = DATE_INPUT_FORMATS
	if extra_formats:
		candidates = tuple(dict.fromkeys((*DATE_INPUT_FORMATS, *tuple(extra_formats))))
	cleaned = value.strip()
	for fmt in candidates:
		try:
			return datetime.strptime(cleaned, fmt)
		except ValueError:
			continue
	return None
