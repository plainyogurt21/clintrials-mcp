#!/usr/bin/env python3
"""
Integration tests for mcp_server tools using the live ClinicalTrials.gov API.
Runs with the project's virtualenv Python.
"""

import sys
from typing import Any, Dict, List

from mcp_server import api_client, SEARCH_RESULT_FIELDS, _summarize_studies


SUMMARY_KEYS = {
    "nctId",
    "briefTitle",
    "acronym",
    "interventions",
    "conditions",
    "phases",
    "sponsors",
    "hasResults",
}


def assert_summary_shape(result: Dict[str, Any], label: str) -> List[str]:
    studies = result.get("studies", []) or []
    print(f"{label}: {len(studies)} studies")
    if not isinstance(studies, list):
        raise AssertionError(f"{label}: 'studies' is not a list")
    if studies:
        missing = SUMMARY_KEYS - set(studies[0].keys())
        if missing:
            raise AssertionError(f"{label}: summary keys missing: {sorted(missing)}")
    return [s.get("nctId") for s in studies if isinstance(s.get("nctId"), str)]


def main() -> int:
    # 1) Condition search
    raw = api_client.search_studies(conditions=["diabetes"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    cond_res = {"studies": _summarize_studies(raw.get("studies", []))}
    cond_ids = assert_summary_shape(cond_res, "search_trials_by_condition")

    # 2) Intervention search
    raw = api_client.search_studies(interventions=["aspirin"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    intr_res = {"studies": _summarize_studies(raw.get("studies", []))}
    intr_ids = assert_summary_shape(intr_res, "search_trials_by_intervention")

    # 3) Sponsor search
    raw = api_client.search_studies(sponsors=["Pfizer"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    spons_res = {"studies": _summarize_studies(raw.get("studies", []))}
    spons_ids = assert_summary_shape(spons_res, "search_trials_by_sponsor")

    # 4) Acronym search via titles + local filter
    raw = api_client.search_studies(titles=["TETON"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    # filter like tool does
    filtered = []
    targets = {"teton"}
    for study in raw.get("studies", []) or []:
        protocol = study.get("protocolSection", {}) or {}
        ident = protocol.get("identificationModule", {}) or {}
        acr = ident.get("acronym")
        if isinstance(acr, str) and any(t in acr.lower() for t in targets):
            filtered.append(study)
    acr_res = {"studies": _summarize_studies(filtered)}
    acr_ids = assert_summary_shape(acr_res, "search_trials_by_acronym")

    # 5) Combined search (conditions + acronyms via titles)
    raw = api_client.search_studies(conditions=["diabetes"], titles=["TETON"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    comb_res = {"studies": _summarize_studies(raw.get("studies", []))}
    comb_ids = assert_summary_shape(comb_res, "search_trials_combined")

    # 6) NCT IDs only search
    raw = api_client.search_studies(conditions=["diabetes"], max_studies=10, fields=SEARCH_RESULT_FIELDS)
    nct_only_res = {"studies": _summarize_studies(raw.get("studies", []))}
    nct_only_ids = assert_summary_shape(nct_only_res, "search_trials_nct_ids_only")

    # Collate some IDs for details
    pool = cond_ids or intr_ids or spons_ids or acr_ids or comb_ids or nct_only_ids
    if not pool:
        print("No NCT IDs found in discovery searches; cannot proceed to details.")
        return 1

    # 7) Get single trial details
    first_id = pool[0]
    detail_one = api_client.get_study_by_id(first_id)
    if not isinstance(detail_one, dict) or (
        "studies" not in detail_one and "protocolSection" not in detail_one
    ):
        raise AssertionError("get_trial_details: unexpected shape")
    print(f"get_trial_details: retrieved details for {first_id}")

    # 8) Batched details (replicate tool)
    batch_ids = pool[:10]
    ordered = []
    for i in range(0, len(batch_ids), 10):
        part = batch_ids[i:i+10]
        page = api_client.search_studies(nct_ids=part, fields=None, max_studies=len(part))
        ordered.extend(page.get("studies", []))
    if not ordered:
        raise AssertionError("get_trial_details_batched: no studies returned")
    print(f"get_trial_details_batched: retrieved {len(ordered)} studies")

    # 9) Search by NCT IDs directly (using those collected)
    raw = api_client.search_studies(nct_ids=batch_ids, max_studies=len(batch_ids), fields=SEARCH_RESULT_FIELDS)
    by_ids = {"studies": _summarize_studies(raw.get("studies", []))}
    ids_from_res = assert_summary_shape(by_ids, "search_trials_by_nct_ids")
    if not ids_from_res:
        raise AssertionError("search_trials_by_nct_ids: no studies returned")

    print("All integration checks completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
