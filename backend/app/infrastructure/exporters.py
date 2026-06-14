"""Export adapter boundaries for reports and analysis datasets."""

import csv
from pathlib import Path
from typing import Any


class CsvExporter:
    """Small CSV exporter ready for future metrics and batch results."""

    def export(self, rows: list[dict[str, Any]], destination: Path) -> Path:
        """Write homogeneous dictionaries to a CSV file."""

        if not rows:
            raise ValueError("At least one row is required")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return destination
