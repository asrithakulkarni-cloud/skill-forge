import sqlite3
from datetime import date

import streamlit as st
import pandas as pd

# 1. Set up the website
st.set_page_config(
    page_title="SkillForge",
    page_icon="🚀",
    layout="wide"
)

# 2. Connect to the database
conn = sqlite3.connect("skillforge.db", check_same_thread=False)

# 3. Create tables to save information
conn.execute("""
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    progress INTEGER DEFAULT 0
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS practice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill TEXT NOT NULL,
    hours REAL NOT NULL,
    study_date TEXT NOT NULL,
    notes TEXT
)
""")
conn.commit()

# 4. Design the website
st.markdown("""
<style>
.stApp {
    background-color: #f4f7fc;
}
.main-title {
    background: linear-gradient(120deg, #142850, #2563eb);
    padding: 25px;
    border-radius: 15px;
    color: white;
}
.main-title h1 {
    color: white;
}
.stButton button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
    <h1>🚀 SkillForge</h1>
    <p>Personal Skill Growth Tracker</p>
    <p>Learn new skills. Track your progress. Reach your goals.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# 5. Create navigation tabs
dashboard, skills_tab, practice_tab, history_tab = st.tabs([
    "📊 Dashboard",
    "🎯 My Skills",
    "📝 Log Practice",
    "📚 Practice History"
])

# 6. Dashboard page
with dashboard:
    st.header("Your Learning Dashboard")

    skills = pd.read_sql_query(
        "SELECT * FROM skills", conn
    )

    logs = pd.read_sql_query(
        "SELECT * FROM practice", conn
    )

    total_skills = len(skills)
    total_hours = logs["hours"].sum() if not logs.empty else 0

    average_progress = (
        skills["progress"].mean() if not skills.empty else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Skills Tracked", total_skills)
    col2.metric("Practice Hours", f"{total_hours:.1f}")
    col3.metric("Average Progress", f"{average_progress:.0f}%")

    st.subheader("Your Skill Progress")

    if not skills.empty:
        chart_data = skills.set_index("name")["progress"]
        st.bar_chart(chart_data)
        st.dataframe(
            skills[["name", "category", "progress"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Add your first skill in the My Skills tab.")

# 7. Add skills and update progress
with skills_tab:
    st.header("Manage Your Skills")

    with st.form("add_skill_form"):
        skill_name = st.text_input("Skill Name")
        category = st.selectbox(
            "Category",
            ["Programming", "Data Analytics", "Design",
             "Communication", "Other"]
        )

        add_button = st.form_submit_button("Add Skill")

        if add_button:
            if skill_name.strip():
                try:
                    conn.execute(
                        "INSERT INTO skills (name, category, progress) "
                        "VALUES (?, ?, 0)",
                        (skill_name.strip(), category)
                    )
                    conn.commit()
                    st.success("Skill added successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("This skill already exists.")
            else:
                st.warning("Please enter a skill name.")

    st.divider()
    st.subheader("Update Your Progress")

    skills = pd.read_sql_query(
        "SELECT * FROM skills ORDER BY name", conn
    )

    if not skills.empty:
        selected_skill = st.selectbox(
            "Select a skill",
            skills["name"].tolist()
        )

        current_progress = int(
            skills.loc[
                skills["name"] == selected_skill, "progress"
            ].iloc[0]
        )

        progress = st.slider(
            "Completion Percentage",
            min_value=0,
            max_value=100,
            value=current_progress
        )

        if st.button("Save Progress"):
            conn.execute(
                "UPDATE skills SET progress = ? WHERE name = ?",
                (progress, selected_skill)
            )
            conn.commit()
            st.success("Progress updated!")
            st.rerun()
    else:
        st.info("Add a skill before updating progress.")

# 8. Record daily practice
with practice_tab:
    st.header("Log Your Learning")

    skills = pd.read_sql_query(
        "SELECT name FROM skills ORDER BY name", conn
    )

    if not skills.empty:
        with st.form("practice_form"):
            selected_skill = st.selectbox(
                "What did you study?",
                skills["name"].tolist()
            )

            study_date = st.date_input(
                "Study Date",
                value=date.today(),
                max_value=date.today()
            )

            hours = st.number_input(
                "Hours Studied",
                min_value=0.25,
                max_value=24.0,
                value=1.0,
                step=0.25
            )

            notes = st.text_area(
                "What did you learn?",
                placeholder="Example: Learned Python loops"
            )

            save_button = st.form_submit_button("Save Practice")

            if save_button:
                conn.execute(
                    "INSERT INTO practice "
                    "(skill, hours, study_date, notes) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        selected_skill,
                        hours,
                        study_date.isoformat(),
                        notes
                    )
                )
                conn.commit()
                st.success("Practice session saved!")
                st.rerun()
    else:
        st.info("Add a skill first in the My Skills tab.")

# 9. View learning history
with history_tab:
    st.header("Your Practice History")

    history = pd.read_sql_query(
        "SELECT study_date, skill, hours, notes "
        "FROM practice ORDER BY study_date DESC",
        conn
    )

    if not history.empty:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Practice Hours by Skill")
        hours_chart = history.groupby("skill")["hours"].sum()
        st.bar_chart(hours_chart)

        csv = history.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download History as CSV",
            data=csv,
            file_name="skillforge_history.csv",
            mime="text/csv"
        )
    else:
        st.info("Your practice history will appear here.")

# 10. Footer
st.divider()
st.caption("SkillForge | Built with Python, Streamlit, SQLite and Pandas")

