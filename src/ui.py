"""Shared visual foundation for the Streamlit application."""

import streamlit as st


def sanitize_sensitive_text(value: object) -> str:
    """Redact structured identifiers and person names from displayed metadata."""
    text = "" if value is None else str(value)
    if not text:
        return text

    from src.redactor import redact_sensitive_data

    return redact_sensitive_data(text, include_uncertain=True)


def render_empty_state(
    *,
    eyebrow: str,
    title: str,
    description: str,
    icon: str,
    steps: tuple[str, ...],
    actions: tuple[tuple[str, str, str], ...],
) -> None:
    """Render a framed empty state with practical next steps and page links."""
    with st.container(border=True):
        intro_columns = st.columns([0.2, 1], vertical_alignment="center")
        with intro_columns[0]:
            st.markdown(
                f'<div class="pld-empty-state-icon" aria-hidden="true">{icon}</div>',
                unsafe_allow_html=True,
            )
        with intro_columns[1]:
            st.markdown(
                f'<div class="pld-empty-state-eyebrow">{eyebrow}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"### {title}")
            st.write(description)

        st.divider()
        st.markdown("**A simple way to begin**")
        step_columns = st.columns(len(steps), gap="small")
        for index, (column, step) in enumerate(zip(step_columns, steps), start=1):
            with column:
                st.markdown(
                    f"""
                    <div class="pld-empty-state-step">
                        <span class="pld-empty-state-step-number">{index:02}</span>
                        <span>{step}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
        action_columns = st.columns(len(actions), gap="small")
        for column, (page, label, action_icon) in zip(action_columns, actions):
            with column:
                st.page_link(
                    page,
                    label=label,
                    icon=f":material/{action_icon}:",
                    width="stretch",
                )


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
            font-family: system-ui, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
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

        .pld-page-header {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            gap: 1.5rem;
            margin: 0.4rem 0 1.8rem;
            padding: 1.45rem 1.6rem;
            border: 1px solid rgba(58, 83, 106, 0.72);
            border-radius: 1rem;
            background:
                radial-gradient(ellipse at 98% 0%, rgba(20, 184, 166, 0.13), transparent 25rem),
                linear-gradient(115deg, rgba(23, 34, 53, 0.98), rgba(17, 29, 46, 0.96));
            box-shadow: 0 16px 38px rgba(2, 8, 20, 0.2);
        }

        .pld-page-header-main {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
        }

        .pld-page-mark {
            display: grid;
            flex: 0 0 3rem;
            width: 3rem;
            height: 3rem;
            place-items: center;
            border: 1px solid rgba(45, 212, 191, 0.34);
            border-radius: 0.9rem;
            background: rgba(20, 184, 166, 0.12);
            color: var(--pld-teal-bright);
            font-family: "Material Symbols Rounded";
            font-size: 1.55rem;
            font-feature-settings: "liga";
        }

        .pld-page-eyebrow {
            margin-bottom: 0.35rem;
            color: var(--pld-teal-bright);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .pld-page-title {
            margin: 0;
            color: var(--pld-text);
            font-size: clamp(1.7rem, 3vw, 2.45rem);
            font-weight: 720;
            letter-spacing: -0.05em;
            line-height: 1.1;
        }

        .pld-page-description {
            max-width: 56rem;
            margin: 0.55rem 0 0;
            color: #AEBBCD;
            font-size: 0.94rem;
            line-height: 1.65;
        }

        .pld-page-state {
            min-width: 10rem;
            padding: 0.85rem 1rem;
            border-left: 1px solid rgba(91, 112, 137, 0.48);
            color: var(--pld-muted);
            font-size: 0.72rem;
            letter-spacing: 0.06em;
            text-align: right;
            text-transform: uppercase;
        }

        .pld-page-state strong {
            display: block;
            margin-top: 0.25rem;
            color: var(--pld-text);
            font-size: 1.03rem;
            letter-spacing: -0.02em;
            text-transform: none;
        }

        .pld-landing-hero {
            position: relative;
            display: grid;
            grid-template-columns: minmax(0, 1.12fr) minmax(21rem, 0.88fr);
            align-items: center;
            gap: clamp(2rem, 5vw, 5rem);
            min-height: 34rem;
            overflow: hidden;
            padding: clamp(2rem, 5vw, 4.5rem);
            border: 1px solid rgba(45, 212, 191, 0.2);
            border-radius: 1.45rem;
            background:
                radial-gradient(ellipse at 82% 25%, rgba(20, 184, 166, 0.12), transparent 27rem),
                linear-gradient(125deg, #121F31 0%, #111D2E 60%, #102536 100%);
            box-shadow: 0 28px 70px rgba(2, 8, 20, 0.35);
        }

        .pld-landing-hero::before {
            position: absolute;
            inset: 0;
            background-image: linear-gradient(rgba(120, 157, 177, 0.035) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(120, 157, 177, 0.035) 1px, transparent 1px);
            background-size: 42px 42px;
            content: "";
            mask-image: linear-gradient(90deg, black, transparent 85%);
            pointer-events: none;
        }

        .pld-landing-copy,
        .pld-landing-visual {
            position: relative;
            z-index: 1;
        }

        .pld-landing-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 1.25rem;
            color: var(--pld-teal-bright);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.15em;
            text-transform: uppercase;
        }

        .pld-landing-eyebrow::before {
            width: 1.8rem;
            height: 1px;
            background: var(--pld-teal);
            content: "";
        }

        .pld-landing-title {
            max-width: 50rem;
            margin: 0;
            color: #F7FAFC;
            font-size: clamp(2.6rem, 5.3vw, 5.2rem);
            font-weight: 740;
            letter-spacing: -0.07em;
            line-height: 0.99;
        }

        .pld-landing-title .pld-title-accent {
            color: var(--pld-teal-bright);
        }

        .pld-landing-subtitle {
            max-width: 43rem;
            margin: 1.3rem 0 0;
            color: #B5C3D2;
            font-size: clamp(1.05rem, 1.6vw, 1.23rem);
            line-height: 1.75;
        }

        .pld-landing-visual {
            display: grid;
            min-height: 24rem;
            place-items: center;
            isolation: isolate;
        }

        .pld-shield-stage {
            position: relative;
            display: grid;
            width: min(100%, 28rem);
            aspect-ratio: 1;
            place-items: center;
        }

        .pld-shield-orbit {
            position: absolute;
            inset: 8%;
            border: 1px solid rgba(45, 212, 191, 0.19);
            border-radius: 50%;
            box-shadow: 0 0 55px rgba(20, 184, 166, 0.08), inset 0 0 55px rgba(20, 184, 166, 0.04);
        }

        .pld-shield-orbit::before,
        .pld-shield-orbit::after {
            position: absolute;
            border: 1px dashed rgba(89, 169, 180, 0.23);
            border-radius: 50%;
            content: "";
        }

        .pld-shield-orbit::before { inset: 12%; }
        .pld-shield-orbit::after { inset: -10%; border-color: rgba(89, 169, 180, 0.12); }

        .pld-shield-svg {
            position: relative;
            z-index: 1;
            width: 66%;
            filter: drop-shadow(0 0 30px rgba(45, 212, 191, 0.22));
        }

        .pld-orbit-label {
            position: absolute;
            z-index: 2;
            padding: 0.45rem 0.7rem;
            border: 1px solid rgba(45, 212, 191, 0.24);
            border-radius: 999px;
            background: rgba(12, 25, 39, 0.92);
            color: #C4D8DF;
            font-size: 0.68rem;
            font-weight: 650;
            letter-spacing: 0.06em;
            white-space: nowrap;
        }

        .pld-orbit-label--top { top: 9%; left: 34%; }
        .pld-orbit-label--right { top: 44%; right: -3%; }
        .pld-orbit-label--bottom { bottom: 8%; left: 30%; }
        .pld-orbit-label--left { top: 47%; left: -5%; }

        .pld-landing-section {
            margin-top: clamp(3rem, 7vw, 6rem);
        }

        .pld-section-intro {
            max-width: 49rem;
            margin-bottom: 1.4rem;
        }

        .pld-section-eyebrow {
            margin-bottom: 0.55rem;
            color: var(--pld-teal-bright);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .pld-section-title {
            margin: 0;
            color: var(--pld-text);
            font-size: clamp(1.75rem, 3.2vw, 2.6rem);
            font-weight: 700;
            letter-spacing: -0.055em;
            line-height: 1.12;
        }

        .pld-section-copy {
            margin: 0.7rem 0 0;
            color: #A8B6C7;
            line-height: 1.7;
        }

        .pld-story-panel {
            height: 100%;
            padding: clamp(1.35rem, 2.5vw, 2rem);
            border: 1px solid var(--pld-border);
            border-radius: 1rem;
            background: linear-gradient(145deg, rgba(23, 34, 53, 0.92), rgba(15, 26, 42, 0.92));
        }

        .pld-story-index {
            margin-bottom: 1.1rem;
            color: var(--pld-teal-bright);
            font-size: 0.7rem;
            font-weight: 750;
            letter-spacing: 0.14em;
        }

        .pld-story-title {
            margin: 0 0 0.7rem;
            color: #F0F5F8;
            font-size: 1.2rem;
            font-weight: 680;
            letter-spacing: -0.025em;
        }

        .pld-story-copy {
            margin: 0;
            color: #A7B5C5;
            font-size: 0.9rem;
            line-height: 1.7;
        }

        .pld-empty-state-icon {
            display: grid;
            width: 3.35rem;
            height: 3.35rem;
            place-items: center;
            border: 1px solid rgba(45, 212, 191, 0.32);
            border-radius: 1rem;
            background: rgba(20, 184, 166, 0.12);
            color: var(--pld-teal-bright);
            font-family: "Material Symbols Rounded";
            font-size: 1.7rem;
            font-feature-settings: "liga";
        }

        .pld-empty-state-eyebrow {
            margin-bottom: 0.35rem;
            color: var(--pld-teal-bright);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .pld-empty-state-step {
            display: flex;
            min-height: 4.1rem;
            align-items: flex-start;
            gap: 0.7rem;
            padding: 0.8rem;
            border: 1px solid rgba(58, 78, 99, 0.56);
            border-radius: 0.75rem;
            background: rgba(14, 25, 41, 0.68);
            color: #B5C3D2;
            font-size: 0.84rem;
            line-height: 1.5;
        }

        .pld-empty-state-step-number {
            flex: 0 0 auto;
            color: var(--pld-teal-bright);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.06em;
        }

        .pld-solution-card {
            height: 100%;
            padding: 1.35rem;
            border: 1px solid rgba(67, 93, 116, 0.63);
            border-radius: 0.95rem;
            background:
                radial-gradient(ellipse at top right, rgba(20, 184, 166, 0.08), transparent 16rem),
                rgba(17, 29, 46, 0.92);
        }

        .pld-solution-icon {
            display: grid;
            width: 2.75rem;
            height: 2.75rem;
            place-items: center;
            margin-bottom: 1rem;
            border: 1px solid rgba(45, 212, 191, 0.25);
            border-radius: 0.8rem;
            background: rgba(20, 184, 166, 0.1);
            color: var(--pld-teal-bright);
            font-family: "Material Symbols Rounded";
            font-size: 1.35rem;
            font-feature-settings: "liga";
        }

        .pld-flow-track {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            align-items: stretch;
            gap: 0.75rem;
            margin-top: 1.6rem;
        }

        .pld-flow-node {
            position: relative;
            min-height: 9.5rem;
            padding: 1rem 0.9rem;
            border: 1px solid rgba(59, 83, 105, 0.78);
            border-radius: 0.85rem;
            background: linear-gradient(160deg, rgba(23, 37, 56, 0.96), rgba(15, 26, 42, 0.96));
        }

        .pld-flow-node:not(:last-child)::after {
            position: absolute;
            top: 1.45rem;
            right: -0.83rem;
            z-index: 1;
            width: 0.9rem;
            height: 1px;
            background: rgba(45, 212, 191, 0.52);
            content: "";
        }

        .pld-flow-number {
            color: var(--pld-teal-bright);
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.1em;
        }

        .pld-flow-title {
            margin: 0.65rem 0 0.4rem;
            color: #EAF1F5;
            font-size: 0.92rem;
            font-weight: 650;
        }

        .pld-flow-copy {
            color: #9EADBE;
            font-size: 0.75rem;
            line-height: 1.55;
        }

        .pld-feature-line {
            display: flex;
            align-items: flex-start;
            gap: 0.8rem;
            padding: 0.9rem 0;
            border-bottom: 1px solid rgba(58, 78, 99, 0.48);
        }

        .pld-feature-line:last-child { border-bottom: 0; }

        .pld-feature-check {
            color: var(--pld-teal-bright);
            font-family: "Material Symbols Rounded";
            font-size: 1.15rem;
            font-feature-settings: "liga";
        }

        .pld-tech-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1.3rem;
        }

        .pld-tech-tag {
            padding: 0.52rem 0.8rem;
            border: 1px solid rgba(67, 93, 116, 0.72);
            border-radius: 0.65rem;
            background: rgba(17, 29, 46, 0.84);
            color: #C4D0DC;
            font-size: 0.79rem;
            font-weight: 600;
        }

        .pld-landing-cta {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            margin: clamp(3rem, 6vw, 5rem) 0 1.5rem;
            padding: clamp(1.4rem, 3vw, 2.2rem);
            border: 1px solid rgba(45, 212, 191, 0.23);
            border-radius: 1rem;
            background: linear-gradient(110deg, rgba(20, 184, 166, 0.11), rgba(23, 34, 53, 0.95) 65%);
        }

        @media (max-width: 980px) {
            .pld-landing-hero { grid-template-columns: 1fr; min-height: auto; }
            .pld-landing-visual { min-height: 19rem; }
            .pld-flow-track { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .pld-flow-node:nth-child(3)::after { display: none; }
        }

        @media (max-width: 680px) {
            .pld-page-header { grid-template-columns: 1fr; gap: 1rem; }
            .pld-page-state { padding: 0.75rem 0 0; border-top: 1px solid rgba(91, 112, 137, 0.48); border-left: 0; text-align: left; }
            .pld-landing-hero { padding: 1.5rem; }
            .pld-landing-title { font-size: clamp(2.5rem, 13vw, 4rem); }
            .pld-flow-track { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .pld-flow-node:nth-child(3)::after { display: block; }
            .pld-flow-node:nth-child(even)::after { display: none; }
            .pld-landing-cta { align-items: flex-start; flex-direction: column; }
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

        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            min-height: 2.65rem;
            margin: 0.18rem 0;
            padding: 0.58rem 0.72rem;
            border-color: transparent;
            background: transparent;
            box-shadow: none;
            color: #B5C1D1;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(20, 184, 166, 0.13);
            border-color: rgba(20, 184, 166, 0.28);
            color: var(--pld-teal-bright);
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
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

        @media (max-width: 850px) {
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }

            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                width: 100% !important;
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            min-width: 0;
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
    st.sidebar.page_link(
        "app.py",
        label="Home",
        icon=":material/home:",
        width="stretch",
    )
    st.sidebar.page_link(
        "pages/1_Document_Management.py",
        label="Document Management",
        icon=":material/folder_managed:",
        width="stretch",
    )
    st.sidebar.page_link(
        "pages/2_RAG_Query.py",
        label="RAG Query",
        icon=":material/forum:",
        width="stretch",
    )
    st.sidebar.page_link(
        "pages/3_Privacy_Dashboard.py",
        label="Privacy Dashboard",
        icon=":material/shield:",
        width="stretch",
    )
    st.sidebar.page_link(
        "pages/4_Privacy_Audit.py",
        label="Privacy Audit",
        icon=":material/receipt_long:",
        width="stretch",
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


def render_page_header(
    title: str,
    description: str,
    eyebrow: str,
    icon: str,
    status_label: str,
) -> None:
    """Render a workspace header distinct from the product landing page."""
    st.markdown(
        f"""
        <header class="pld-page-header">
            <div class="pld-page-header-main">
                <span class="pld-page-mark" aria-hidden="true">{icon}</span>
                <div>
                    <div class="pld-page-eyebrow">{eyebrow}</div>
                    <h1 class="pld-page-title">{title}</h1>
                    <p class="pld-page-description">{description}</p>
                </div>
            </div>
            <div class="pld-page-state">Workspace status<strong>{status_label}</strong></div>
        </header>
        """,
        unsafe_allow_html=True,
    )
