import streamlit as st
import pandas as pd
import pyodbc
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Connect to SQL Server
def connect_to_sql():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=DESKTOP-4CMUAR0\\SQLEXPRESS;'
            'DATABASE=Assessment_Form;'
            'TrustServerCertificate=yes;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

# Generate PDF from form data
def generate_pdf(data):
    pdf_file = f"{data['Name']}_Patient_Form.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    y = 750
    c.drawString(100, y, "🏥 Patient Information Form")
    y -= 30
    for key, value in data.items():
        if pd.notna(value) and value != "":
            lines = f"{key}: {value}".split("\n")
            for line in lines:
                c.drawString(100, y, line[:110])  # Trim line if too long
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 750
    c.save()
    return pdf_file

# Load dataset
df = pd.read_csv("https://github.com/sachinr-2911/Healthcare_Assessment_Form/raw/main/CleanedDataset.csv")
df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)

# Streamlit UI
st.title("🏥 Patient Information Form")

search_query = st.text_input("🔍 Search Patient Name", "").strip().lower()
filtered_df = df[df["Name"].str.lower().str.contains(search_query, na=False)] if search_query else df

submitted = False
pdf_file = None

if not filtered_df.empty:
    selected_patient = st.selectbox("Select a Patient:", filtered_df["Name"])
    patient_data = filtered_df[filtered_df["Name"] == selected_patient].iloc[0] if not filtered_df.empty else None

    if patient_data is not None:
        with st.form("patient_form"):
            input_data = {}
            for col in df.columns:
                if col == "ID":
                    continue  # ID will be auto-generated
                value = patient_data[col]
                if "Age" in col:
                    input_data[col] = st.number_input(col, int(value), step=1)
                elif "Gender" in col:
                    input_data[col] = st.selectbox(col, ["Male", "Female"], index=["Male", "Female"].index(str(value)))
                elif any(x in col for x in ["Symptoms", "History", "Pattern"]):
                    input_data[col] = st.text_area(col, value if pd.notna(value) else "")
                else:
                    input_data[col] = st.text_input(col, value if pd.notna(value) else "")

            submitted = st.form_submit_button("Submit")

            if submitted:
                conn = connect_to_sql()
                if conn:
                    cursor = conn.cursor()

                    # Create table if it doesn't exist
                    columns_sql = ",\n".join([
                        f"[{col}] NVARCHAR(MAX)" if col != "ID" else "[ID] INT PRIMARY KEY IDENTITY(1,1)"
                        for col in df.columns
                    ])
                    cursor.execute(f"""
                        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Patients' AND xtype='U')
                        CREATE TABLE Patients ({columns_sql})
                    """)
                    conn.commit()

                    # Insert data (excluding ID)
                    columns = [col for col in df.columns if col != "ID"]
                    placeholders = ", ".join(["?" for _ in columns])
                    cursor.execute(
                        f"INSERT INTO Patients ({', '.join(f'[{col}]' for col in columns)}) VALUES ({placeholders})",
                        tuple(input_data[col] for col in columns)
                    )
                    conn.commit()
                    conn.close()

                    st.success("✅ Patient details submitted successfully!")

                    # Generate PDF
                    pdf_file = generate_pdf(input_data)

# 📄 Offer download outside the form
if submitted and pdf_file:
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Download PDF", f, file_name=pdf_file, mime="application/pdf")
