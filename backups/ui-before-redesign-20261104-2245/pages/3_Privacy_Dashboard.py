"""Privacy telemetry for the latest guarded RAG query."""

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.ui import apply_global_styles, render_section_heading, render_sidebar_brand

load_dotenv()

st.set_page_config(
    page_title="Privacy Dashboard | Privacy RAG",
    page_icon=":material/shield:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

result = st.session_state.get("last_query_result")
audit_log = st.session_state.audit_log

if result:
    action = result["action"]
    state = "ready"
    state_label = f"Latest decision · {action}"
else:
    state = "empty"
    state_label = "Awaiting query telemetry"

st.markdown(
    f"""
    <section class="pld-hero">
        <div class="pld-hero-kicker">Live telemetry · privacy control plane</div>
        <h1 class="pld-hero-title">Privacy protection center</h1>
        <p class="pld-hero-copy">
            Inspect the latest query's detection coverage, guardrail decision, and
            source attribution. Findings are presented as categories and counts,
            never as the sensitive values themselves.
        </p>
        <div class="pld-hero-meta">
            <span class="pld-status-chip" data-state="{state}">
                <span class="pld-status-dot"></span>{state_label}
            </span>
            <span class="pld-meta-chip">{len(audit_log)} audited session quer{"y" if len(audit_log) == 1 else "ies"}</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.space("medium")

if not result:
    with st.container(border=True):
        st.markdown("### :material/radar: No query telemetry yet")
        st.write(
            "Run a query to populate this center with the real regex and NER results, "
            "privacy action, and source-document attribution."
        )
        st.page_link(
            "pages/2_RAG_Query.py",
            label="Open RAG Query",
            width="content",
        )

    if audit_log:
        st.space("small")
        render_section_heading(
            "Session activity",
            "Counts below are calculated from this session's actual audit records.",
        )
        total_queries = len(audit_log)
        total_blocked = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Blocked"
        )
        total_redacted = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Redacted"
        )
        total_allowed = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Allowed"
        )

        with st.container(horizontal=True):
            st.metric("Queries processed", total_queries, border=True)
            st.metric("Blocked", total_blocked, border=True)
            st.metric("Redacted", total_redacted, border=True)
            st.metric("Allowed", total_allowed, border=True)
    st.stop()

guardrail = result["guardrail"]
regex_findings = {
    category.replace("_", " ").title(): values
    for category, values in guardrail.get("regex_findings", {}).items()
    if values
}
ner_findings = {
    category: values
    for category, values in guardrail.get("ner_findings", {}).items()
    if values
}
retrieved_documents = result.get("documents", [])

render_section_heading(
    "Latest evaluation",
    f"Evaluated {result['timestamp']} · scope: {result['target_scope']} · "
    f"policy: {result['privacy_policy']}",
)

with st.container(border=True):
    st.markdown("**Sanitized query**")
    st.markdown(f"> {result.get('sanitized_query', '[Query unavailable]')}")
    st.caption(
        f"{len(retrieved_documents)} retrieved chunk(s) · "
        "raw query and source text are not displayed in this report"
    )

st.space("small")

with st.container(horizontal=True):
    st.metric("Sensitive findings", result["total_sensitive"], border=True)
    st.metric("Regex detections", result["regex_count"], border=True)
    st.metric("NER detections", result["ner_count"], border=True)
    st.metric("Guardrail action", result["action"], border=True)

if result["risk_status"].startswith("🟢"):
    st.success(f"**Risk assessment · {result['risk_badge']}** — {result['risk_desc']}")
elif result["risk_status"].startswith("🟡"):
    st.warning(f"**Risk assessment · {result['risk_badge']}** — {result['risk_desc']}")
else:
    st.error(f"**Risk assessment · {result['risk_badge']}** — {result['risk_desc']}")

st.space("small")
render_section_heading(
    "Detection coverage",
    "Actual findings from the latest guardrail evaluation, grouped by detection layer.",
)

detection_columns = st.columns(2, gap="large")
with detection_columns[0]:
    with st.container(border=True):
        st.markdown("### :material/regex: Pattern detection")
        st.caption("Regex-based structured identifier checks")
        if regex_findings:
            for category, findings in regex_findings.items():
                st.markdown(f"- **{category}** · {len(findings)} finding(s)")
        else:
            st.success("No regex categories were detected.")

with detection_columns[1]:
    with st.container(border=True):
        st.markdown("### :material/psychology: Entity detection")
        st.caption("spaCy named-entity recognition")
        if ner_findings:
            for category, findings in ner_findings.items():
                note = " · preserved by policy" if category == "DATE" else ""
                st.markdown(f"- **{category}** · {len(findings)} finding(s){note}")
        else:
            st.success("No named-entity categories were detected.")

st.space("small")
render_section_heading(
    "Source attribution",
    "Per-document counts for findings present in retrieved chunks; sensitive values are omitted.",
)

if retrieved_documents:
    document_findings = {}
    for document in retrieved_documents:
        source_name = document.metadata.get("source_doc", "Unknown document")
        entry = document_findings.setdefault(
            source_name,
            {
                "chunks": 0,
                "regex": set(),
                "ner": set(),
            },
        )
        entry["chunks"] += 1

        for category, findings in regex_findings.items():
            for finding in findings:
                if finding in document.page_content:
                    entry["regex"].add((category, finding))

        for category, findings in ner_findings.items():
            for finding in findings:
                if finding in document.page_content:
                    entry["ner"].add((category, finding))

    source_rows = []
    for source_name, findings in document_findings.items():
        regex_count = len(findings["regex"])
        ner_count = len(findings["ner"])
        total_findings = regex_count + ner_count
        source_rows.append(
            {
                "Source document": source_name,
                "Retrieved chunks": findings["chunks"],
                "Regex findings": regex_count,
                "NER findings": ner_count,
                "Assessment": "Findings detected" if total_findings else "No findings",
            }
        )

    with st.container(border=True):
        st.dataframe(
            source_rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Source document": st.column_config.TextColumn(
                    "Source document", width="large"
                ),
                "Retrieved chunks": st.column_config.NumberColumn(
                    "Chunks", width="small"
                ),
                "Regex findings": st.column_config.NumberColumn(
                    "Regex", width="small"
                ),
                "NER findings": st.column_config.NumberColumn(
                    "NER", width="small"
                ),
                "Assessment": st.column_config.TextColumn(
                    "Assessment", width="medium"
                ),
            },
        )
else:
    st.info("No source chunks were returned for attribution.")

st.space("small")
render_section_heading(
    "Guardrail outcome",
    "Only context approved by the existing guardrail can be viewed below.",
)

with st.container(border=True):
    if result["action"] == "Blocked":
        st.error(
            "Context transmission was blocked. The retrieved text is suppressed "
            "and no content was sent to Gemini."
        )
    elif result["action"] == "Redacted":
        st.badge(
            "Redacted before generation",
            icon=":material/verified_user:",
            color="orange",
        )
        st.info(
            "The guardrail supplied sanitized context for generation. "
            "Source text is intentionally not displayed in the dashboard."
        )
    else:
        st.success(
            "No sensitive values were flagged. Source context is not displayed in "
            "the dashboard to avoid exposing document text."
        )

st.page_link(
    "pages/4_Privacy_Audit.py",
    label="Review privacy audit trail",
    width="content",
)
