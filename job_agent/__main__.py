from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from job_agent.pipeline import run_pipeline, save_result


def _read_text(path: Path | None, inline: str | None, label: str) -> str:
    if inline and inline.strip():
        return inline.strip()
    if path is None:
        raise SystemExit(f"Provide --{label} or --{label}-file")
    if not path.exists():
        raise SystemExit(f"{label} file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"{label} file is empty: {path}")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Multi-agent cover letter pipeline (Researcher + Writer) via Groq.",
    )
    parser.add_argument("--company", "-c", required=True, help="Company name to research")
    parser.add_argument("--job", "-j", help="Job description text")
    parser.add_argument("--job-file", type=Path, help="Path to job description file")
    parser.add_argument("--resume", "-r", help="Resume text")
    parser.add_argument("--resume-file", type=Path, help="Path to resume file")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("output"),
        help="Directory for saved artifacts (default: ./output)",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Less console output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()

    job_description = _read_text(args.job_file, args.job, "job")
    resume_text = _read_text(args.resume_file, args.resume, "resume")

    try:
        result = run_pipeline(
            company_name=args.company,
            job_description=job_description,
            resume_text=resume_text,
            verbose=not args.quiet,
        )
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Pipeline failed:[/red] {exc}")
        return 1

    letter_path = save_result(result, args.output_dir)
    console.print(f"\n[bold green]Saved cover letter ->[/bold green] {letter_path}")
    if not args.quiet:
        console.print("\n" + result.final_materials.coverLetter)
        if result.final_materials.resumeBullets:
            console.print("\n[bold]Resume bullets[/bold]")
            for bullet in result.final_materials.resumeBullets:
                console.print(f"- {bullet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
