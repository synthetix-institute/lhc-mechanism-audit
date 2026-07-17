from __future__ import annotations

from pathlib import Path

from lhc_audit.extract import extract_equations, read_document


def test_display_alias_and_equation_system_are_preserved(tmp_path: Path):
    source = tmp_path / "0806.3381.tex"
    source.write_text(
        r"""
\documentclass{article}
\def\be{\begin{eqnarray}}
\def\ee{\end{eqnarray}}
\begin{document}
\be
{dp\over d\ell}&=&-A\rho R^2\\
{dM\over d\ell}&=&B\rho R^2/v
\ee
The inline threshold is $\tau=x_1x_2>\tau_{min}$.
\end{document}
""",
        encoding="utf-8",
    )
    equations = extract_equations(read_document(source).text)
    assert len(equations) == 2
    assert equations[0]["kind"] == "system"
    assert "dp\\over d\\ell" in equations[0]["formula"]
    assert "dM\\over d\\ell" in equations[0]["formula"]
    assert equations[1]["kind"] == "inline"


def test_metadata_ignores_commented_title_and_extracts_citations(tmp_path: Path):
    source = tmp_path / "0901.2948.tex"
    source.write_text(
        r"""
% \title{Wrong title}
\documentclass{article}
\title{Physical growth at the LHC}
\author{A. Researcher}
\begin{document}
See arXiv:0806.3381 and \[x=y.\]
\end{document}
""",
        encoding="utf-8",
    )
    document = read_document(source)
    assert document.metadata["title"] == "Physical growth at the LHC"
    assert document.metadata["authors"] == ["A. Researcher"]
    assert document.cited_arxiv_ids == ["0806.3381"]
