import streamlit as st
import sys
import os
import io
import importlib
from contextlib import redirect_stdout

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)


try:
    from utils import semantic_stats

    STATS_AVAILABLE = True
except ImportError as e:
    STATS_AVAILABLE = False
    IMPORT_ERROR = str(e)


def show_statistics():
    st.set_page_config(page_title="Knowledge Stats", layout="wide")
    st.title("📊 Semantic Knowledge Statistics")

    if not STATS_AVAILABLE:
        st.error(f"⚠️ Could not import the module.")
        st.code(f"Error: {IMPORT_ERROR}\n\nMake sure the file is named 'app/utils/semantic_stats.py'")
        return

    if st.button("🚀 Run Analysis", type="primary"):
        with st.spinner("Calculating Inference Ratios..."):

            f = io.StringIO()
            with redirect_stdout(f):
                try:
                    importlib.reload(semantic_stats)
                except FileNotFoundError:
                    print("Error: Could not find .ttl files. Check 'data/' and 'ontology/' folders.")
                except Exception as e:
                    print(f"Error running script: {e}")

            report = f.getvalue()

            inference_val = "0%"
            total_triples = "0"

            for line in report.split("\n"):
                if "Inference ratio:" in line:
                    inference_val = line.split(":")[-1].strip()
                if "Total characteristic triples:" in line:
                    total_triples = line.split(":")[-1].strip()

            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Inference Ratio", inference_val, help="New knowledge created by Logic Rules")
            c2.metric("Characteristic Triples", total_triples, help="Total anatomy facts found")

            # Display Raw Logs
            with st.expander("📄 View Full Analysis Logs", expanded=True):
                st.text(report)


if __name__ == "__main__":
    show_statistics()