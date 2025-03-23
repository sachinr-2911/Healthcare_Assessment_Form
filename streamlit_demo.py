import streamlit as st
import pandas as pd 

# Load cleaned patient data
df = pd.read_excel(r"https://github.com/sachinr-2911/Healthcare_Assessment_Form/blob/main/Cleaned_Patient_Data.xlsx")

# Ensure "Age" column is numeric
df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)  # Convert to integer, replacing non-numeric values with 0

# Streamlit UI
st.title("🏥 Patient Information Form")

# Dropdown to select a patient
selected_patient = st.selectbox("Select a Patient:", df["Name"])

# Fetch selected patient data
patient_data = df[df["Name"] == selected_patient].iloc[0]

# Create form
with st.form("patient_form"):
    name = st.text_input("Name", patient_data["Name"])
    age = st.number_input("Age", int(patient_data["Age"]), step=1)  # Ensure integer type
    gender = st.selectbox("Gender", ["Male", "Female"], index=["Male", "Female"].index(str(patient_data["Gender"])))
    symptoms = st.text_area("Symptoms & History", patient_data["Symptoms & History"])

    submitted = st.form_submit_button("Submit")

    if submitted:
        st.success("✅ Patient details updated successfully!")
