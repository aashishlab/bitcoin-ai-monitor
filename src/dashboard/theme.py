import os
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(CURRENT_DIR, "styles.css")


def clean_html(html: str) -> str:
    """
    Remove leading whitespace and blank lines from HTML strings so Streamlit's
    underlying Markdown parser (CommonMark) treats the content strictly as raw HTML,
    preventing any lines with 4+ spaces from being interpreted as indented code blocks (<pre><code>).
    """
    if not html:
        return ""
    return "\n".join(line.lstrip() for line in html.splitlines() if line.strip())


def inject_theme():
    """Inject the CryptoGuard dark theme CSS stylesheet into the Streamlit app."""
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning("styles.css not found. Default theme in use.")


def render_sidebar_branding():
    """Render the top CryptoGuard brand identity inside the sidebar."""
    html_content = """
    <div class="cg-sidebar-brand">
        <div class="cg-brand-icon">🛡️</div>
        <div>
            <div class="cg-brand-title">Crypto<span>Guard</span></div>
            <div class="cg-brand-sub">Bitcoin Intelligence</div>
        </div>
    </div>
    """
    st.sidebar.markdown(clean_html(html_content), unsafe_allow_html=True)


def render_sidebar_footer():
    """Render the bottom status indicators in the sidebar."""
    html_content = """
    <div class="cg-sidebar-footer">
        <div class="cg-status-indicator">
            <span class="cg-dot-active"></span>
            <span><b>System:</b> Offline Engine</span>
        </div>
        <div class="cg-status-indicator">
            <span class="cg-dot-active"></span>
            <span><b>Pipeline:</b> Phase 4 Verified</span>
        </div>
        <div class="cg-sidebar-ver">Build: v4.2-intel · Offline</div>
    </div>
    """
    st.sidebar.markdown(clean_html(html_content), unsafe_allow_html=True)


def render_header(title: str, subtitle: str, badge_text: str = "OFFLINE INVESTIGATION PLATFORM", badge_type: str = "lime"):
    """
    Render a top application header bar with title, subtitle, and status badge.
    """
    badge_class = f"cg-badge-{badge_type}"
    html_content = f"""
    <div class="cg-top-header">
        <div class="cg-header-left">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        <div class="cg-header-right">
            <span class="cg-badge {badge_class}">● {badge_text}</span>
        </div>
    </div>
    """
    st.markdown(clean_html(html_content), unsafe_allow_html=True)


def render_kpi_card_html(label: str, value: str, description: str, icon: str = "📊") -> str:
    """
    Generate the HTML snippet for a KPI card.
    """
    html_content = f"""
    <div class="cg-kpi-card">
        <div class="cg-kpi-top">
            <span class="cg-kpi-label">{label}</span>
            <span class="cg-kpi-icon">{icon}</span>
        </div>
        <div class="cg-kpi-value">{value}</div>
        <div class="cg-kpi-desc">{description}</div>
    </div>
    """
    return clean_html(html_content)


def render_status_badge(text: str, variant: str = "lime") -> str:
    """
    Generate an HTML status badge.
    variant: lime, blue, purple, amber, slate
    """
    return f'<span class="cg-badge cg-badge-{variant}">{text}</span>'

