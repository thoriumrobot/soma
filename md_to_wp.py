#!/usr/bin/env python3
"""
Convert a Markdown document into WordPress (Gutenberg) block format.

Handles exactly the constructs the SOMA tutorials use: ATX headings (h1-h6),
fenced code blocks (```lang), unordered/ordered lists with soft-wrapped
continuation lines, pipe tables with a header separator, horizontal rules, and
paragraphs -- with inline `code`, **bold**, and *italic*. Content inside code
fences is treated verbatim (its #, -, | are never parsed as markdown) and is
HTML-escaped. Emits canonical core/* block comments so the output pastes into
the block editor and validates.
"""
from __future__ import annotations
import re
import sys


def esc(s: str) -> str:
    """HTML-escape text (for code blocks and as the base for inline text)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_CODE_SPAN = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def inline(text: str) -> str:
    """Render inline markdown (code, bold, italic) to safe HTML.

    Code spans are protected first (their contents escaped and wrapped), the
    surrounding text is then HTML-escaped, emphasis is applied, and the code
    spans are restored -- so asterisks or angle brackets inside `code` never
    trigger formatting or break the markup.
    """
    tokens: list[str] = []

    def stash(m: re.Match) -> str:
        tokens.append(f"<code>{esc(m.group(1))}</code>")
        return f"\x00{len(tokens) - 1}\x00"

    text = _CODE_SPAN.sub(stash, text)
    text = esc(text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], text)
    return text


def heading_block(level: int, text: str) -> list[str]:
    attr = "" if level == 2 else f' {{"level":{level}}}'
    return [f"<!-- wp:heading{attr} -->",
            f"<h{level}>{inline(text)}</h{level}>",
            "<!-- /wp:heading -->", ""]


def paragraph_block(text: str) -> list[str]:
    return ["<!-- wp:paragraph -->", f"<p>{inline(text)}</p>",
            "<!-- /wp:paragraph -->", ""]


def code_block(code_lines: list[str]) -> list[str]:
    body = esc("\n".join(code_lines))
    return ["<!-- wp:code -->",
            f'<pre class="wp-block-code"><code>{body}</code></pre>',
            "<!-- /wp:code -->", ""]


def list_block(items: list[str], ordered: bool) -> list[str]:
    tag = "ol" if ordered else "ul"
    attr = ' {"ordered":true}' if ordered else ""
    out = [f"<!-- wp:list{attr} -->", f"<{tag}>"]
    for it in items:
        out.append("<!-- wp:list-item -->")
        out.append(f"<li>{inline(it)}</li>")
        out.append("<!-- /wp:list-item -->")
    out += [f"</{tag}>", "<!-- /wp:list -->", ""]
    return out


def table_block(rows: list[list[str]]) -> list[str]:
    head, body = rows[0], rows[1:]
    fig = '<figure class="wp-block-table"><table><thead><tr>'
    fig += "".join(f"<th>{inline(c)}</th>" for c in head)
    fig += "</tr></thead><tbody>"
    for r in body:
        fig += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    fig += "</tbody></table></figure>"
    return ["<!-- wp:table -->", fig, "<!-- /wp:table -->", ""]


def separator_block() -> list[str]:
    return ["<!-- wp:separator -->",
            '<hr class="wp-block-separator has-alpha-channel-opacity"/>',
            "<!-- /wp:separator -->", ""]


HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^```(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
NUMBERED = re.compile(r"^(\d+)\.\s+(.*)$")
TABLE_ROW = re.compile(r"^\|(.*)\|\s*$")
TABLE_SEP = re.compile(r"^\|?[\s:|-]+\|?\s*$")
HR = re.compile(r"^(-{3,}|_{3,}|\*{3,})\s*$")


def split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    para: list[str] = []

    def flush_para():
        if para:
            out.extend(paragraph_block(" ".join(para)))
            para.clear()

    while i < n:
        line = lines[i]

        # fenced code block (verbatim; its contents are never parsed)
        m = FENCE.match(line)
        if m:
            flush_para()
            code: list[str] = []
            i += 1
            while i < n and not FENCE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.extend(code_block(code))
            continue

        # blank line: paragraph boundary
        if line.strip() == "":
            flush_para()
            i += 1
            continue

        # heading
        m = HEADING.match(line)
        if m:
            flush_para()
            out.extend(heading_block(len(m.group(1)), m.group(2).strip()))
            i += 1
            continue

        # horizontal rule
        if HR.match(line):
            flush_para()
            out.extend(separator_block())
            i += 1
            continue

        # table: a pipe row immediately followed by a separator row
        if TABLE_ROW.match(line) and i + 1 < n and TABLE_SEP.match(lines[i + 1]) \
                and "-" in lines[i + 1]:
            flush_para()
            rows = [split_row(line)]
            i += 2  # header + separator
            while i < n and TABLE_ROW.match(lines[i]):
                rows.append(split_row(lines[i]))
                i += 1
            out.extend(table_block(rows))
            continue

        # list (unordered or ordered), with soft-wrapped continuation lines
        bm, nm = BULLET.match(line), NUMBERED.match(line)
        if bm or nm:
            flush_para()
            ordered = bool(nm)
            items: list[str] = [(nm.group(2) if nm else bm.group(1)).strip()]
            i += 1
            while i < n:
                nxt = lines[i]
                if nxt.strip() == "":
                    break
                b2, n2 = BULLET.match(nxt), NUMBERED.match(nxt)
                if (ordered and n2) or (not ordered and b2):
                    items.append((n2.group(2) if n2 else b2.group(1)).strip())
                    i += 1
                elif nxt[:1] in (" ", "\t"):        # continuation of current item
                    items[-1] += " " + nxt.strip()
                    i += 1
                else:
                    break
            out.extend(list_block(items, ordered))
            continue

        # otherwise: accumulate into the current paragraph
        para.append(line.strip())
        i += 1

    flush_para()
    # collapse the trailing blank the block builders leave behind
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def main(argv):
    src, dst = argv[1], argv[2]
    with open(src, encoding="utf-8") as f:
        md = f.read()
    html = convert(md)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {dst} ({len(html)} bytes)")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
