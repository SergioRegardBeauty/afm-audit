"""Discovery complet de l'API SOAP B2T Atlas For Men.

Parcourt le WSDL via zeep et génère un Markdown structuré listant :
  - Chaque opération avec sa SOAPAction
  - Les paramètres d'entrée (nom + type)
  - La structure de retour (champs + types)
  - Les types complexes utilisés

Usage :
    python tools/b2t_discovery.py
    → écrit docs/B2T_API_DISCOVERY.md
"""
from __future__ import annotations

from pathlib import Path

import zeep
from zeep.helpers import serialize_object  # noqa: F401

WSDL_URL = "http://192.168.23.28/AFM/WS/WsCustomer/crmservices.svc?wsdl"
OUT_FILE = Path(__file__).resolve().parent.parent / "docs" / "B2T_API_DISCOVERY.md"
OUT_FILE.parent.mkdir(exist_ok=True)


def describe_type(t, indent=0, seen=None) -> list[str]:
    """Rendu lisible d'un type zeep (complexe ou simple)."""
    if seen is None:
        seen = set()
    pad = "  " * indent
    name = getattr(t, "name", None) or getattr(t, "qname", None) or repr(t)
    type_key = str(name)
    if type_key in seen:
        return [f"{pad}- _(cycle vers {name})_"]
    seen = seen | {type_key}

    lines: list[str] = []
    # ComplexType avec attributs (Sequence)
    if hasattr(t, "elements") and t.elements:
        for child_name, child_elt in t.elements:
            child_type = child_elt.type
            child_type_name = getattr(child_type, "name", None) or getattr(child_type, "qname", "?")
            min_occurs = getattr(child_elt, "min_occurs", "1")
            max_occurs = getattr(child_elt, "max_occurs", "1")
            occur = ""
            if str(min_occurs) == "0":
                occur = " _(optionnel)_"
            elif max_occurs == "unbounded" or (isinstance(max_occurs, int) and max_occurs > 1):
                occur = " _(liste)_"
            lines.append(f"{pad}- **`{child_name}`** : `{child_type_name}`{occur}")
            # Récursion sur les complex types
            if (hasattr(child_type, "elements") and child_type.elements
                    and indent < 3 and str(child_type_name) not in seen):
                lines.extend(describe_type(child_type, indent + 1, seen))
    elif hasattr(t, "accepted_types") and t.accepted_types:
        for at in t.accepted_types:
            lines.append(f"{pad}- _accepted type_ : `{at.__name__}`")
    else:
        lines.append(f"{pad}- _(type simple : `{name}`)_")
    return lines


def main():
    print(f"Loading WSDL from {WSDL_URL} ...")
    client = zeep.Client(wsdl=WSDL_URL)

    md = ["# B2T crmservices — Discovery API SOAP", ""]
    md.append(f"_WSDL : `{WSDL_URL}`_\n")
    md.append("_Généré par `tools/b2t_discovery.py` via `zeep`._\n")
    md.append("---\n")

    for service in client.wsdl.services.values():
        md.append(f"## Service : `{service.name}`\n")
        for port in service.ports.values():
            binding = port.binding
            md.append(f"### Port : `{port.name}`")
            md.append(f"- Binding : `{binding.name}`")
            md.append(f"- Endpoint : `{port.binding_options['address']}`\n")

            operations = sorted(binding._operations.items())
            md.append(f"**{len(operations)} opérations** disponibles dans ce binding :\n")

            # Table récap
            md.append("| Opération | SOAPAction | Use case |")
            md.append("|---|---|---|")
            for op_name, op in operations:
                soap_action = getattr(op, "soapaction", "") or "(none)"
                short = soap_action.split("/")[-1] if "/" in soap_action else soap_action
                md.append(f"| `{op_name}` | `…/{short}` | _(voir détail ci-dessous)_ |")
            md.append("")

            # Détail par opération
            for op_name, op in operations:
                md.append(f"#### 🔹 `{op_name}`")
                md.append(f"- **SOAPAction** : `{op.soapaction}`")
                md.append(f"- **Style** : `{op.style}`")

                # Input
                md.append("- **Input** :")
                if op.input.body and hasattr(op.input.body, "type"):
                    md.extend(describe_type(op.input.body.type, indent=1))
                else:
                    md.append("  - _(pas d'input documenté)_")

                # Output
                md.append("- **Output** :")
                if op.output and op.output.body and hasattr(op.output.body, "type"):
                    md.extend(describe_type(op.output.body.type, indent=1))
                else:
                    md.append("  - _(pas d'output documenté)_")

                md.append("")

    # Types complexes globaux
    md.append("---\n")
    md.append("## Types complexes globaux (data contracts)\n")
    try:
        complex_types = []
        for prefix, namespace in client.wsdl.types.prefix_map.items():
            for t in client.wsdl.types.get_types(namespace) or []:
                if hasattr(t, "elements") and t.elements and getattr(t, "name", None):
                    complex_types.append(t)
        complex_types.sort(key=lambda t: t.name)
        for t in complex_types[:60]:  # cap à 60 pour ne pas exploser le fichier
            md.append(f"### `{t.name}`")
            md.extend(describe_type(t, indent=0))
            md.append("")
        if len(complex_types) > 60:
            md.append(f"_… {len(complex_types) - 60} types complexes additionnels non affichés_")
    except Exception as e:
        md.append(f"_(erreur listing types : {e})_")

    OUT_FILE.write_text("\n".join(md), encoding="utf-8")
    print(f"\n✅ Wrote {OUT_FILE}  ({OUT_FILE.stat().st_size / 1024:.1f} KB)")
    print(f"   Opérations totales : {len(operations)}")


if __name__ == "__main__":
    main()
