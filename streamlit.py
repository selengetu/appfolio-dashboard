import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import pdfkit
# Set page layout
st.set_page_config(page_title="Business Dashboards", layout="wide")

# 🔹 1. Define File Paths (Updated for Windows)
BASE_DIR = r"C:\Users\SelengeTulga\Downloads\Tenant\dashboard"  # ✅ FIXED
st.title("📊 Appfolio Dashboards")
FILES = {
    "Tenant Data": os.path.join(BASE_DIR, "rent_roll-20250317.csv"),
    "Work Orders": os.path.join(BASE_DIR, "work_order-20250317.csv"),
    "Vacancies": os.path.join(BASE_DIR, "unit_vacancy_detail-20250318.csv"),
}
def save_pdf():
    # Convert Streamlit page to PDF
    pdfkit.from_url("http://localhost:8501", "dashboard.pdf")
    st.success("✅ Dashboard exported as PDF!")


# 🔹 2. Load DataFrames
dfs = {}
for name, path in FILES.items():
    if os.path.exists(path):  # Check if file exists
        dfs[name] = pd.read_csv(path)
    else:
        st.warning(f"⚠️ File not found: {path}")

# 🔹 3. Display DataFrames in Tabs
if dfs:
    tab1, tab2, tab3 = st.tabs(["🏠 Tenant Data", "🔧 Work Orders", "🏢 Vacancies"])
    
    with tab1:
        st.subheader("🏠 Tenant Data")
        st.write(dfs["Tenant Data"].head())

    with tab2:
        st.subheader("🔧 Work Orders")
        st.write(dfs["Work Orders"].head())

    with tab3:
        st.subheader("🏢 Vacancies")
        st.write(dfs["Vacancies"].head())

