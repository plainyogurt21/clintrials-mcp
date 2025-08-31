#!/usr/bin/env python3
"""
Targeted integration test for TETON-IPF trials:
- Search titles for "TETON" and intervention "Treprostinil"
- Exercise each search method, normalize results, and fetch details in batches
"""

from typing import Any, Dict, List

from mcp_server import api_client, SEARCH_RESULT_FIELDS, _summarize_studies


def summarize(label: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    studies = raw.get("studies", []) or []
    out = {"studies": _summarize_studies(studies)}
    print(f"{label}: {len(out['studies'])} studies")
    for s in out["studies"][:5]:
        print(f"  - {s.get('nctId')} | {s.get('acronym')} | {s.get('briefTitle')}")
    return out


def filter_teton_trepo(summaries: Dict[str, Any]) -> Dict[str, Any]:
    filtered: List[Dict[str, Any]] = []
    for s in summaries.get("studies", []) or []:
        title = (s.get("briefTitle") or "").lower()
        acr = (s.get("acronym") or "").lower()
        intrs = [i.lower() for i in (s.get("interventions") or [])]
        if ("teton" in title or "teton" in acr) and any("treprostinil" in i for i in intrs):
            filtered.append(s)
    print(f"Filtered TETON + Treprostinil: {len(filtered)} studies")
    return {"studies": filtered}


def main() -> int:
    # 1) Combined titles + intervention (primary target)
    raw = api_client.search_studies(titles=["TETON"], interventions=["Treprostinil"], max_studies=50, fields=SEARCH_RESULT_FIELDS)
    comb_res = summarize("combined[titles=TETON, intr=Treprostinil]", raw)

    # 2) Acronym/title-based (titles only), then filter by Treprostinil locally
    raw = api_client.search_studies(titles=["TETON"], max_studies=50, fields=SEARCH_RESULT_FIELDS)
    acro_res = summarize("acronym/title[titles=TETON]", raw)
    acro_res = filter_teton_trepo(acro_res)

    # 3) Intervention-only, then filter by TETON in title/acronym
    raw = api_client.search_studies(interventions=["Treprostinil"], max_studies=50, fields=SEARCH_RESULT_FIELDS)
    intr_res = summarize("intervention[intr=Treprostinil]", raw)
    intr_filtered = []
    for s in intr_res.get("studies", []):
        title = (s.get("briefTitle") or "").lower()
        acr = (s.get("acronym") or "").lower()
        if "teton" in title or "teton" in acr:
            intr_filtered.append(s)
    intr_res = {"studies": intr_filtered}
    print(f"Filtered intervention + TETON: {len(intr_res['studies'])} studies")

    # 4) Condition-based (IPF), then filter by TETON + Treprostinil
    raw = api_client.search_studies(conditions=["Idiopathic Pulmonary Fibrosis"], max_studies=50, fields=SEARCH_RESULT_FIELDS)
    cond_res = summarize("condition[IPF]", raw)
    cond_res = filter_teton_trepo(cond_res)

    # 5) Sponsor-based (United Therapeutics), then filter by TETON + Treprostinil
    raw = api_client.search_studies(sponsors=["United Therapeutics"], max_studies=50, fields=SEARCH_RESULT_FIELDS)
    spons_res = summarize("sponsor[United Therapeutics]", raw)
    spons_res = filter_teton_trepo(spons_res)

    # 6) NCT IDs only (reuse combined), then details batched
    teton_ids = [s.get("nctId") for s in comb_res.get("studies", []) if isinstance(s.get("nctId"), str)]
    if not teton_ids:
        # Fallback to any found in the filtered sets
        for res in (acro_res, intr_res, cond_res, spons_res):
            teton_ids.extend([s.get("nctId") for s in res.get("studies", []) if isinstance(s.get("nctId"), str)])

    teton_ids = list(dict.fromkeys(teton_ids))  # dedupe, preserve order
    print(f"Collected TETON IDs: {teton_ids[:10]}")

    if teton_ids:
        # Details for first up to 10
        chunk = teton_ids[:10]
        detail = api_client.search_studies(nct_ids=chunk, fields=None, max_studies=len(chunk))
        print(f"Fetched details for {len(detail.get('studies', []))} studies (batched)")

    # Summary assertion: ensure we found at least one match
    total_matches = sum(len(res.get("studies", [])) for res in (comb_res, acro_res, intr_res, cond_res, spons_res))
    if total_matches == 0:
        print("No TETON + Treprostinil trials found in this run.")
        return 2

    print("TETON-IPF targeted checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

