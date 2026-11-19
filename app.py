"""Product landing page for Privacy Leakage Detection in RAG Systems."""

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.ui import apply_global_styles, render_sidebar_brand

load_dotenv()

st.set_page_config(
    page_title="Privacy Leakage Detection in RAG Systems",
    page_icon=":material/shield_lock:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

st.markdown(
    """
    <section class="pld-landing-hero">
        <div class="pld-landing-copy">
            <div class="pld-landing-eyebrow">Research prototype · privacy-aware retrieval</div>
            <h1 class="pld-landing-title">
                Privacy Leakage<br>
                Detection in<br>
                <span class="pld-title-accent">RAG Systems</span>
            </h1>
            <p class="pld-landing-subtitle">
                A privacy inspection layer for retrieval-augmented generation.
                Detect sensitive information in retrieved context, enforce a guardrail
                policy, and keep a privacy-safe record of each decision.
            </p>
        </div>
        <div class="pld-landing-visual" aria-label="Privacy shield and inspection signals">
            <div class="pld-shield-stage">
                <div class="pld-shield-orbit"></div>
                <span class="pld-orbit-label pld-orbit-label--top">CONTEXT INSPECTION</span>
                <span class="pld-orbit-label pld-orbit-label--right">GUARDRAIL</span>
                <span class="pld-orbit-label pld-orbit-label--bottom">SAFE GENERATION</span>
                <span class="pld-orbit-label pld-orbit-label--left">PII SIGNALS</span>
                <svg class="pld-shield-svg" viewBox="0 0 360 400" role="img" aria-label="Layered privacy shield">
                    <defs>
                        <linearGradient id="shieldFill" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#17394A"/>
                            <stop offset="100%" stop-color="#112333"/>
                        </linearGradient>
                        <linearGradient id="shieldStroke" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#5EEAD4"/>
                            <stop offset="100%" stop-color="#14B8A6"/>
                        </linearGradient>
                        <filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%">
                            <feGaussianBlur stdDeviation="7" result="blur"/>
                            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                        </filter>
                    </defs>
                    <path d="M180 31 304 78v103c0 84-49 145-124 188C105 326 56 265 56 181V78Z"
                          fill="url(#shieldFill)" stroke="url(#shieldStroke)" stroke-width="3"/>
                    <path d="M180 58 279 95v86c0 67-38 117-99 154-61-37-99-87-99-154V95Z"
                          fill="none" stroke="#347C83" stroke-width="1.5" stroke-dasharray="5 8"/>
                    <path d="M124 197h37l19-43 26 88 20-45h28"
                          fill="none" stroke="#5EEAD4" stroke-width="5" stroke-linecap="round"
                          stroke-linejoin="round" filter="url(#softGlow)"/>
                    <circle cx="124" cy="197" r="6" fill="#5EEAD4"/>
                    <circle cx="254" cy="197" r="6" fill="#5EEAD4"/>
                    <path d="m180 124 31 12v26c0 22-12 38-31 50-19-12-31-28-31-50v-26Z"
                          fill="#153C49" stroke="#2DD4BF" stroke-width="2"/>
                    <path d="m167 157 9 9 18-21" fill="none" stroke="#A7F3D0"
                          stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="180" cy="354" r="3" fill="#5EEAD4"/>
                    <circle cx="304" cy="181" r="3" fill="#5EEAD4"/>
                    <circle cx="56" cy="181" r="3" fill="#5EEAD4"/>
                </svg>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="pld-landing-section">', unsafe_allow_html=True)
action_columns = st.columns([1.2, 1, 3.2], gap="medium")
with action_columns[0]:
    if st.button(
        label="Explore Project",
        icon=":material/arrow_forward:",
        width="stretch",
        type="primary",
        key="explore_project_hero",
    ):
        st.switch_page("pages/1_Document_Management.py")
with action_columns[1]:
    st.page_link(
        "pages/2_RAG_Query.py",
        label="Open secure query",
        icon=":material/lock:",
        width="stretch",
    )
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <section class="pld-landing-section">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">The challenge</div>
            <h2 class="pld-section-title">Useful retrieval should not mean unchecked disclosure.</h2>
            <p class="pld-section-copy">
                A RAG system can retrieve passages containing personal or confidential
                details. If that context is sent onward without inspection, sensitive
                information may cross a boundary the user did not intend.
            </p>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

problem_columns = st.columns([1, 1], gap="large")
with problem_columns[0]:
    st.markdown(
        """
        <div class="pld-story-panel">
            <div class="pld-story-index">01 / PROBLEM</div>
            <h3 class="pld-story-title">Retrieved text carries its own risk.</h3>
            <p class="pld-story-copy">
                Semantic search selects relevant passages, not necessarily safe ones.
                A document may contain identifiers or named entities that need to be
                handled before a model sees the retrieved context.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with problem_columns[1]:
    st.markdown(
        """
        <div class="pld-story-panel">
            <div class="pld-story-index">02 / DESIGN GOAL</div>
            <h3 class="pld-story-title">Inspect between retrieval and generation.</h3>
            <p class="pld-story-copy">
                This project adds a detection and policy-enforcement step to the
                existing RAG flow, while retaining document-grounded retrieval and
                recording privacy-safe query outcomes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="pld-landing-section">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">Proposed solution</div>
            <h2 class="pld-section-title">Three layers. One privacy decision.</h2>
            <p class="pld-section-copy">
                Structured patterns and named entities are inspected together. The
                selected privacy policy determines whether the context is redacted
                before generation or the request is blocked.
            </p>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

solution_columns = st.columns(3, gap="medium")
solutions = [
    (
        "regex",
        "01 · PATTERN MATCHING",
        "Regex detection",
        "Checks retrieved context for supported structured identifiers using the project's existing patterns.",
    ),
    (
        "psychology",
        "02 · ENTITY RECOGNITION",
        "spaCy NER",
        "Finds contextual named entities using the configured spaCy model and current detection logic.",
    ),
    (
        "policy",
        "03 · POLICY ENFORCEMENT",
        "Privacy guardrail",
        "Redact & Continue sanitizes context, while Block Request stops generation when sensitive content is found.",
    ),
]
for column, (icon, label, title, copy) in zip(solution_columns, solutions):
    with column:
        st.markdown(
            f"""
            <div class="pld-solution-card">
                <span class="pld-solution-icon" aria-hidden="true">{icon}</span>
                <div class="pld-story-index">{label}</div>
                <h3 class="pld-story-title">{title}</h3>
                <p class="pld-story-copy">{copy}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <section class="pld-landing-section" id="architecture">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">System architecture</div>
            <h2 class="pld-section-title">A visible checkpoint in the RAG journey.</h2>
            <p class="pld-section-copy">
                The privacy inspection sits after semantic retrieval and before
                language-model generation. The original retrieval and generation
                components remain in place.
            </p>
        </div>
        <div class="pld-flow-track">
            <div class="pld-flow-node">
                <div class="pld-flow-number">01 · INGEST</div>
                <div class="pld-flow-title">PDF documents</div>
                <div class="pld-flow-copy">Extract text and recursively split into chunks.</div>
            </div>
            <div class="pld-flow-node">
                <div class="pld-flow-number">02 · INDEX</div>
                <div class="pld-flow-title">Vectors in ChromaDB</div>
                <div class="pld-flow-copy">Create Sentence Transformer embeddings for retrieval.</div>
            </div>
            <div class="pld-flow-node">
                <div class="pld-flow-number">03 · RETRIEVE</div>
                <div class="pld-flow-title">Relevant context</div>
                <div class="pld-flow-copy">Find document passages for a user question.</div>
            </div>
            <div class="pld-flow-node">
                <div class="pld-flow-number">04 · INSPECT</div>
                <div class="pld-flow-title">Regex + NER</div>
                <div class="pld-flow-copy">Evaluate the retrieved text for sensitive content.</div>
            </div>
            <div class="pld-flow-node">
                <div class="pld-flow-number">05 · ENFORCE</div>
                <div class="pld-flow-title">Privacy policy</div>
                <div class="pld-flow-copy">Sanitize approved context or stop the request.</div>
            </div>
            <div class="pld-flow-node">
                <div class="pld-flow-number">06 · RESPOND</div>
                <div class="pld-flow-title">Gemini + audit</div>
                <div class="pld-flow-copy">Generate from approved context and record safe metadata.</div>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="pld-landing-section">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">Project capabilities</div>
            <h2 class="pld-section-title">Built around the complete workflow.</h2>
        </div>
        <div class="pld-story-panel">
            <div class="pld-feature-line"><span class="pld-feature-check">verified</span><div><strong>Document workspace</strong><br><span class="pld-story-copy">PDF upload, recursive chunking, vector indexing, and sanitized PDF downloads.</span></div></div>
            <div class="pld-feature-line"><span class="pld-feature-check">verified</span><div><strong>Privacy-aware RAG queries</strong><br><span class="pld-story-copy">Document scope selection, policy controls, retrieval, protected generation, and source metadata.</span></div></div>
            <div class="pld-feature-line"><span class="pld-feature-check">verified</span><div><strong>Detection visibility</strong><br><span class="pld-story-copy">Actual Regex and NER category counts, guardrail outcomes, and source attribution.</span></div></div>
            <div class="pld-feature-line"><span class="pld-feature-check">verified</span><div><strong>Privacy-safe governance</strong><br><span class="pld-story-copy">Session audit history, filtering, CSV exports, and redacted document copies.</span></div></div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="pld-landing-section">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">Technology</div>
            <h2 class="pld-section-title">The tools behind the prototype.</h2>
            <p class="pld-section-copy">
                Technologies are named from the application's current imports and pipeline.
            </p>
        </div>
        <div class="pld-tech-strip">
            <span class="pld-tech-tag">Python</span>
            <span class="pld-tech-tag">Streamlit</span>
            <span class="pld-tech-tag">LangChain</span>
            <span class="pld-tech-tag">Sentence Transformers</span>
            <span class="pld-tech-tag">ChromaDB</span>
            <span class="pld-tech-tag">spaCy</span>
            <span class="pld-tech-tag">Google Gemini</span>
            <span class="pld-tech-tag">PyMuPDF</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="pld-landing-section">
        <div class="pld-section-intro">
            <div class="pld-section-eyebrow">Project team</div>
            <h2 class="pld-section-title">A research-focused engineering effort.</h2>
            <p class="pld-section-copy">
                The repository does not currently include contributor names, roles,
                or affiliations, so no individual team details are shown here.
            </p>
        </div>
        <div class="pld-story-panel">
            <div class="pld-story-index">RESEARCH PROTOTYPE</div>
            <h3 class="pld-story-title">Privacy Leakage Detection in RAG Systems</h3>
            <p class="pld-story-copy">
                The project explores detection and policy enforcement for sensitive
                information in retrieved context, with a privacy-safe audit trail.
                Add verified contributor details to the project repository to display
                a named team here.
            </p>
        </div>
    </section>
    <section class="pld-landing-cta">
        <div>
            <div class="pld-section-eyebrow">Explore the system</div>
            <h2 class="pld-section-title">Start with a protected document workflow.</h2>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

cta_columns = st.columns([1.2, 1, 3.2], gap="medium")
with cta_columns[0]:
    if st.button(
        label="Explore Project",
        icon=":material/arrow_forward:",
        width="stretch",
        type="primary",
        key="explore_project_footer",
    ):
        st.switch_page("pages/1_Document_Management.py")
with cta_columns[1]:
    st.page_link(
        "pages/3_Privacy_Dashboard.py",
        label="View privacy center",
        icon=":material/shield:",
        width="stretch",
    )

st.caption("Privacy Leakage Detection in RAG Systems · Research prototype")
