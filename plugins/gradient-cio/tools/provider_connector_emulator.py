#!/usr/bin/env python3
"""Fictional connector emulator for provider-neutral acceptance tests."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any


SCHEMA_DIGEST_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


class EmulatorError(ValueError):
    """Raised when a fictional connector violates the intake contract."""


@dataclass(frozen=True)
class EmulatedPage:
    """One connector page and its explicit continuation evidence."""

    records: tuple[dict[str, Any], ...]
    schema_digest: str
    next_cursor: str | None
    complete: bool


@dataclass(frozen=True)
class EmulatedCollection:
    """Exhaustive source collection returned by the emulator."""

    provider: str
    data_type: str
    records: tuple[dict[str, Any], ...]
    schema_digest: str
    page_count: int
    requested_cursors: tuple[str | None, ...]


@dataclass(frozen=True)
class EmulatedCorrectionDelta:
    """Identity-based correction evidence; omissions are never deletions."""

    created_source_ids: tuple[str, ...]
    updated_source_ids: tuple[str, ...]
    unchanged_source_ids: tuple[str, ...]
    omitted_source_ids: tuple[str, ...]


class SyntheticConnectorEmulator:
    """Exercise pagination and drift controls without claiming vendor behavior."""

    def __init__(
        self,
        *,
        provider: str,
        data_type: str,
        pages: dict[str | None, EmulatedPage],
    ) -> None:
        if "(TEST)" not in provider:
            raise EmulatorError("Synthetic provider identity must include (TEST).")
        if not data_type:
            raise EmulatorError("Synthetic data type is required.")
        if None not in pages:
            raise EmulatorError("Synthetic connector requires an initial page.")
        self._provider = provider
        self._data_type = data_type
        self._pages = copy.deepcopy(pages)

    def collect(self, *, max_pages: int = 100) -> EmulatedCollection:
        if max_pages < 1:
            raise EmulatorError("max_pages must be positive.")
        cursor: str | None = None
        requested: list[str | None] = []
        records: list[dict[str, Any]] = []
        schema_digest: str | None = None

        while True:
            if cursor in requested:
                raise EmulatorError("Connector pagination cursor loop detected.")
            if len(requested) >= max_pages:
                raise EmulatorError("Connector pagination exceeded max_pages.")
            requested.append(cursor)
            page = self._pages.get(cursor)
            if page is None:
                raise EmulatorError(f"Connector page is missing for cursor {cursor!r}.")
            if SCHEMA_DIGEST_PATTERN.fullmatch(page.schema_digest) is None:
                raise EmulatorError("Connector page schema digest is invalid.")
            if schema_digest is None:
                schema_digest = page.schema_digest
            elif schema_digest != page.schema_digest:
                raise EmulatorError("Connector schema drifted during pagination.")
            records.extend(copy.deepcopy(page.records))

            if page.complete:
                if page.next_cursor is not None:
                    raise EmulatorError(
                        "Completed connector page cannot return a next cursor."
                    )
                break
            if page.next_cursor is None:
                raise EmulatorError(
                    "Incomplete connector page must return a next cursor."
                )
            cursor = page.next_cursor

        source_ids = [record.get("external_record_id") for record in records]
        if not records:
            raise EmulatorError("Connector collection cannot be empty.")
        if any(not isinstance(item, str) or not item for item in source_ids):
            raise EmulatorError("Every connector record needs an external_record_id.")
        if len(source_ids) != len(set(source_ids)):
            raise EmulatorError("Connector source record IDs must be unique.")
        if schema_digest is None:
            raise EmulatorError("Connector collection has no schema evidence.")

        return EmulatedCollection(
            provider=self._provider,
            data_type=self._data_type,
            records=tuple(records),
            schema_digest=schema_digest,
            page_count=len(requested),
            requested_cursors=tuple(requested),
        )


def example_pages() -> dict[str | None, EmulatedPage]:
    """Return a deterministic two-page fictional connector scenario."""
    schema_digest = f"sha256:{'e' * 64}"
    return {
        None: EmulatedPage(
            records=(
                {
                    "external_record_id": "example-record-1",
                    "value": "100",
                    "unit": "currency_units",
                },
            ),
            schema_digest=schema_digest,
            next_cursor="page-2",
            complete=False,
        ),
        "page-2": EmulatedPage(
            records=(
                {
                    "external_record_id": "example-record-2",
                    "value": "200",
                    "unit": "currency_units",
                },
            ),
            schema_digest=schema_digest,
            next_cursor=None,
            complete=True,
        ),
    }


def compare_collections(
    previous: EmulatedCollection,
    current: EmulatedCollection,
) -> EmulatedCorrectionDelta:
    """Compare source runs without treating omitted IDs as deletes."""
    if (
        previous.provider != current.provider
        or previous.data_type != current.data_type
        or previous.schema_digest != current.schema_digest
    ):
        raise EmulatorError("Correction comparison requires matching source identity.")
    previous_by_id = {
        str(record["external_record_id"]): record for record in previous.records
    }
    current_by_id = {
        str(record["external_record_id"]): record for record in current.records
    }
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)
    shared_ids = previous_ids & current_ids
    updated = {
        source_id
        for source_id in shared_ids
        if json.dumps(previous_by_id[source_id], sort_keys=True)
        != json.dumps(current_by_id[source_id], sort_keys=True)
    }
    return EmulatedCorrectionDelta(
        created_source_ids=tuple(sorted(current_ids - previous_ids)),
        updated_source_ids=tuple(sorted(updated)),
        unchanged_source_ids=tuple(sorted(shared_ids - updated)),
        omitted_source_ids=tuple(sorted(previous_ids - current_ids)),
    )


__all__ = [
    "EmulatedCollection",
    "EmulatedCorrectionDelta",
    "EmulatedPage",
    "EmulatorError",
    "SyntheticConnectorEmulator",
    "compare_collections",
    "example_pages",
]
