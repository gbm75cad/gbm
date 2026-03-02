#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin



@dataclass
class Notice:
    source: str
    title: str
    link: str
    published_at: datetime | None


def load_config(path: Path) -> dict[str, Any]:
    import yaml

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: Path, state: dict[str, list[str]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def parse_date(raw: str, fmt: str | None) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if fmt:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            return None
    for candidate in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, candidate)
        except ValueError:
            continue
    return None


def extract_text(node) -> str:
    if node is None:
        return ""
    return " ".join(node.get_text(separator=" ", strip=True).split())


def collect_source(source_cfg: dict[str, Any]) -> list[Notice]:
    import requests
    from bs4 import BeautifulSoup

    name = source_cfg["name"]
    url = source_cfg["url"]

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(source_cfg["item_selector"])

    notices: list[Notice] = []
    for item in items:
        title_node = item.select_one(source_cfg.get("title_selector", "")) if source_cfg.get("title_selector") else item
        title = extract_text(title_node)

        link = url
        link_selector = source_cfg.get("link_selector")
        if link_selector:
            link_node = item.select_one(link_selector)
            if link_node and link_node.has_attr("href"):
                link = urljoin(url, link_node["href"])

        date_selector = source_cfg.get("date_selector")
        raw_date = ""
        if date_selector:
            raw_date = extract_text(item.select_one(date_selector))
        published_at = parse_date(raw_date, source_cfg.get("date_format"))

        if title:
            notices.append(
                Notice(
                    source=name,
                    title=title,
                    link=link,
                    published_at=published_at,
                )
            )

    return notices


def filter_by_keywords(notices: list[Notice], keywords: list[str]) -> list[Notice]:
    if not keywords:
        return notices
    lowered = [k.lower() for k in keywords]
    return [n for n in notices if any(k in n.title.lower() for k in lowered)]


def find_new_notices(notices: list[Notice], seen_links: set[str]) -> tuple[list[Notice], set[str]]:
    new_items: list[Notice] = []
    updated_seen = set(seen_links)

    for notice in notices:
        if notice.link in updated_seen:
            continue
        new_items.append(notice)
        updated_seen.add(notice.link)

    return new_items, updated_seen


def render_report(notices: list[Notice]) -> str:
    if not notices:
        return "# Relatório de licitações\n\nNenhuma nova licitação encontrada nesta execução.\n"

    lines = ["# Relatório de novas licitações", ""]
    for notice in sorted(notices, key=lambda n: n.published_at or datetime.min, reverse=True):
        date_str = notice.published_at.strftime("%d/%m/%Y") if notice.published_at else "sem data"
        lines.append(f"- **{notice.source}** | {date_str} | [{notice.title}]({notice.link})")

    lines.append("")
    return "\n".join(lines)


def run(config_path: Path, state_path: Path, output_path: Path) -> int:
    config = load_config(config_path)
    state = load_state(state_path)

    keywords = config.get("keywords", [])
    sources = config.get("sources", [])

    all_new: list[Notice] = []

    for source in sources:
        source_name = source["name"]
        notices = collect_source(source)
        notices = filter_by_keywords(notices, keywords)

        seen = set(state.get(source_name, []))
        new_items, updated_seen = find_new_notices(notices, seen)

        all_new.extend(new_items)
        state[source_name] = sorted(updated_seen)

    save_state(state_path, state)

    report = render_report(all_new)
    output_path.write_text(report, encoding="utf-8")

    print(f"Execução concluída. Novas licitações: {len(all_new)}")
    print(f"Relatório salvo em: {output_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitora páginas de licitações de prefeituras.")
    parser.add_argument("--config", default="config.yaml", type=Path, help="Arquivo YAML de configuração")
    parser.add_argument("--state", default="state.json", type=Path, help="Arquivo de estado com itens já vistos")
    parser.add_argument("--output", default="relatorio.md", type=Path, help="Arquivo de relatório em Markdown")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(run(args.config, args.state, args.output))
