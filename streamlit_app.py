import streamlit as st
import datetime
import pandas as pd
import plotly.express as px

def calculate_bmr(weight, age, gender):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if gender == "Male":
        return (10 * weight) + (6.25 * 170) - (5 * age) + 5  # Assuming average height
    else:
        return (10 * weight) + (6.25 * 160) - (5 * age) - 161  # Assuming average height

def calculate_tdee(bmr, activity_hours):
    """Calculate Total Daily Energy Expenditure"""
    # Base activity factor (sedentary) = 1.2
    # Additional activity factor per hour of exercise = 0.075
    activity_factor = 1.2 + (0.075 * activity_hours/7)  # Divide by 7 to get daily average
    return bmr * activity_factor

def calculate_macros(calories, goal):
    """Calculate macronutrient distribution based on goal"""
    if goal == "Lose Weight":
        protein_pct = 0.40
        fat_pct = 0.35
        carb_pct = 0.25
    elif goal == "Maintain Weight":
        protein_pct = 0.30
        fat_pct = 0.30
        carb_pct = 0.40
    else:  # Gain Weight
        protein_pct = 0.30
        fat_pct = 0.25
        carb_pct = 0.45
    
    protein_cals = calories * protein_pct
    fat_cals = calories * fat_pct
    carb_cals = calories * carb_pct
    
    protein_g = protein_cals / 4
    fat_g = fat_cals / 9
    carb_g = carb_cals / 4
    
    return {
        "protein": round(protein_g),
        "fat": round(fat_g),
        "carbs": round(carb_g)
    }

def create_weight_projection(start_weight, target_weight, target_date):
    """Create a DataFrame with weekly weight projections"""
    dates = pd.date_range(
        start=datetime.date.today(),
        end=target_date,
        freq='W'  # Weekly frequency
    )
    
    # Add start and end dates if they're not in the range
    dates = pd.date_range(
        start=datetime.date.today(),
        end=target_date,
        freq='D'  # Daily frequency for smoother line
    )
    
    total_days = (target_date - datetime.date.today()).days
    daily_change = (target_weight - start_weight) / total_days
    
    weights = [start_weight + (daily_change * i) for i in range(len(dates))]
    
    df = pd.DataFrame({
        'Date': dates,
        'Weight': weights
    })
    
    return df

# Set page config
st.set_page_config(page_title="Macro Calculator", layout="wide")

# Add title and description
st.title("🏋️‍♂️ Macro Calculator")
st.write("Calculate your daily caloric needs and macro distribution based on your goals!")

# Create two columns for input
col1, col2 = st.columns(2)

with col1:
    st.subheader("Personal Information")
    age = st.number_input("Age", min_value=15, max_value=100, value=30)
    gender = st.selectbox("Gender", ["Male", "Female"])
    current_weight = st.number_input("Current Weight (kg)", min_value=40, max_value=200, value=70)
    exercise_hours = st.number_input("Hours of Exercise per Week", min_value=0, max_value=30, value=3)

with col2:
    st.subheader("Goals")
    target_weight = st.number_input("Target Weight (kg)", min_value=40, max_value=200, value=65)
    goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain Weight", "Gain Weight"])
    if goal != "Maintain Weight":
        target_date = st.date_input(
            "Target Date",
            min_value=datetime.date.today() + datetime.timedelta(days=7),
            value=datetime.date.today() + datetime.timedelta(days=35)
        )

# Calculate results when user clicks button
if st.button("Calculate Macros"):
    # Basic calculations
    bmr = calculate_bmr(current_weight, age, gender)
    tdee = calculate_tdee(bmr, exercise_hours)
    
    # Adjust calories based on goal
    if goal == "Lose Weight":
        weight_diff = current_weight - target_weight
        days_until_target = (target_date - datetime.date.today()).days
        # Assume 7700 calories per kg of weight loss
        daily_deficit = (weight_diff * 7700) / days_until_target
        target_calories = max(tdee - daily_deficit, 1200)  # Don't go below 1200 calories
    elif goal == "Gain Weight":
        weight_diff = target_weight - current_weight
        days_until_target = (target_date - datetime.date.today()).days
        # Assume 7700 calories per kg of weight gain
        daily_surplus = (weight_diff * 7700) / days_until_target
        target_calories = tdee + daily_surplus
    else:
        target_calories = tdee

    # Calculate macros
    macros = calculate_macros(target_calories, goal)
    
    # Display results
    st.header("Your Results")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.metric("Daily Calories", f"{round(target_calories)} kcal")
    with col4:
        st.metric("BMR", f"{round(bmr)} kcal")
    with col5:
        st.metric("TDEE", f"{round(tdee)} kcal")
    
    # Display macros
    st.subheader("Daily Macronutrient Targets")
    col6, col7, col8 = st.columns(3)
    
    with col6:
        st.metric("Protein", f"{macros['protein']}g")
    with col7:
        st.metric("Fats", f"{macros['fat']}g")
    with col8:
        st.metric("Carbs", f"{macros['carbs']}g")
    
    if goal != "Maintain Weight":
        st.info(f"""
        To reach your target weight of {target_weight}kg by {target_date}, 
        you should aim for {round(target_calories)} calories per day. 
        This represents a {'deficit' if goal == 'Lose Weight' else 'surplus'} of 
        {abs(round(target_calories - tdee))} calories from your maintenance calories.
        """)
        
        # Create and display weight projection graph
        st.subheader("Weight Projection")
        projection_df = create_weight_projection(current_weight, target_weight, target_date)
        
        fig = px.line(
            projection_df,
            x='Date',
            y='Weight',
            title=f"Projected Weight Progress ({goal})",
            labels={'Weight': 'Weight (kg)', 'Date': 'Date'},
        )
        
        fig.add_hline(
            y=target_weight,
            line_dash="dash",
            line_color="red",
            annotation_text="Target Weight"
        )
        
        fig.update_layout(
            showlegend=True,
            hovermode='x unified',
            plot_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Weekly breakdown
        st.subheader("Weekly Weight Milestones")
        weekly_df = projection_df.resample('W', on='Date').first()
        for idx, row in weekly_df.iterrows():
            week_num = (idx - pd.Timestamp(datetime.date.today())).days // 7 + 1
            st.write(f"Week {week_num}: {row['Weight']:.1f} kg")

# Add footer with information
st.markdown("---")
st.markdown("""
**Notes:**
- BMR: Basal Metabolic Rate (calories burned at rest)
- TDEE: Total Daily Energy Expenditure (calories burned including activity)
- Calculations assume moderate intensity exercise
- Adjust intake based on progress and energy levels
- The weight projection assumes linear progress and may vary in reality
""")
