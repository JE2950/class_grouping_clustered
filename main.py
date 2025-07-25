import streamlit as st
import pandas as pd
import networkx as nx
from random import shuffle

st.set_page_config(page_title="Class Group Generator", layout="wide")

st.title("🧑‍🏫 Class Group Generator (With Fallback and Visualisation)")

st.markdown("""
Upload a CSV with:
- `Name`, `Gender`, `SEN`, `Attainment`
- `Friend1`–`Friend5`: five chosen friends
- `Avoid1`–`Avoid3`: pupils to avoid
""")

uploaded = st.file_uploader("📤 Upload your CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded).fillna("")
    st.success("File uploaded!")

    G = nx.Graph()
    avoid_dict = {}

    for _, row in df.iterrows():
        name = row["Name"]
        G.add_node(name, gender=row["Gender"], sen=row["SEN"], attainment=row["Attainment"])
        for i in range(1, 6):
            friend = row[f"Friend{i}"]
            if friend:
                G.add_edge(name, friend)
        avoids = [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]]
        avoid_dict[name] = avoids

    friend_clusters = list(nx.connected_components(G))
    shuffle(friend_clusters)

    class_size = 20
    num_classes = len(df) // class_size
    classes = [[] for _ in range(num_classes)]
    unplaced = []

    def violates_avoid(group, student):
        for peer in group:
            if peer in avoid_dict.get(student, []) or student in avoid_dict.get(peer, []):
                return True
        return False

    for cluster in friend_clusters:
        cluster = list(cluster)
        placed = False
        for group in classes:
            if len(group) + len(cluster) <= class_size and all(not violates_avoid(group, s) for s in cluster):
                group.extend(cluster)
                placed = True
                break
        if not placed:
            unplaced.extend(cluster)

    st.header("📋 Class Lists")
    results = []
    for i, group in enumerate(classes):
        st.subheader(f"Class {i+1} ({len(group)} pupils)")
        st.write(group)
        for name in group:
            results.append({"Name": name, "Class": f"Class {i+1}"})

    if unplaced:
        st.warning(f"⚠️ {len(unplaced)} student(s) could not be placed automatically.")
        st.subheader("🧍‍♂️ Unplaced Students")
        st.write(unplaced)

    export_df = pd.DataFrame(results)
    st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")

    # Visualisation
    st.header("🔍 Friendship Placement Summary")

    # Build name to class map
    name_to_class = {row["Name"]: row["Class"] for row in results}

    visual_data = []
    for _, row in df.iterrows():
        name = row["Name"]
        row_class = name_to_class.get(name, "Unplaced")
        summary = {"Name": name, "Class": row_class}
        for i in range(1, 6):
            f = row[f"Friend{i}"]
            if not f:
                summary[f"Friend{i}"] = ""
            elif name_to_class.get(f) == row_class:
                summary[f"Friend{i}"] = f"✅ {f}"
            else:
                summary[f"Friend{i}"] = f"❌ {f}"
        visual_data.append(summary)

    vis_df = pd.DataFrame(visual_data)
    st.dataframe(vis_df)
