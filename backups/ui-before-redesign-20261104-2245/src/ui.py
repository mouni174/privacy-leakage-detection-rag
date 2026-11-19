"""Shared visual foundation for the Streamlit application."""

import streamlit as st


def apply_global_styles() -> None:
    """Apply shared layout, navigation, and component styling."""
    st.markdown(
        """
        <style>
        :root {
            --pld-bg: #101827;
            --pld-panel: #172235;
            --pld-panel-raised: #1B2A40;
            --pld-border: #29374B;
            --pld-teal: #14B8A6;
            --pld-teal-bright: #2DD4BF;
            --pld-text: #F4F7FB;
            --pld-muted: #9AA8BB;
            --pld-red: #F87171;
            --pld-amber: #FBBF24;
            --pld-green: #34D399;
        }

        html, body, [class*="st-"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                         BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded" !important;
            font-weight: normal;
            font-style: normal;
            font-size: 1.2em;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            font-feature-settings: "liga";
            -webkit-font-feature-settings: "liga";
            -webkit-font-smoothing: antialiased;
        }

        [data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"] {
            display: none;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 82% 0%, rgba(20, 184, 166, 0.09), transparent 31rem),
                var(--pld-bg);
            color: var(--pld-text);
        }

        .block-container {
            max-width: 1480px;
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }

        h1, h2, h3, h4 {
            letter-spacing: -0.035em;
        }

        h1 {
            font-weight: 700;
        }

        .pld-hero {
            position: relative;
            overflow: hidden;
            padding: clamp(1.5rem, 3vw, 2.5rem);
            border: 1px solid rgba(45, 212, 191, 0.2);
            border-radius: 1.15rem;
            background:
                radial-gradient(ellipse at 87% 15%, rgba(20, 184, 166, 0.17), transparent 25rem),
                linear-gradient(125deg, #17263A 0%, #142134 58%, #122436 100%);
            box-shadow: 0 18px 48px rgba(2, 8, 20, 0.24);
        }

        .pld-hero-kicker {
            margin-bottom: 0.75rem;
            color: var(--pld-teal-bright);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .pld-hero-title {
            max-width: 46rem;
            margin: 0;
            color: var(--pld-text);
            font-size: clamp(2rem, 4vw, 3.15rem);
            font-weight: 700;
            letter-spacing: -0.055em;
            line-height: 1.08;
        }

        .pld-hero-copy {
            max-width: 47rem;
            margin: 0.95rem 0 0;
            color: #B2C0D1;
            font-size: 1rem;
            line-height: 1.7;
        }

        .pld-hero-meta {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.6rem;
            margin-top: 1.5rem;
        }

        .pld-status-chip,
        .pld-meta-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.48rem;
            padding: 0.4rem 0.7rem;
            border: 1px solid var(--pld-border);
            border-radius: 999px;
            background: rgba(11, 22, 38, 0.48);
            color: #C5D0DE;
            font-size: 0.76rem;
            font-weight: 600;
        }

        .pld-status-chip[data-state="ready"] {
            border-color: rgba(52, 211, 153, 0.28);
            color: var(--pld-green);
        }

        .pld-status-chip[data-state="empty"] {
            border-color: rgba(251, 191, 36, 0.28);
            color: var(--pld-amber);
        }

        .pld-status-dot {
            width: 0.42rem;
            height: 0.42rem;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 0.7rem currentColor;
        }

        .pld-step-number {
            color: var(--pld-teal-bright);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.1em;
        }

        .pld-feature-label {
            margin: 0.35rem 0 0.6rem;
            color: var(--pld-muted);
            font-size: 0.77rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stMarkdownContainer"] small {
            color: var(--pld-muted);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #121D2E 0%, #101827 100%);
            border-right: 1px solid var(--pld-border);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            padding: 0.5rem 0.7rem 0.9rem;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            min-height: 2.65rem;
            margin: 0.18rem 0;
            padding: 0.58rem 0.72rem;
            border: 1px solid transparent;
            border-radius: 0.7rem;
            color: #B5C1D1;
            transition: background-color 140ms ease, color 140ms ease, border-color 140ms ease;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background: rgba(20, 184, 166, 0.1);
            border-color: rgba(20, 184, 166, 0.22);
            color: var(--pld-text);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(20, 184, 166, 0.13);
            border-color: rgba(20, 184, 166, 0.28);
            color: var(--pld-teal-bright);
        }

        [data-testid="stMetric"] {
            min-height: 7.25rem;
            padding: 1.05rem 1.15rem;
            border: 1px solid var(--pld-border);
            border-radius: 0.9rem;
            background: linear-gradient(145deg, rgba(27, 42, 64, 0.94), rgba(23, 34, 53, 0.96));
            box-shadow: 0 10px 24px rgba(2, 8, 20, 0.16);
        }

        [data-testid="stMetricLabel"] {
            color: var(--pld-muted);
            font-size: 0.83rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--pld-text);
            font-weight: 650;
            letter-spacing: -0.035em;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--pld-border);
            border-radius: 0.9rem;
            background: rgba(23, 34, 53, 0.74);
            box-shadow: 0 9px 24px rgba(2, 8, 20, 0.12);
        }

        div.stButton > button,
        div.stDownloadButton > button,
        a[data-testid="stPageLink-NavLink"] {
            border-radius: 0.7rem;
            font-weight: 600;
            transition: transform 140ms ease, border-color 140ms ease, background-color 140ms ease;
        }

        .stApp a[data-testid="stPageLink-NavLink"] {
            display: flex;
            min-height: 3.1rem;
            align-items: center;
            padding: 0.65rem 0.8rem;
            border: 1px solid var(--pld-border);
            background: rgba(23, 34, 53, 0.82);
            color: #DCE6F1;
            text-decoration: none;
            box-shadow: 0 7px 18px rgba(2, 8, 20, 0.12);
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover,
        .stApp a[data-testid="stPageLink-NavLink"]:hover {
            transform: translateY(-1px);
            border-color: rgba(20, 184, 166, 0.55);
        }

        div.stButton > button[kind="primary"] {
            color: #06201F;
            border-color: var(--pld-teal);
            background: var(--pld-teal);
        }

        div.stButton > button[kind="primary"]:hover {
            color: #06201F;
            border-color: var(--pld-teal-bright);
            background: var(--pld-teal-bright);
        }

        [data-testid="stAlert"] {
            border-radius: 0.8rem;
        }

        @media (max-width: 768px) {
            .block-container {
                padding: 1.25rem 1rem 2rem;
            }

            [data-testid="stMetric"] {
                min-height: 6.4rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    """Render the product identity above the multipage navigation."""
    st.sidebar.markdown(
        """
        <div class="pld-sidebar-brand">
            <div class="pld-brand-mark">P</div>
            <div>
                <div class="pld-brand-name">Privacy RAG</div>
                <div class="pld-brand-caption">PRIVACY INTELLIGENCE</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
        <style>
        .pld-sidebar-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.35rem 0.35rem 1.15rem;
            margin-bottom: 0.7rem;
            border-bottom: 1px solid #29374B;
        }

        .pld-brand-mark {
            display: grid;
            width: 2.4rem;
            height: 2.4rem;
            place-items: center;
            border: 1px solid rgba(20, 184, 166, 0.42);
            border-radius: 0.75rem;
            background: rgba(20, 184, 166, 0.13);
            color: #2DD4BF;
            font-size: 1.15rem;
            font-weight: 750;
        }

        .pld-brand-name {
            color: #F4F7FB;
            font-size: 1.02rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        .pld-brand-caption {
            margin-top: 0.12rem;
            color: #8FA0B5;
            font-size: 0.62rem;
            font-weight: 650;
            letter-spacing: 0.11em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, description: str | None = None) -> None:
    """Render a consistently spaced section title and optional supporting text."""
    st.subheader(title)
    if description:
        st.caption(description)
