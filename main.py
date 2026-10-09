import argparse
import html
import json
import sys
from pathlib import Path

from src.auditor import (
    fingerprint as _fingerprint,
    split_groups as _split_groups,
    validate as _validate,
)


def fingerprint(text: str) -> str:
    """Return the normalized SHA-256 fingerprint of text."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return _fingerprint(text)


def validate(records: list[dict]) -> list[dict]:
    """Validate records and reject duplicate IDs."""
    return _validate(records)


def evidence(train: list[dict], test: list[dict]) -> dict:
    """Identify train records responsible for test leakage."""
    train_by_fingerprint = {}
    train_by_group = {}

    for record in train:
        train_by_fingerprint.setdefault(
            fingerprint(record["text"]), []
        ).append(record["id"])

        train_by_group.setdefault(
            record["group"], []
        ).append(record["id"])

    content = []
    groups = []

    for record in test:
        matching_content = train_by_fingerprint.get(
            fingerprint(record["text"]), []
        )
        matching_groups = train_by_group.get(record["group"], [])

        if matching_content:
            content.append({
                "test_id": record["id"],
                "train_ids": matching_content,
            })

        if matching_groups:
            groups.append({
                "test_id": record["id"],
                "group": record["group"],
                "train_ids": matching_groups,
            })

    return {
        "content": content,
        "groups": groups,
    }


def audit(train: list[dict], test: list[dict]) -> dict:
    """Audit content and group leakage across two partitions."""
    validate(train)
    validate(test)

    train_ids = {record["id"] for record in train}
    test_ids = {record["id"] for record in test}

    duplicate_ids = train_ids & test_ids
    if duplicate_ids:
        raise ValueError(
            f"Duplicate record IDs across partitions: "
            f"{sorted(duplicate_ids, key=str)}"
        )

    findings = evidence(train, test)

    content_leaks = [
        item["test_id"] for item in findings["content"]
    ]
    group_leaks = [
        item["test_id"] for item in findings["groups"]
    ]

    clean = not content_leaks and not group_leaks

    return {
        "clean": clean,
        "content_leaks": content_leaks,
        "group_leaks": group_leaks,
        "content_leakage_count": len(content_leaks),
        "group_leakage_count": len(group_leaks),
    }


def split_groups(
    records: list[dict],
    test_fraction: float = 0.2,
    seed: str = "course",
) -> dict:
    """Split records without separating records from the same group."""
    return _split_groups(
        records,
        test_fraction=test_fraction,
        seed=seed,
    )


def summarize(train: list[dict], test: list[dict]) -> dict:
    """Summarize partition sizes, groups, leakage, and usability."""
    findings = audit(train, test)
    provenance = evidence(train, test)

    train_rows = len(train)
    test_rows = len(test)

    usable = (
        train_rows > 0
        and test_rows > 0
        and findings["clean"]
    )

    return {
        "train_rows": train_rows,
        "test_rows": test_rows,
        "train_groups": len({r["group"] for r in train}),
        "test_groups": len({r["group"] for r in test}),
        "clean": findings["clean"],
        "content_leaks": findings["content_leaks"],
        "group_leaks": findings["group_leaks"],
        "content_leakage_count": findings["content_leakage_count"],
        "group_leakage_count": findings["group_leakage_count"],
        "evidence": provenance,
        "usable": usable,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit dataset splits for content and group leakage."
    )
    parser.add_argument("input", help="Path to the input JSON file.")
    parser.add_argument(
        "--split",
        type=float,
        default=0.2,
        help="Test fraction when the input contains records.",
    )
    parser.add_argument(
        "--seed",
        default="course",
        help="Stable split seed.",
    )
    parser.add_argument(
        "--output",
        default="split-audit.json",
        help="Path for the JSON audit report.",
    )
    parser.add_argument(
        "--html",
        help="Optional path for an HTML audit report.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return exit code 2 if the split is unusable.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        input_path = Path(args.input)
        payload = json.loads(input_path.read_text(encoding="utf-8-sig"))

        if not isinstance(payload, dict):
            raise ValueError("Input JSON must contain an object.")

        if "train" in payload and "test" in payload:
            train = payload["train"]
            test = payload["test"]
        elif "records" in payload:
            result = split_groups(
                payload["records"],
                test_fraction=args.split,
                seed=args.seed,
            )
            train = result["train"]
            test = result["test"]
        else:
            raise ValueError(
                "Input must contain either 'train' and 'test', "
                "or 'records'."
            )

        if not isinstance(train, list) or not isinstance(test, list):
            raise ValueError("Train and test partitions must be lists.")

        report = summarize(train, test)
        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if args.html:
            report_json = html.escape(
                json.dumps(report, indent=2, ensure_ascii=False)
            )
            page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dataset Split Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 900px;
margin: 2rem auto; padding: 0 1rem; }}
pre {{ background: #f3f4f6; padding: 1rem; overflow: auto; }}
</style>
</head>
<body>
<h1>Dataset Split Audit</h1>
<p>Usable: <strong>{report["usable"]}</strong></p>
<pre>{report_json}</pre>
</body>
</html>
"""
            Path(args.html).write_text(page, encoding="utf-8")

        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\nJSON report saved to: {output_path}")

        if args.html:
            print(f"HTML report saved to: {args.html}")

        if args.check and not report["usable"]:
            return 2

        return 0

    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
