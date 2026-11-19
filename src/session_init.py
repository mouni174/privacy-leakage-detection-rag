"""
session_init.py
---------------
Shared session-state initializer for all Streamlit pages.

Call `init_session_state()` at the top of every page to guarantee
all required keys exist regardless of which page the user opens first.
Existing values are never overwritten.
"""

import streamlit as st


def init_session_state() -> None:
    """Initialize all application session-state keys with safe defaults."""

    defaults: dict = {
        # Feature 3 – Document Registry
        # Key: filename  →  dict(chunks_count=int, sanitized_bytes=bytes|None)
        "documents": {},

        # Set of already-processed filenames (prevents re-indexing on rerun)
        "processed_files": set(),

        # Whether the Chroma DB has at least one indexed document
        "database_ready": False,

        # Feature 3 – Query scope (persists across page navigation)
        "selected_scope": "All Documents",

        # Feature 1 – Privacy policy (persists across page navigation)
        "privacy_policy": "Redact & Continue",

        # Feature 5 – Audit trail (in-memory session list of dicts)
        "audit_log": [],

        # Feature 4 – Latest query telemetry & findings for Privacy Dashboard
        "last_query_result": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
