import streamlit as st
import pandas as pd
from database import init_db, get_events, get_summary, import_events, get_quality_report

st.set_page_config(page_title="AdTrack AI", page_icon="📡", layout="wide")
init_db()

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1440px;}
[data-testid="stMetric"] {background: #111827; border: 1px solid #263244; padding: 16px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("📡 AdTrack AI")
st.caption("One conversion ledger for your website, ad platforms, CRM and backend.")
with st.sidebar:
    st.header("Workspace")
    st.write("**Data sources**")
    st.write("🟢 First-party event API")
    st.write("🟡 CSV imports")
    st.write("⚪ Meta / TikTok API connectors — configure credentials to activate")
    st.divider()
    st.subheader("Import conversions")
    upload = st.file_uploader("Upload a CSV", type=["csv"])
    if upload is not None and st.button("Import CSV", type="primary"):
        try:
            frame = pd.read_csv(upload)
            count, skipped = import_events(frame)
            st.success(f"Imported {count} events. Skipped {skipped} duplicates/invalid rows.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not import CSV: {exc}")

summary = get_summary()
a,b,c,d = st.columns(4)
a.metric("Recorded conversions", f"{summary['conversions']:,}")
b.metric("Conversion value", f"{summary['value']:,.2f}")
c.metric("Unique orders", f"{summary['orders']:,}")
d.metric("Duplicate events", f"{summary['duplicates']:,}")

events = get_events()
quality = get_quality_report()
st.subheader("Conversion activity")
if events.empty:
    st.info("No conversion events yet. Send a test event to the API or import a CSV to populate the ledger.")
else:
    daily = events.copy()
    daily["date"] = pd.to_datetime(daily["occurred_at"], errors="coerce").dt.date
    chart = daily.groupby(["date", "source"]).size().unstack(fill_value=0)
    st.line_chart(chart)
    st.dataframe(events, use_container_width=True, hide_index=True)

st.subheader("Tracking health")
q1,q2,q3 = st.columns(3)
q1.metric("Events missing event ID", quality["missing_event_id"])
q2.metric("Events missing campaign tags", quality["missing_campaign"])
q3.metric("Potential duplicates", quality["duplicate_groups"])
if quality["warnings"]:
    for warning in quality["warnings"]:
        st.warning(warning)
else:
    st.success("No basic data-quality warnings detected.")

st.subheader("Source breakdown")
if not events.empty:
    breakdown = events.groupby("source", as_index=False).agg(
        conversions=("event_id", "count"), value=("value", "sum")
    )
    st.dataframe(breakdown, use_container_width=True, hide_index=True)

st.caption("Important: this ledger reports events received by AdTrack AI. It does not prove which ad platform caused a conversion. Compare platform attribution separately.")
