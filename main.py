import streamlit as st
import pandas as pd
import random
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Class Group Generator (4 Classes)", layout="wide")
st.title("🧑‍🏫 Class Group Generator – 4 Classes")
st.markdown("""
Upload a CSV with these columns:
- `Name`, `Gender`, `SEN`, `Attainment`
- `Friend1`–`Friend5`
- `Avoid1`–`Avoid3`
""")

uploaded = st.file_uploader("📤 Upload your CSV", type="csv")
if not uploaded:
    st.stop()

# Load and preprocess
df = pd.read_csv(uploaded).fillna("")
students = df["Name"].tolist()
max_class_size = 18
classes = [[] for _ in range(4)]

# Build maps
friend_map = {
    row["Name"]: [row[f"Friend{i}"] for i in range(1, 6) if row[f"Friend{i}"]]
    for _, row in df.iterrows()
}
avoid_map = {
    row["Name"]: [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]]
    for _, row in df.iterrows()
}
student_info = df.set_index("Name")[["Gender", "SEN"]].to_dict("index")

# Helper: can this student go into this group?
def can_place(student, group):
    if len(group) >= max_class_size:
        return False
    for peer in group:
        if peer in avoid_map[student] or student in avoid_map.get(peer, []):
            return False
    return True

# Greedy placement with friend-tie to smallest class
name_to_class = {}
placed = set()
for student in random.sample(students, len(students)):
    best = []
    for cls_idx, grp in enumerate(classes):
        if not can_place(student, grp):
            continue
        # count friends already in group
        cnt = sum(1 for f in friend_map[student] if f in grp)
        best.append((cnt, len(grp), cls_idx))
    if not best:
        # cannot go anywhere—mark unsatisfied
        continue
    # pick max friends, then smallest group
    best.sort(key=lambda x: (-x[0], x[1]))
    _, _, chosen = best[0]
    classes[chosen].append(student)
    name_to_class[student] = chosen
    placed.add(student)

# Identify unsatisfied: unplaced OR placed without any friend
unsatisfied = []
for student in students:
    cls = name_to_class.get(student, None)
    if cls is None:
        unsatisfied.append(student)
    else:
        grp = classes[cls]
        if not any(f in grp for f in friend_map[student]):
            unsatisfied.append(student)

# 1) Friendship visualiser
st.subheader("🔍 Friendship Placement Summary")
vis = []
for _, row in df.iterrows():
    name = row["Name"]
    cls = name_to_class.get(name, "Unplaced")
    vis_row = {"Name": name, "Class": f"Class {cls+1}" if isinstance(cls,int) else "Unplaced"}
    grp = classes[cls] if isinstance(cls,int) else []
    for i in range(1,6):
        f = row[f"Friend{i}"]
        if not f:
            vis_row[f"Friend{i}"] = ""
        elif f in grp:
            vis_row[f"Friend{i}"] = f"✅ {f}"
        else:
            vis_row[f"Friend{i}"] = f"❌ {f}"
    vis.append(vis_row)
vis_df = pd.DataFrame(vis)
st.dataframe(vis_df)

# 2) Pie charts at the bottom
for idx, grp in enumerate(classes, start=1):
    st.subheader(f"Class {idx} – Composition")
    genders = [student_info[n]["Gender"] for n in grp]
    plt.figure(figsize=(1.5,1.5))
    plt.pie([genders.count("M"), genders.count("F")], labels=["M","F"], autopct="%1.1f%%")
    plt.title("Gender")
    st.pyplot(plt.gcf())
    plt.clf()

    sens = [student_info[n]["SEN"] for n in grp]
    plt.figure(figsize=(1.5,1.5))
    plt.pie([sens.count("Yes"), sens.count("No")], labels=["SEN","No SEN"], autopct="%1.1f%%")
    plt.title("SEN")
    st.pyplot(plt.gcf())
    plt.clf()

# 3) Export table with columns Class 1–4 and Unplaced
st.header("📋 Exported Class List")
export = {f"Class {i+1}": classes[i] for i in range(4)}
export["Unsatisfied"] = unsatisfied
max_rows = max(len(lst) for lst in export.values())
for k in export:
    export[k] += [""] * (max_rows - len(export[k]))
export_df = pd.DataFrame(export)
st.dataframe(export_df)

# Download buttons
st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode(), "classes.csv")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    export_df.to_excel(w, index=False)
buf.seek(0)
st.download_button("📥 Download Excel", data=buf, file_name="classes.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Finally, list Unsatisfied separately
if unsatisfied:
    st.warning(f"⚠️ {len(unsatisfied)} student(s) need manual sorting:")
    st.write(unsatisfied)
