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

# --- Load Data ---
df = pd.read_csv(uploaded).fillna("")
students = df["Name"].tolist()
max_class_size = 18
classes = [[] for _ in range(4)]

# --- Build lookup maps ---
friend_map = {
    r["Name"]: [r[f"Friend{i}"] for i in range(1,6) if r[f"Friend{i}"]]
    for _, r in df.iterrows()
}
avoid_map = {
    r["Name"]: [r[f"Avoid{i}"] for i in range(1,4) if r[f"Avoid{i}"]]
    for _, r in df.iterrows()
}
student_info = df.set_index("Name")[["Gender","SEN"]].to_dict("index")

# --- Placement helper ---
def can_place(name, group):
    if len(group) >= max_class_size:
        return False
    for peer in group:
        if peer in avoid_map[name] or name in avoid_map.get(peer,[]):
            return False
    return True

# --- Greedy placement: maximise # of friends, tie-break = smallest class ---
name_to_class = {}
for name in random.sample(students, len(students)):
    # find all valid classes
    candidates = []
    for idx, grp in enumerate(classes):
        if not can_place(name, grp):
            continue
        # count how many of this student's friends are already in grp
        cnt = sum(1 for f in friend_map[name] if f in grp)
        candidates.append((cnt, len(grp), idx))
    if not candidates:
        continue
    # pick the class with highest cnt, then smallest size
    cnt, _, chosen = max(candidates, key=lambda x: (x[0], -x[1]))
    classes[chosen].append(name)
    name_to_class[name] = chosen

# --- Identify ManualSort list ---
unplaced = [n for n in students if n not in name_to_class]
unsatisfied = [
    n for n in students
    if n in name_to_class
       and not any(f in classes[name_to_class[n]] for f in friend_map[n])
]
manual_sort = unplaced + unsatisfied

# --- Export wide table ---
export = {f"Class {i+1}": classes[i] for i in range(4)}
export["ManualSort"] = manual_sort
max_rows = max(len(lst) for lst in export.values())
for k in export:
    export[k] += [""]*(max_rows - len(export[k]))
export_df = pd.DataFrame(export)

st.header("📋 Exported Class List")
st.dataframe(export_df)

# Download buttons
st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode(), "classes.csv")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    export_df.to_excel(writer, index=False)
buf.seek(0)
st.download_button(
    "📥 Download Excel",
    data=buf,
    file_name="classes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Friendship Visualiser ---
st.subheader("🔍 Friendship Placement Summary")
vis = []
for _, r in df.iterrows():
    name = r["Name"]
    cls = name_to_class.get(name, None)
    grp = classes[cls] if cls is not None else []
    row = {"Name": name, "Class": f"Class {cls+1}" if cls is not None else "Unplaced"}
    for i in range(1,6):
        f = r[f"Friend{i}"]
        if not f:
            row[f"Friend{i}"] = ""
        elif f in grp:
            row[f"Friend{i}"] = f"✅ {f}"
        else:
            row[f"Friend{i}"] = f"❌ {f}"
    vis.append(row)
st.dataframe(pd.DataFrame(vis))

# --- Pie Charts at the very bottom ---
st.header("📊 Class Composition")
for idx, grp in enumerate(classes, start=1):
    st.subheader(f"Class {idx}")
    # Gender split
    genders = [student_info[n]["Gender"] for n in grp]
    plt.figure(figsize=(1.5,1.5))
    plt.pie([genders.count("M"), genders.count("F")], labels=["M","F"], autopct="%1.1f%%")
    plt.title("Gender")
