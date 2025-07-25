import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Class Group Generator", layout="wide")

st.title("🧑‍🏫 Class Group Generator (Min 1 Friend, Custom Class Count)")

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

    total_students = len(df)
    max_class_count = total_students // 10
    class_count = st.number_input("🔢 How many classes/groups?", min_value=2, max_value=max_class_count, value=4)

    students = df["Name"].tolist()
    class_size = total_students // class_count + 1
    classes = [[] for _ in range(class_count)]

    # Build friend and avoid dictionaries
    friend_map = {row["Name"]: [row[f"Friend{i}"] for i in range(1, 6) if row[f"Friend{i}"]] for _, row in df.iterrows()}
    avoid_map = {row["Name"]: [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]] for _, row in df.iterrows()}

    name_to_class = {}
    placed = set()
    unplaced = []

    def can_place(student, group):
        if len(group) >= class_size:
            return False
        for peer in group:
            if peer in avoid_map[student] or student in avoid_map.get(peer, []):
                return False
        return True

    random.shuffle(students)

    for student in students:
        if student in placed:
            continue

        friends = friend_map.get(student, [])
        friend_in_class = False

        # Try placing with a friend who's already placed
        for friend in friends:
            if friend in name_to_class:
                friend_class = name_to_class[friend]
                if can_place(student, classes[friend_class]):
                    classes[friend_class].append(student)
                    name_to_class[student] = friend_class
                    placed.add(student)
                    friend_in_class = True
                    break

        if friend_in_class:
            continue

        # Otherwise, place student and one friend together
        for friend in friends:
            if friend not in placed:
                for group_id, group in enumerate(classes):
                    if can_place(student, group) and can_place(friend, group):
                        group.extend([student, friend])
                        name_to_class[student] = group_id
                        name_to_class[friend] = group_id
                        placed.add(student)
                        placed.add(friend)
                        friend_in_class = True
                        break
                if friend_in_class:
                    break

        if not friend_in_class:
            unplaced.append(student)

    # Display results
    st.header("📋 Class Lists")
    results = []
    for i, group in enumerate(classes):
        st.subheader(f"Class {i+1} ({len(group)} pupils)")
        st.write(group)
        for name in group:
            results.append({"Name": name, "Class": f"Class {i+1}"})

    if unplaced:
        st.warning(f"⚠️ {len(unplaced)} student(s) could not be placed with at least one friend.")
        st.subheader("🧍‍♂️ Unplaced Students")
        st.write(unplaced)

    export_df = pd.DataFrame(results)
    st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")

    # Excel Export
    excel_buffer = export_df.to_excel(index=False, engine='openpyxl')
    st.download_button("📥 Download Excel", excel_buffer, file_name="assignments.xlsx")

    # Visualisation
    st.header("🔍 Friendship Placement Summary")

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
