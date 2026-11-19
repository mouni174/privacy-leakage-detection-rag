"""Privacy-safe query audit workspace and CSV exports."""

from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.ui import (
    apply_global_styles,
    render_empty_state,
    render_page_header,
    render_section_heading,
    render_sidebar_brand,
    sanitize_sensitive_text,
)

load_dotenv()

st.set_page_config(
    page_title="Privacy Audit | Privacy RAG",
    page_icon=":material/receipt_long:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

audit_log = []
for existing_record in st.session_state.audit_log:
    safe_record = dict(existing_record)
    for field in ("Sanitized Query", "Target Scope", "Source Documents"):
        value = safe_record.get(field)
        if value and not (field == "Target Scope" and value == "All Documents"):
            safe_record[field] = sanitize_sensitive_text(value)
    audit_log.append(safe_record)
total_audited = len(audit_log)
total_blocked = sum(
    1 for entry in audit_log if entry.get("Guardrail Action") == "Blocked"
)
total_redacted = sum(
    1 for entry in audit_log if entry.get("Guardrail Action") == "Redacted"
)

render_page_header(
    title="Privacy audit",
    description=(
        "Search and review this session's query history. The ledger displays sanitized "
        "query text, detector counts, policy decisions, and source metadata—not detected "
        "sensitive values."
    ),
    eyebrow="04 / Governance ledger",
    icon="receipt_long",
    status_label=f"{total_audited} events · {total_blocked} blocked",
)

if not audit_log:
    render_empty_state(
        eyebrow="AUDIT LEDGER",
        title="No audit records yet",
        description=(
            "Only real guarded query events appear here. Run a query to create a "
            "record with sanitized query text, policy decisions, and detection "
            "metadata; no example records are inserted."
        ),
        icon="history",
        steps=(
            "Index a PDF in Document Management.",
            "Run a guarded query and review its result.",
            "Return here to search, filter, and export session records.",
        ),
        actions=(
            (
                "pages/1_Document_Management.py",
                "Manage Documents",
                "folder_managed",
            ),
            ("pages/2_RAG_Query.py", "Open Secure RAG Query", "forum"),
        ),
    )
    st.stop()

with st.container(horizontal=True):
    st.metric("Audited queries", total_audited, border=True)
    st.metric("Blocked requests", total_blocked, border=True)
    st.metric("Redacted requests", total_redacted, border=True)

st.space("small")
render_section_heading(
    "Event search and filters",
    "Search operates on sanitized query text and audit metadata. Detected values are not searchable or displayed.",
)

with st.container(border=True):
    st.markdown('<div class="pld-story-index">NARROW THE LEDGER</div>', unsafe_allow_html=True)
    search_text = st.text_input(
        "Search records",
        placeholder="Search sanitized query, source, or category",
        key="audit_search",
    ).strip().casefold()

    action_values = sorted(
        {entry.get("Guardrail Action", "") for entry in audit_log if entry.get("Guardrail Action")}
    )
    policy_values = sorted(
        {entry.get("Privacy Policy", "") for entry in audit_log if entry.get("Privacy Policy")}
    )
    risk_values = sorted(
        {entry.get("Risk Status", "") for entry in audit_log if entry.get("Risk Status")}
    )
    action_filter, policy_filter, risk_filter = st.columns(3, gap="medium")
    with action_filter:
        selected_action = st.selectbox(
            "Guardrail action",
            ["All actions", *action_values],
            key="audit_action_filter",
        )
    with policy_filter:
        selected_policy = st.selectbox(
            "Privacy policy",
            ["All policies", *policy_values],
            key="audit_policy_filter",
        )
    with risk_filter:
        selected_risk = st.selectbox(
            "Risk status",
            ["All risk levels", *risk_values],
            key="audit_risk_filter",
        )

filtered_records = []
for record in audit_log:
    if selected_action != "All actions" and record.get("Guardrail Action") != selected_action:
        continue
    if selected_policy != "All policies" and record.get("Privacy Policy") != selected_policy:
        continue
    if selected_risk != "All risk levels" and record.get("Risk Status") != selected_risk:
        continue

    searchable_text = " ".join(
        str(record.get(field, ""))
        for field in (
            "Timestamp",
            "Sanitized Query",
            "Target Scope",
            "Source Documents",
            "Detected Categories",
            "Privacy Policy",
            "Guardrail Action",
            "Risk Status",
        )
    ).casefold()
    if search_text and search_text not in searchable_text:
        continue
    filtered_records.append(record)

st.caption(
    f"Showing {len(filtered_records)} of {total_audited} session record(s)."
)

st.space("small")
render_section_heading(
    "Audit records",
    "Each record preserves the guardrail decision and detection totals without exposing finding values.",
)

if not filtered_records:
    with st.container(border=True):
        st.info("No records match the current search and filter selection.")
else:
    for record in reversed(filtered_records):
        with st.container(border=True):
            header_columns = st.columns([3, 1], vertical_alignment="center")
            with header_columns[0]:
                st.markdown(
                    f"#### :material/event_note: {record.get('Timestamp', 'Timestamp unavailable')}"
                )
            with header_columns[1]:
                action = record.get("Guardrail Action", "Unknown")
                action_color = {
                    "Blocked": "red",
                    "Redacted": "orange",
                    "Allowed": "green",
                }.get(action, "gray")
                st.badge(action, color=action_color)

            st.markdown("**Sanitized query**")
            st.markdown(f"> {record.get('Sanitized Query') or '[No query text recorded]'}")

            detail_columns = st.columns([1, 1.4, 1, 1], vertical_alignment="top")
            with detail_columns[0]:
                st.markdown("**Target scope**")
                st.write(record.get("Target Scope", "—"))
            with detail_columns[1]:
                st.markdown("**Source documents**")
                st.write(record.get("Source Documents", "—"))
            with detail_columns[2]:
                st.markdown("**Detection totals**")
                st.write(
                    f"{record.get('Total Sensitive Items', 0)} total · "
                    f"{record.get('Regex Finding Count', 0)} regex · "
                    f"{record.get('NER Finding Count', 0)} NER"
                )
            with detail_columns[3]:
                st.markdown("**Policy / model**")
                st.write(
                    f"{record.get('Privacy Policy', '—')}  \n"
                    f"LLM: {record.get('LLM Invoked', '—')}"
                )

            detected_categories = record.get("Detected Categories", "None")
            st.caption(
                f"Risk: {record.get('Risk Status', '—')} · "
                f"Categories: {detected_categories}"
            )
            st.caption(
                f"Policy rationale: {record.get('Policy Rationale', '—')} · "
                f"Generation: {record.get('Generation Status', '—')}"
            )

st.space("small")
render_section_heading(
    "Export records",
    "Download the full session log or only the records matching the current filters.",
)

full_csv = pd.DataFrame(audit_log).to_csv(index=False).encode("utf-8")
filtered_csv = pd.DataFrame(filtered_records).to_csv(index=False).encode("utf-8")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

export_columns = st.columns([1, 1.4], vertical_alignment="center")
with export_columns[0]:
    st.download_button(
        label="Export full audit log",
        data=full_csv,
        file_name=f"privacy_audit_report_{timestamp}.csv",
        mime="text/csv",
        key="export_audit_csv",
        type="primary",
        width="stretch",
        help="Export all privacy-safe audit records from this session.",
    )
with export_columns[1]:
    st.download_button(
        label="Export filtered records",
        data=filtered_csv,
        file_name=f"privacy_audit_filtered_{timestamp}.csv",
        mime="text/csv",
        key="export_filtered_audit_csv",
        width="stretch",
        disabled=not filtered_records,
        help="Export only records matching the current search and filters.",
    )

st.caption(
    "Export contents: sanitized query text, detection counts, categories, and policy "
    "classifications. Raw retrieved context and detected values are not included in "
    "the exported audit records."
)
