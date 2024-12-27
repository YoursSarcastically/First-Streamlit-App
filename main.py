import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
from openai import OpenAI

# Set page config
st.set_page_config(
    page_title="Acha Khana 🍽️",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper functions
def calculate_bmi(weight, height):
    """Calculate BMI given weight (kg) and height (m)."""
    return weight / (height ** 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_bmi_emoji(category):
    """Return appropriate emoji for BMI category."""
    emoji_map = {
        'Underweight': '⚖️',
        'Normal weight': '✅',
        'Overweight': '⚠️',
        'Obese': '❗'
    }
    return emoji_map.get(category, '⚖️')

def generate_ai_recommendations(user_info):
    """Generate AI-based food recommendations."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )
    completion = client.chat.completions.create(
        model="meta-llama/llama-3.2-3b-instruct:free",
        messages=[
            {
                "role": "user",
                "content": f"Generate a 7-day Indian homely food only (dinner, lunch, and breakfast) recommendation for a {user_info['age']} years old, {user_info['gender']} with a goal to {user_info['fitness_goal']} and prefer {user_info['veg_pref']} food."
            }
        ]
    )
    return completion.choices[0].message.content

def generate_meal_plan(calorie_target, veg_pref, meal_preferences):
    """Generate a meal plan based on calorie target and meal distributions."""
    # Placeholder for actual logic without CSV data
    meal_data = [
        {"Recipe_name": "Veg Pulao", "Category": "Lunch", "Calories (kcal)": 300},
        {"Recipe_name": "Idli Sambar", "Category": "Breakfast", "Calories (kcal)": 200},
        {"Recipe_name": "Paneer Curry", "Category": "Dinner", "Calories (kcal)": 400},
        {"Recipe_name": "Fruit Salad", "Category": "Snack", "Calories (kcal)": 150}
    ]
    data = pd.DataFrame(meal_data)

    daily_plans = []
    used_meals = set()

    for day in range(7):
        daily_plan = []
        remaining_calories = calorie_target

        for category, percentage in meal_preferences.items():
            category_target_calories = calorie_target * (percentage / 100)
            try:
                category_foods = data[(data['Category'].str.contains(category, case=False)) &
                                      (data['Calories (kcal)'] <= category_target_calories * 1.2)]

                category_foods = category_foods[~category_foods['Recipe_name'].isin(used_meals)]

                if not category_foods.empty:
                    category_foods['calorie_diff'] = abs(category_foods['Calories (kcal)'] - category_target_calories)
                    recommended = category_foods.nsmallest(1, 'calorie_diff')
                    used_meals.add(recommended['Recipe_name'].iloc[0])
                    daily_plan.append(recommended)
            except Exception as e:
                st.error(f"Error processing category {category}: {str(e)}")
                continue

        if daily_plan:
            day_df = pd.concat(daily_plan)
            day_df['Day'] = f'Day {day + 1}'
            daily_plans.append(day_df)

    return pd.concat(daily_plans) if daily_plans else pd.DataFrame()

# Main title
st.title("🍱 Acha Khana.AI by Suraj✨")

st.markdown("""
    ### Generate a meal plan that's best for you with BMI and Calorie calculations 🌟
""")

# Create two columns for the layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯Tell Us About Yourself")

    input_col1, input_col2, input_col3 = st.columns(3)

    with input_col1:
        age = st.number_input("🎂 Age", min_value=0, max_value=120, value=25)
        height = st.number_input("📏 Height (cm)", min_value=100, max_value=250, value=170) / 100
        activity_level = st.selectbox("💪 Lifestyle", [
            "Sedentary (Office Job) 💻",
            "Light Active (Light Exercise) 🛃",
            "Moderate Active (Regular Exercise) 🏃",
            "Very Active (Athlete) 🏋"
        ])

    with input_col2:
        gender = st.selectbox("👤 Gender", ["Male", "Female", "Other"])
        current_weight = st.number_input("⚖️ Current Weight (kg)", min_value=20, max_value=200, value=70)
        veg_pref = st.selectbox("🥗 Food Preference", ["Veg 🌱", "Non-Veg 🥗"])

    with input_col3:
        fitness_goal = st.selectbox("🎯 Fitness Goal", [
            "Lose Weight 🔽", "Maintain Weight ⚖️", "Gain Weight 🔼"
        ])
        target_weight = st.number_input("🎯 Target Weight (kg)", min_value=20, max_value=200, value=current_weight)

with col2:
    st.header("🍽️ Customize Your Meals")
    st.write("Adjust how you want your daily calories distributed:")

    breakfast_pct = st.slider("🌅 Breakfast %", 0, 40, 25)
    lunch_pct = st.slider("🌞 Lunch %", 0, 40, 30)
    dinner_pct = st.slider("🌙 Dinner %", 0, 40, 30)
    snacks_pct = st.slider("🍪 Snacks %", 0, 40, 15)

    total_pct = breakfast_pct + lunch_pct + dinner_pct + snacks_pct
    meal_preferences = {
        'Breakfast': (breakfast_pct / total_pct) * 100,
        'Lunch': (lunch_pct / total_pct) * 100,
        'Dinner': (dinner_pct / total_pct) * 100,
        'Snack': (snacks_pct / total_pct) * 100
    }

# Calculate BMI and calorie needs
bmi = calculate_bmi(current_weight, height)
bmi_category = get_bmi_category(bmi)

if gender == "Male":
    bmr = 88.362 + (13.397 * current_weight) + (4.799 * height * 100) - (5.677 * age)
else:
    bmr = 447.593 + (9.247 * current_weight) + (3.098 * height * 100) - (4.330 * age)

activity_multipliers = {
    "Sedentary (Office Job) 💻": 1.2,
    "Light Active (Light Exercise) 🛃": 1.375,
    "Moderate Active (Regular Exercise) 🏃": 1.55,
    "Very Active (Athlete) 🏋": 1.725
}

tdee = bmr * activity_multipliers[activity_level]
if "Lose Weight" in fitness_goal:
    calorie_target = tdee - 500
elif "Gain Weight" in fitness_goal:
    calorie_target = tdee + 500
else:
    calorie_target = tdee

# Display health metrics
with st.expander("🏥 Your Health Metrics"):
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("📊 BMI", f"{bmi:.1f}")
        st.write(f"Category: {bmi_category} {get_bmi_emoji(bmi_category)}")

    with metric_col2:
        st.metric("🔥 Base Metabolic Rate", f"{bmr:.0f} kcal")

    with metric_col3:
        st.metric("🎯 Daily Calorie Target", f"{calorie_target:.0f} kcal")

# Generate button
if st.button("✨ Bana do mera acha khaana!"):
    with st.spinner("Creating your personalized meal plan..."):
        user_info = {
            "age": age,
            "gender": gender,
            "fitness_goal": fitness_goal,
            "veg_pref": veg_pref
        }
        ai_recommendations = generate_ai_recommendations(user_info)

        st.header("🔎 Here's your Acha Khaana!")
        st.write(f"Here are some meal suggestions based on your preferences: {ai_recommendations}")

        meal_plan = generate_meal_plan
st.markdown("---")
st.markdown("### Made with ❤️ by [Suraj Sharma](https://www.linkedin.com/in/surajsharma97/)")
