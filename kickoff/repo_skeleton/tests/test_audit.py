"""Tests basiques pour valider le pipeline avant intégration LLM."""
from __future__ import annotations

import pytest

from afm_audit.audit import detect_flow, detect_pays_langue, parse_csv_transcript


def test_detect_pays_fr():
    pays, lang = detect_pays_langue("00330892799800_20260105192055.mp3.csv")
    assert pays == "FR" and lang == "fr"


def test_detect_pays_gb():
    pays, lang = detect_pays_langue("004408706315429_20260102174519.mp3.csv")
    assert pays == "GB" and lang == "en"


def test_detect_pays_de():
    pays, lang = detect_pays_langue("004908003313322_20260102184216.mp3.csv")
    assert pays == "DE" and lang == "de"


def test_detect_flow_sav():
    assert detect_flow("Je voudrais un remboursement svp") == "sav"
    assert detect_flow("I want to return my order") == "sav"
    assert detect_flow("Erstattung bitte") == "sav"


def test_detect_flow_cde_tel():
    assert detect_flow("Bonjour je voudrais passer commande") == "cde_tel"
    assert detect_flow("Hello, place an order please") == "cde_tel"


def test_parse_csv_basic():
    csv_content = (
        "Number;Speaker;Start time;End time;Duration;Text\n"
        "0;Orateur 1;00:00:01.000;00:00:05.000;00:00:04.000;\"Bonjour Atlas for Men\"\n"
        "1;Orateur 2;00:00:06.000;00:00:10.000;00:00:04.000;\"Bonjour\"\n"
    )
    parsed = parse_csv_transcript(csv_content)
    assert "Bonjour" in parsed.text
    assert parsed.duree >= 8
