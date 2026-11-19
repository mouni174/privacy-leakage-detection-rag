"""
pages/4_Privacy_Audit.py
-------------------------
Feature 5 – Privacy Audit Trail & Compliance Log.

Purpose: Review privacy events.
Includes:
  • Total audited queries
  • Blocked requests
  • Redacted requests
  • Clean requests allowed
  • Audit history table
  • CSV export

Never exposes raw sensitive PII in the audit log or exported CSV.
"""

from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Privacy Audit – Privacy RAG",
    page_icon="📜",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────────────────────────
init_session_state()

# ── Page title & description ───────────────────────────────────────────────────
st.title("📜 Privacy Audit Trail")
st.markdown(
    "A session-scoped, privacy-safe compliance log of all queries processed by the system. "
    "**Zero raw PII is ever recorded or exported.** "
    "Only detection counts, entity categories, and sanitized query text are captured."
)

st.markdown("---")

# ── No records yet ─────────────────────────────────────────────────────────────
if not st.session_state.audit_log:
    st.info(
        "📭 **No audit records found.** "
        "Submit queries on the **🔍 RAG Query** page to automatically populate this audit log."
    )
    st.stop()

# ── Summary KPIs ───────────────────────────────────────────────────────────────
audit_log = st.session_state.audit_log

total_audited = len(audit_log)
total_blocked = sum(1 for a in audit_log if a.get("Guardrail Action") == "Blocked")
total_redacted = sum(1 for a in audit_log if a.get("Guardrail Action") == "Redacted")
total_allowed = sum(1 for a in audit_log if a.get("Guardrail Action") == "Allowed")

st.subheader("📊 Audit Overview")

a_col1, a_col2, a_col3, a_col4 = st.columns(4)
a_col1.metric("Total Audited Queries", total_audited)
a_col2.metric("Blocked Requests 🔴", total_blocked)
a_col3.metric("Redacted Requests 🟡", total_redacted)
a_col4.metric("Clean Requests Allowed 🟢", total_allowed)

st.markdown("---")

# ── Audit history table ────────────────────────────────────────────────────────
st.subheader("🗂️ Audit History Table")

df_audit = pd.DataFrame(audit_log)

st.dataframe(
    df_audit,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ── CSV export ─────────────────────────────────────────────────────────────────
st.subheader("📥 Export Audit Log")

csv_data = df_audit.to_csv(index=False).encode("utf-8")
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

col_btn, col_info = st.columns([1, 2])

with col_btn:
    st.download_button(
        label="📥 Export Audit Log (CSV)",
        data=csv_data,
        file_name=f"privacy_audit_report_{timestamp_str}.csv",
        mime="text/csv",
        key="export_audit_csv",
        help="Export the privacy-sanitized session audit trail as a CSV file. Contains zero raw PII.",
        use_container_width=True,
        type="primary"
    )

with col_info:
    st.caption(
        "🔒 **Privacy Guarantee:** Exported audit logs strictly contain token counts, sanitized query text, "
        "and policy classifications. Confidential entity values are excised before logging."
    )
