"""Shared tag list (taxonomy) for the Discovery Engine (Step 5) AND the MVP (Step 9).

Both must import from here so one golden set can evaluate both.
Every tag maps to a node of the metric decomposition (see step2_decomposition.md).
"""

# ---------------------------------------------------------------- decomposition nodes
NODES = {
    "A": "SIP goes live (mandate/autopay setup, first instalment)",
    "B": "Instalments keep succeeding (INVOLUNTARY lapse)",
    "C": "User chooses to continue (VOLUNTARY lapse)",
    "D": "Re-entry / switching (restart or new SIP = still retained)",
    "E": "Engagement behaviour (diagnostic only)",
    "X": "Not mapped to the metric",
}

# ---------------------------------------------------------------- lifecycle stage
LIFECYCLE_STAGES = {
    "pre_start": "Thinking about or setting up a first SIP; no instalment yet",
    "m0_1": "First month: first instalment / mandate just set up",
    "m2_6": "Months 2-6 of the SIP",
    "m7_12": "Months 7-12 of the SIP",
    "m12_plus": "More than 12 months in",
    "unknown": "Timing not stated or not inferable",
}

# ---------------------------------------------------------------- action
ACTIONS = {
    "started":            ("Started / set up a SIP", "A"),
    "setup_failed":       ("Tried to start but mandate/first payment failed", "A"),
    "checking":           ("Checking value/returns, no decision mentioned", "E"),
    "considering_stop":   ("Thinking about pausing, reducing or stopping", "C"),
    "paused":             ("Paused / skipped instalments", "C"),
    "reduced":            ("Lowered the SIP amount", "C"),
    "stopped":            ("Cancelled the SIP", "C"),
    "lapsed_involuntary": ("SIP stopped/failed without the user choosing to (bounce, mandate, auto-cancel)", "B"),
    "redeemed":           ("Withdrew money (with or without stopping)", "C"),
    "continued":          ("Kept going, incl. through a dip or doubt", "C"),
    "restarted":          ("Restarted after a stop/pause, or switched to a new SIP", "D"),
    "unknown":            ("No clear action", "X"),
}

# ---------------------------------------------------------------- trigger (the main tag)
TRIGGERS = {
    "expectation_gap":   ("Returns lower/slower than they expected when starting", "C"),
    "negative_returns":  ("Portfolio is red / flat; market fall", "C"),
    "confusing_numbers": ("Doesn't understand XIRR, NAV, returns %, current vs invested value", "C"),
    "liquidity_need":    ("Needed the money (emergency, expense, purchase)", "C"),
    "income_change":     ("Job loss, salary delay, irregular / stopped income", "C"),
    "payment_failure":   ("Mandate/autopay failure, insufficient balance, bank change, debit-date issue", "B"),
    "setup_friction":    ("Problems setting up mandate / first instalment / KYC for the SIP", "A"),
    "app_trust_issue":   ("App bugs, wrong data, support problems, doubts about platform safety", "C"),
    "peer_influence":    ("Friend, family, YouTuber, Reddit or advisor told them to stop/switch", "C"),
    "goal_reached":      ("Goal achieved or time horizon ended", "C"),
    "no_goal":           ("No clear reason/goal for investing, lost motivation", "C"),
    "too_many_sips":     ("Too many SIPs/funds, consolidating", "D"),
    "fund_switch":       ("Moving to a different fund/SIP (still investing)", "D"),
    "other":             ("Clear trigger that fits none of the above", "X"),
    "none":              ("No trigger stated", "X"),
}

# ---------------------------------------------------------------- segment signals (only if EXPLICIT)
SEGMENT_SIGNALS = {
    "age_band": ["<21", "21-27", "28-35", "36+", "unknown"],
    "income_type": ["student", "salaried", "gig_freelance", "business", "unknown"],
    "source_of_money": ["salary", "stipend_pocket_money", "family", "savings_bonus", "unknown"],
    "influencer": ["friend_family", "youtube_social", "reddit_forum", "advisor_ca", "app_prompt", "none", "unknown"],
}

# ---------------------------------------------------------------- MVP-only labels (Step 4 / Step 9)
SAFE_BEHAVIOURS = {
    "answer": "Educational, grounded answer is OK",
    "decline_advice": "Asks which fund / whether to stop -> polite decline + AMFI/SEBI advisor pointer",
    "not_sure_fallback": "Out of knowledge base / low confidence -> 'Not sure' + official link",
}


def node_for(trigger: str) -> str:
    """Decomposition node (A-E/X) for a trigger tag."""
    return TRIGGERS.get(trigger, ("", "X"))[1]


def validate(record: dict) -> list[str]:
    """Return a list of problems with one tagged record (empty list = valid)."""
    errs = []
    if record.get("lifecycle_stage") not in LIFECYCLE_STAGES:
        errs.append(f"bad lifecycle_stage: {record.get('lifecycle_stage')}")
    if record.get("action") not in ACTIONS:
        errs.append(f"bad action: {record.get('action')}")
    if record.get("trigger") not in TRIGGERS:
        errs.append(f"bad trigger: {record.get('trigger')}")
    for k, allowed in SEGMENT_SIGNALS.items():
        v = (record.get("segment_signals") or {}).get(k, "unknown")
        if v not in allowed:
            errs.append(f"bad segment_signals.{k}: {v}")
    return errs


def prompt_block() -> str:
    """Taxonomy as text, to paste into LLM prompts (engine + MVP classifier)."""
    def fmt(d):
        return "\n".join(f"  - {k}: {v[0] if isinstance(v, tuple) else v}" for k, v in d.items())
    seg = "\n".join(f"  - {k}: {', '.join(v)}" for k, v in SEGMENT_SIGNALS.items())
    return (
        f"lifecycle_stage (pick one):\n{fmt(LIFECYCLE_STAGES)}\n\n"
        f"action (pick one):\n{fmt(ACTIONS)}\n\n"
        f"trigger (pick the MAIN one):\n{fmt(TRIGGERS)}\n\n"
        f"segment_signals (fill ONLY if explicitly stated, else 'unknown'):\n{seg}\n\n"
        "Rules: do not assume 'negative_returns' just because the user stopped; "
        "if money was not available on the debit date, use 'payment_failure' or 'income_change'."
    )


if __name__ == "__main__":
    print(f"{len(LIFECYCLE_STAGES)} stages, {len(ACTIONS)} actions, {len(TRIGGERS)} triggers")
    sample = {"lifecycle_stage": "m2_6", "action": "stopped", "trigger": "expectation_gap",
              "segment_signals": {"income_type": "student"}}
    print("sample valid:", validate(sample) == [], "| node:", node_for(sample["trigger"]))
    print(validate({"lifecycle_stage": "x", "action": "stopped", "trigger": "market"}))
