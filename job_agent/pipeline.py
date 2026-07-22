from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from job_agent.models import PipelineResult
from job_agent.researcher import research_company
from job_agent.writer import write_cover_letter

console = Console()


def run_pipeline(
    company_name: str,
    job_description: str,
    resume_text: str,
    *,
    verbose: bool = True,
) -> PipelineResult:
    """Run Researcher → Writer (draft → critique → optional revise)."""
    if verbose:
        console.print(Rule("[bold]Agent 1: Researcher[/bold]"))
        console.print(f"Searching and structuring research for [cyan]{company_name}[/cyan]...")

    research, notes = research_company(company_name, job_description)

    if verbose:
        console.print(
            Panel(
                "\n".join(f"- {f}" for f in research.companyFacts) or "(none)",
                title="Company facts",
                border_style="cyan",
            )
        )
        console.print(
            Panel(
                "\n".join(f"- {r}" for r in research.roleRequirements) or "(none)",
                title="Role requirements",
                border_style="cyan",
            )
        )
        if notes:
            console.print(
                Panel(notes[:1200] + ("..." if len(notes) > 1200 else ""), title="Research notes")
            )

        console.print(Rule("[bold]Agent 2: Writer[/bold]"))
        console.print("Drafting cover letter...")

    draft, critique, final_letter, revised = write_cover_letter(
        research, job_description, resume_text
    )

    if verbose:
        console.print(Panel(draft, title="Draft", border_style="yellow"))
        console.print(
            Panel(
                critique.model_dump_json(indent=2),
                title="Critique",
                border_style="magenta",
            )
        )
        if revised:
            console.print("[yellow]Issues found - revising...[/yellow]")
            console.print(Panel(final_letter, title="Final letter", border_style="green"))
        else:
            console.print("[green]No issues flagged - using draft as final.[/green]")

    return PipelineResult(
        research=research,
        draft=draft,
        critique=critique,
        final_letter=final_letter,
        revised=revised,
    )


def save_result(result: PipelineResult, output_dir: Path) -> Path:
    """Persist research JSON + final cover letter to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in result.research.companyName)
    letter_path = output_dir / f"{safe}_cover_letter.txt"
    research_path = output_dir / f"{safe}_research.json"
    meta_path = output_dir / f"{safe}_pipeline.json"

    letter_path.write_text(result.final_letter, encoding="utf-8")
    research_path.write_text(result.research.model_dump_json(indent=2), encoding="utf-8")
    meta_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return letter_path
