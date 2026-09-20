"""Expose pytest failures through GitHub check annotations.

GitHub's Actions log storage is not always reachable from a diagnostic client,
while check-run annotations remain available through the GitHub API.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def _escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def annotate(report: Path) -> None:
    if not report.is_file():
        print("::warning::Test run failed before a JUnit report was written")
        return

    root = ET.parse(report).getroot()
    for case in root.iter("testcase"):
        failure = case.find("failure")
        if failure is None:
            failure = case.find("error")
        if failure is None:
            continue
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        detail = failure.get("message") or failure.text or "pytest failure"
        print(f"::error title={_escape(name)}::{_escape(detail[:1000])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    annotate(parser.parse_args().report)
