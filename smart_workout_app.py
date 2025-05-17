
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Define known barbell-type keywords for correction logic
barbell_keywords = ['barbell', 'deadlift', 'bench press', 'squat', 'row', 'clean', 'press']

# Define a basic exercise library per muscle group
exercise_library = {
    "Chest": ["Flat Barbell Bench Press", "Incline Dumbbell Press", "Cable Fly"],
    "Back": ["Pull-ups", "Barbell Row", "Seated Cable Row"],
    "Legs": ["Barbell Squats", "Leg Press", "Lunges"],
    "Biceps": ["Barbell Curl", "Dumbbell Curl", "Cable Curl"],
    "Triceps": ["Tricep Pushdown", "Dips", "Skullcrushers"],
    "Shoulders": ["Overhead Press", "Lateral Raises", "Arnold Press"],
    "Abs": ["Planks", "Cable Crunches", "Hanging Leg Raises"],
    "Cardio": ["Treadmill", "Elliptical", "Jump Rope"]
}

# Function to determine if an exercise needs barbell correction
def is_barbell_exercise(exercise):
    return any(keyword in exercise.lower() for keyword in barbell_keywords)

# Correction logic
def correct_weight(row):
    if is_barbell_exercise(row['Exercise']):
        return row['Weight'] * 2 + 45  # both sides + barbell weight
    return row['Weight']

# Workout suggestion logic
def suggest_workout(df, today):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce')
    df['Reps'] = pd.to_numeric(df['Reps'], errors='coerce')
    df['Weight'] = df['Weight'].fillna(0)
    df['Corrected_Weight'] = df.apply(correct_weight, axis=1)

    muscle_groups = list(exercise_library.keys())
    past_week = today - timedelta(days=7)
    recent_df = df[(df['Date'] >= past_week) & (df['Date'] <= today)]
    last_trained = {}
    for _, row in recent_df.iterrows():
        last_trained[row['Category']] = row['Date']

    # Sort by least recently trained
    priority_groups = sorted(
        muscle_groups,
        key=lambda x: last_trained.get(x, datetime(1900, 1, 1))
    )

    # Pick top 2 undertrained groups
    target_groups = priority_groups[:2]
    suggestions = {}

    for group in target_groups:
        exercises = exercise_library[group]
        suggestions[group] = []
        for exercise in exercises:
            past_entries = df[df['Exercise'].str.lower() == exercise.lower()].sort_values(by='Date', ascending=False)
            if not past_entries.empty:
                last_weight = past_entries.iloc[0]['Corrected_Weight']
                suggested_weight = round(last_weight * 1.025, 1)  # 2.5% progression
            else:
                suggested_weight = "Start Light"
            suggestions[group].append({
                "Exercise": exercise,
                "Weight (lbs)": suggested_weight,
                "Reps": "8–12",
                "Alt": f"Any basic {group.lower()} movement if this isn’t available"
            })

    return suggestions, target_groups

# Streamlit UI
st.title("Smart Workout Suggester")
st.write("Upload your FitNotes CSV log to get a custom workout suggestion for tomorrow.")

uploaded_file = st.file_uploader("Choose a FitNotes CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, on_bad_lines="skip")
    today = datetime.now()
    suggestions, focus_groups = suggest_workout(df, today)

    st.subheader(f"Suggested Focus for Tomorrow: {', '.join(focus_groups)}")
    for group, exercises in suggestions.items():
        st.markdown(f"### {group}")
        for ex in exercises:
            st.markdown(f"- **{ex['Exercise']}** | {ex['Weight (lbs)']} lbs | {ex['Reps']} reps")
            st.markdown(f"  _Alt: {ex['Alt']}_")
