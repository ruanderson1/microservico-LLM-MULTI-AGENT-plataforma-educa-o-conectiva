from pathlib import Path
import sys


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from services.class_report_service import CLASS_REPORT_GRAPH
from services.student_report_service import STUDENT_REPORT_GRAPH


def _to_mermaid(graph) -> str:
    return graph.get_graph().draw_mermaid()


def main() -> None:
    student_mermaid = _to_mermaid(STUDENT_REPORT_GRAPH)
    class_mermaid = _to_mermaid(CLASS_REPORT_GRAPH)

    content = "\n".join(
        [
            "# LangGraph Gerado Automaticamente",
            "",
            "Este arquivo e gerado por scripts/generate_langgraph_diagrams.py.",
            "",
            "## Student Report Graph",
            "",
            "```mermaid",
            student_mermaid,
            "```",
            "",
            "## Class Report Graph",
            "",
            "```mermaid",
            class_mermaid,
            "```",
            "",
        ]
    )

    output_path = SERVICE_ROOT / "docs" / "langgraph-generated.md"
    output_path.write_text(content, encoding="utf-8")
    print(f"Diagrama gerado em: {output_path}")


if __name__ == "__main__":
    main()