st.button("📄 Export Dashboard as PDF", on_click=save_pdf)
# **🔹 TAB 1: Financial Overview**
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # Filter rows where Status == 'Current' and count them
    current_units = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Current"].shape[0]
    vacant_units = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Vacant-Rented"].shape[0]
    # Count total rows (all units)
    all_units = dfs["Tenant Data"].shape[0]

    # Calculate occupancy percentage
    occupied = (current_units / all_units) * 100
    
    dfs["Tenant Data"]["Rent"] = dfs["Tenant Data"]["Rent"].replace("[\$,]", "", regex=True)  # Remove $ and ,
    dfs["Tenant Data"]["Rent"] = pd.to_numeric(dfs["Tenant Data"]["Rent"], errors="coerce")  # Convert to number
    dfs["Tenant Data"]["Market Rent"] = dfs["Tenant Data"]["Market Rent"].replace("[\$,]", "", regex=True)  # Remove $ and ,
    dfs["Tenant Data"]["Market Rent"] = pd.to_numeric(dfs["Tenant Data"]["Market Rent"], errors="coerce")  # Convert to number

    # Calculate total rent
    total_rent = dfs["Tenant Data"]["Rent"].sum()
    market_total_rent = dfs["Tenant Data"]["Market Rent"].sum()
    total_move_out = dfs["Tenant Data"]["Move-out"].notnull().sum()

    # Display the metric card
    col1.metric(label="🏠Total Unit", value=f"{all_units}")
    col2.metric(label="📊 Occupancy Rate", value=f"{occupied:.2f}%")
    col3.metric(label="💵 Total Rent Collected % ", value=f"{(total_rent)/(market_total_rent)*100:,.2f}%")
    col4.metric(label="🚪Total Move-outs", value=f"{total_move_out}")

    col5, col6 = st.columns(2)

    # Use col2 and col5 for two separate charts
    with col6:
        df_filtered = dfs["Tenant Data"].dropna(subset=["Tenant", "Late Count"]).copy()

        # **Convert "Late Count" to numeric**
        df_filtered["Late Count"] = pd.to_numeric(df_filtered["Late Count"], errors="coerce")
        df_filtered = df_filtered[df_filtered["Late Count"] > 2]
        df_filtered = df_filtered.sort_values(by="Late Count", ascending=False)

        # **Create Bar Chart**
        fig = px.bar(df_filtered, x="Tenant", y="Late Count", 
                    title="📊 Late Payment Frequency by Tenant",
                    labels={"Late Count": "Late Payment Count", "Tenant": "Tenant Name"},
                    color="Late Count",
                    text_auto=True)
        
        st.plotly_chart(fig, use_container_width=True)


    with col5:
        # Convert "Move-in" to datetime, handling errors
        dfs["Tenant Data"]["Move-in"] = pd.to_datetime(dfs["Tenant Data"]["Move-in"], errors="coerce")

        # Remove rows where "Move-in" is NaN (invalid dates)
        df = dfs["Tenant Data"].dropna(subset=["Move-in"])

        # Ensure "Rent" and "Market Rent" are numeric
        df["Rent"] = pd.to_numeric(df["Rent"], errors="coerce")
        df["Market Rent"] = pd.to_numeric(df["Market Rent"], errors="coerce")

        # Sort data by "Move-in" date
        df = df.sort_values("Move-in")

        # **Create a Line Chart**
        fig = px.line(df, x="Move-in", y=["Rent", "Market Rent"], 
                    title="📈 Rent Trends Over Time",
                    markers=True, labels={"value": "Amount ($)", "Move-in": "Move-in Date"})

        # Display the Line Chart
        st.plotly_chart(fig, use_container_width=True)


    
    col7, col8 = st.columns(2)

    # Use col2 and col5 for two separate charts
    with col7:
        # **Convert Lease Dates to Datetime**
        dfs["Tenant Data"]["Lease From"] = pd.to_datetime(dfs["Tenant Data"]["Lease From"], errors="coerce")
        dfs["Tenant Data"]["Lease To"] = pd.to_datetime(dfs["Tenant Data"]["Lease To"], errors="coerce")

        # **Calculate Lease Days**
        dfs["Tenant Data"]["Lease Days"] = (dfs["Tenant Data"]["Lease To"] - dfs["Tenant Data"]["Lease From"]).dt.days

        # **Drop invalid rows where Lease Days is NaN or negative**
        filtered_df = dfs["Tenant Data"].dropna(subset=["Lease Days"])
        filtered_df = filtered_df[filtered_df["Lease Days"] > 0]

       
        # **Ensure "SqFt" column is numeric**
        filtered_df["Sqft"] = pd.to_numeric(filtered_df["Sqft"], errors="coerce")

        # **Group by SqFt bins and Calculate Average Lease Days**
        filtered_df["Sqft Group"] = pd.cut(filtered_df["Sqft"], bins=10).astype(str)
        avg_lease_days_df = filtered_df.groupby("Sqft Group")["Lease Days"].mean().reset_index()

        # **Create a Bar Chart (Histogram Style)**
        fig_bar = px.bar(avg_lease_days_df, x="Sqft Group", y="Lease Days", 
                        title="📊 Avg Lease Days by Sqft Group",
                        labels={"Lease Days": "Avg Lease Duration (Days)", "Sqft Group": "Square Footage Range"},
                        color="Lease Days",
                        text_auto=True)
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col8:
        # Ensure "Status" column exists
        if "Status" in dfs["Tenant Data"].columns:
            status_counts = dfs["Tenant Data"]["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            # **Create Pie Chart**
            fig = px.pie(status_counts, values="Count", names="Status", 
                        title="🏠 Tenant Status Distribution", hole=0.4)

            # Display the Pie Chart
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 'Status' column not found in dataset.")

with tab2:
    col21, col22, col23, col24 = st.columns(4)
    
    # Filter rows where Status == 'Current' and count them
    new_work_orders = dfs["Work Orders"][dfs["Work Orders"]["Status"] == "New"].shape[0]
    urgent_work_orders = dfs["Work Orders"][dfs["Work Orders"]["Priority"] == "Urgent"].shape[0]
    # Count total rows (all units)
    all_work_order= dfs["Work Orders"].shape[0]

    
    dfs["Work Orders"]["Amount"] = dfs["Work Orders"]["Amount"].replace("[\$,]", "", regex=True)  # Remove $ and ,
    dfs["Work Orders"]["Amount"] = pd.to_numeric(dfs["Work Orders"]["Amount"], errors="coerce")  # Convert to number

    # Calculate total rent
    total_amount = dfs["Work Orders"]["Amount"].sum()
    market_total_rent = dfs["Tenant Data"]["Market Rent"].sum()
    total_move_out = dfs["Tenant Data"]["Move-out"].notnull().sum()

    # Display the metric card
    col21.metric(label="🛠️ Total work order", value=f"{all_work_order}")
    col22.metric(label="🆕New work orders", value=f"{new_work_orders}")
    col23.metric(label="⚠️Urgent work order ", value=f"{urgent_work_orders}")
    col24.metric(label="💰Total Amounts", value=f"${total_amount}")

    col26, col27 = st.columns(2)

    # Use col2 and col5 for two separate charts
        
    with col26:

        if "Work Order Type" in dfs["Work Orders"].columns:
            status_counts = dfs["Work Orders"]["Work Order Type"].value_counts().reset_index()
            status_counts.columns = ["Work Order Type", "Count"]

            # **Create Pie Chart**
            fig = px.pie(status_counts, values="Count", names="Work Order Type", 
                        title="🏠 Work Order Type Distribution", hole=0.4)

            # Display the Pie Chart
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 'Status' column not found in dataset.")
    with col27:
        df_filtered = dfs["Work Orders"].dropna(subset=["Work Order Issue"]).copy()

        # **Count work order frequency per unit**
        work_order_issue_counts = df_filtered["Work Order Issue"].value_counts().reset_index()
        work_order_issue_counts.columns = ["Work Order Issue", "Work Order Issue Count"]  # Rename columns

        # **Sort by Work Order Count in Descending Order & Show Top 20**
        work_order_issue_counts = work_order_issue_counts.sort_values(by="Work Order Issue Count", ascending=True).tail(20)

        # **Create Horizontal Bar Chart**
        figg = px.bar(work_order_issue_counts, x="Work Order Issue Count", y="Work Order Issue", 
                    title="📊 Work Order Frequency by Issue)",
                    labels={"Work Order Issue Count": "Work Order Issue Count", "Work Order Issue": "Work Order Issue"},
                    color="Work Order Issue Count",
                    color_continuous_scale="blues",  # Adjust color scale
                    text_auto=True,
                    orientation='h')  # Horizontal bars

        st.plotly_chart(figg, use_container_width=True)
with tab3:
    col31, col32, col33, col34 = st.columns(4)

        # **Filter Vacancy and Work Order Counts**
    rent_ready = dfs["Vacancies"][dfs["Vacancies"]["Rent Ready"] == "Yes"].shape[0]
    urgent_work_orders = dfs["Work Orders"][dfs["Work Orders"]["Priority"] == "Urgent"].shape[0]
    total_work_orders = dfs["Work Orders"].shape[0]
    total_vacancy = dfs["Vacancies"].shape[0]

        # **Convert "Days Vacant" to Numeric**
    dfs["Vacancies"]["Days Vacant"] = pd.to_numeric(
        dfs["Vacancies"]["Days Vacant"].replace("[\$,]", "", regex=True), 
        errors="coerce"
    )

        # **Calculate Average Days Vacant**
    avg_days_vacant = dfs["Vacancies"]["Days Vacant"].mean()

        # **Display Metric Cards**
    col31.metric(label="🏠 Total Vacancy", value=f"{total_vacancy}")
    col32.metric(label="✅ Rent Ready Units", value=f"{rent_ready}")
    col33.metric(label="⚠️ Urgent Work Orders", value=f"{urgent_work_orders}")
    col34.metric(label="📉 Avg Days Vacant", value=f"{avg_days_vacant:.1f} days")

        # **Create Another Row for More Metrics**
    col36, col37 = st.columns(2)

    

    with col36:
        df = dfs["Vacancies"]  # Ensure you're using the correct dataset key

        # **Convert Dates to Datetime**
        df["Last Move In"] = pd.to_datetime(df["Last Move In"], errors="coerce")
        df["Last Move Out"] = pd.to_datetime(df["Last Move Out"], errors="coerce")

        # **Extract Month-Year for Grouping**
        df["Move In Month"] = df["Last Move In"].dt.to_period("M")
        df["Move Out Month"] = df["Last Move Out"].dt.to_period("M")

        # **Count Move-Ins and Move-Outs per Month**
        move_in_counts = df["Move In Month"].value_counts().sort_index()
        move_out_counts = df["Move Out Month"].value_counts().sort_index()

        # **Create DataFrame for Plotting**
        move_trends = pd.DataFrame({"Move In": move_in_counts, "Move Out": move_out_counts}).fillna(0)
        move_trends.index = move_trends.index.to_timestamp()  # Convert Period to Timestamp

        # **Create Line Chart**
        fig = px.line(move_trends, 
                    x=move_trends.index, 
                    y=["Move In", "Move Out"],
                    markers=True,
                    title="📈 Move-In and Move-Out Trends by Month",
                    labels={"value": "Number of Vacancies", "index": "Month"},
                    line_shape="linear")

        # **Display in Streamlit**
        st.plotly_chart(fig, use_container_width=True)

    with col37:
        df1 = dfs["Vacancies"]  # Ensure you're using the correct dataset key

        # **Convert "Days Vacant" to Numeric**
        df1["Days Vacant"] = pd.to_numeric(df["Days Vacant"], errors="coerce")
        df1["Sqft"] = pd.to_numeric(df1["Sqft"], errors="coerce")

        # **Drop NaN values**
        df_filtered1 = df1.dropna(subset=["Sqft", "Days Vacant"])

        # **Create Scatter Plot**
        fig = px.scatter(df_filtered1, 
                        x="Sqft", 
                        y="Days Vacant",
                        title="📊 Relationship Between Square Footage and Days Vacant",
                        labels={"Sqft": "Square Footage", "Days Vacant": "Days Vacant"},
                        color="Days Vacant",
                        size="Days Vacant",
                        hover_data=["Sqft", "Days Vacant"])

        # **Display in Streamlit**
        st.plotly_chart(fig, use_container_width=True)

    col38, col39 = st.columns(2)

    # Use col2 and col5 for two separate charts
        
    with col38:
     
        status_counts = dfs["Vacancies"]["Unit Status"].value_counts().reset_index()
        status_counts.columns = ["Unit Status", "Count"]

            # **Create Pie Chart**
        fig1 = px.pie(status_counts, values="Count", names="Unit Status", 
                    title="🏠 Unit Status Distribution", hole=0.4)

            # Display the Pie Chart
        st.plotly_chart(fig1, use_container_width=True)
        
