import streamlit as st
import pandas as pd
import networkx as nx
from random import shuffle

st.set_page_config(page_title="Class Group Generator", layout="wide")

st.title("🧑‍🏫 Class Group Generator (Clustering-Based)")
st.write("""
Upload a CSV of pupils with:
- `Name`, `Gender` (M/F), `SEN` (Yes/No), `Attainment` (High/Medium/Low)
- `Friend1`–`Friend5`: five chosen friends
- `Avoid1`–`Avoid3`: pupils to avoid
""")

uploaded = st.file_uploader("📤 Upload your CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded).fillna("")
    st.success("File uploaded!")

    G = nx.Graph()
    for _, row in df.iterrows():
        name = row["Name"]
        G.add_node(name, gender=row["Gender"], sen=row["SEN"], attainment=row["Attainment"])
        for i in range(1, 6):
            friend = row[f"Friend{i}"]
            if friend:
                G.add_edge(name, friend)

    # Create clusters of connected students
    friend_clusters = list(nx.connected_components(G))
    shuffle(friend_clusters)

    class_size = 20
    num_classes = len(df) // class_size
    classes = [[] for _ in range(num_classes)]

    # Convert avoid columns into a dict for fast access
    avoid_dict = {row["Name"]: [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]] for _, row in df.iterrows()}

    def violates_avoid(group, student):
        for peer in group:
            if peer in avoid_dict.get(student, []) or student in avoid_dict.get(peer, []):
                return True
        return False

    success = True
    for cluster in friend_clusters:
        cluster = list(cluster)
        placed = False
        for group in classes:
            if len(group) + len(cluster) <= class_size and all(not violates_avoid(group, s) for s in cluster):
                group.extend(cluster)
                placed = True
                break
        if not placed:
            success = False
            break

    if success:
        st.header("📋 Class Lists")
        results = []
        for i, group in enumerate(classes):
            st.subheader(f"Class {i+1} ({len(group)} pupils)")
            st.write(group)
            for name in group:
                results.append({"Name": name, "Class": f"Class {i+1}"})
        export_df = pd.DataFrame(results)
        st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")
    else:
        st.error("❌ Could not group all clusters into classes without violating constraints. Try loosening 'avoid' rules or increasing class size.")
