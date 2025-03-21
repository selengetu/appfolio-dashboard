import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta
# Set page layout
st.set_page_config(page_title="Business Dashboards", layout="wide")

try:
    import kaleido  # Required for Plotly image export
except ImportError:
    st.warning("Installing required package: kaleido")
    os.system("pip install kaleido")

BASE_DIR = os.path.join(os.getcwd(), "data")  # Use relative path

st.title("📊 Appfolio Dashboards")
# Define file prefixes
file_prefixes = {
    "Tenant Data": "rent_roll",
    "Work Orders": "work_order",
    "Vacancies": "unit_vacancy_detail",
    "T_rent": "t_rent",
    "Beg Year": "beg_year",
    "Sameday": "same_day",
}

# Initialize a dictionary to store the latest file for each category
latest_files = {}

# List all files in the BASE_DIR
files_in_directory = os.listdir(BASE_DIR)

# Function to extract date from the filename
def extract_date_from_filename(filename):
    # Assuming the date format is YYYYMMDD just before the .csv extension
    date_str = filename.split('-')[-1].split('.')[0]  # Extract the date part
    return datetime.strptime(date_str, "%Y%m%d")

# Iterate through each category and find the latest file
for category, prefix in file_prefixes.items():
    # Filter files based on the prefix
    relevant_files = [f for f in files_in_directory if f.startswith(prefix) and f.endswith(".csv")]
    
    if relevant_files:
        # Sort the files by the date extracted from their filenames in descending order (latest first)
        latest_file = max(relevant_files, key=extract_date_from_filename)
        latest_files[category] = os.path.join(BASE_DIR, latest_file)

# Print the latest files for each category
for category, file_path in latest_files.items():
    print(f"Latest {category}: {file_path}")
    
FILES = {
    "Tenant Data": latest_files.get("Tenant Data"),
    "Work Orders": latest_files.get("Work Orders"),
    "Vacancies": latest_files.get("Vacancies"),
    "T_rent": latest_files.get("T_rent"),
    "Beg Year": latest_files.get("Beg Year"),
    "Sameday": latest_files.get("Sameday")
}
# 🔹 2. Load DataFrames
dfs = {}
for name, path in FILES.items():
    if os.path.exists(path):  # Check if file exists
        dfs[name] = pd.read_csv(path)
    else:
        st.warning(f"⚠️ File not found: {path}")
# Create folder for images
IMG_DIR = "plotly_images"
os.makedirs(IMG_DIR, exist_ok=True)

# 🔹 Generate and Save Plotly Charts as Images
image_paths = []
# 🔹 3. Display DataFrames in Tabs
if dfs:
    tab1, tab2, tab3 = st.tabs(["🏠 Tenant Data", "🔧 Work Orders", "🏢 Vacancies"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    # Filter rows where Status == 'Current' and count them
    current = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Current"].shape[0]
    unrented = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Notice-Unrented"].shape[0]
    current_units = current+unrented
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
    col3.metric(label="💵 Total Rent ", value=f"${(total_rent):,.0f}")
    col4.metric(label="🚪Total Move-outs (Next 60 days)", value=f"{total_move_out}")

    col5 = st.columns(1)[0] 
    

    with col5:

        tenant_df = dfs["Tenant Data"]  # Ensure the correct dataset key
        tenant_df["Rent"] = pd.to_numeric(tenant_df["Rent"], errors="coerce")
        total_units = tenant_df.groupby("BD/BA").size()
        occupied_units = tenant_df[tenant_df["Status"].isin(["Current", "Notice-Unrented", "Notice-Rented"])].groupby("BD/BA").size()
        bd_ba_summary = pd.DataFrame({
            "Total_Rent": tenant_df.groupby("BD/BA")["Rent"].sum(),
            "Total_Units": total_units,
            "Occupied_Units": occupied_units
        }).fillna(0)  # Fill NaN for BD/BA groups without occupied units

        bd_ba_summary["Occupancy_Rate"] = (bd_ba_summary["Occupied_Units"] / bd_ba_summary["Total_Units"]) * 100
        bd_ba_summary["Occupancy_Rate"] = bd_ba_summary["Occupancy_Rate"].round(2).astype(str) + "%"


        total_rent = bd_ba_summary["Total_Rent"].sum()
        total_units_all = bd_ba_summary["Total_Units"].sum()
        occupied_units_all = bd_ba_summary["Occupied_Units"].sum()

        overall_occupancy_rate = (occupied_units_all / total_units_all) * 100 if total_units_all > 0 else 0
        overall_occupancy_rate = f"{round(overall_occupancy_rate, 2)}%"
        bd_ba_summary["Total_Rent"] = bd_ba_summary["Total_Rent"].apply(lambda x: f"${x:,.2f}")

        # 🔹 **Append "Total" Row**
        total_row = pd.DataFrame([{
            "BD/BA": "Total",
            "Total_Rent": f"${total_rent:,.2f}",
            "Occupancy_Rate": overall_occupancy_rate
        }])

        bd_ba_summary = bd_ba_summary.drop(columns=["Total_Units", "Occupied_Units"])
        bd_ba_summary = bd_ba_summary.reset_index()
        bd_ba_summary = pd.concat([bd_ba_summary, total_row], ignore_index=True)

        three_month_df = dfs["T_rent"]  # Ensure the correct dataset key

        # 1. Clean the Rent column (remove $ and ,)
        three_month_df["Rent"] = (
            three_month_df["Rent"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
            .str.strip()
        )

        # 2. Then convert to numeric
        three_month_df["Rent"] = pd.to_numeric(three_month_df["Rent"], errors="coerce")

        # ✅ Print to confirm
        three_month_total_units = three_month_df.groupby("BD/BA").size()
        three_month_occupied_units = three_month_df[three_month_df["Status"].isin(["Current", "Notice-Unrented", "Notice-Rented"])].groupby("BD/BA").size()
        three_month_bd_ba_summary = pd.DataFrame({
            "Total_Rent": three_month_df.groupby("BD/BA")["Rent"].sum(),
            "Total_Units": three_month_total_units,
            "Occupied_Units": three_month_occupied_units
        }).fillna(0)  # Fill NaN for BD/BA groups without occupied units

        three_month_bd_ba_summary["Occupancy_Rate"] = (three_month_bd_ba_summary["Occupied_Units"] / three_month_bd_ba_summary["Total_Units"]) * 100
        three_month_bd_ba_summary["Occupancy_Rate"] = three_month_bd_ba_summary["Occupancy_Rate"].round(2).astype(str) + "%"

        three_month_total_rent = three_month_bd_ba_summary["Total_Rent"].sum()
        three_month_total_units_all = three_month_bd_ba_summary["Total_Units"].sum()
        three_month_occupied_units_all = three_month_bd_ba_summary["Occupied_Units"].sum()

        three_month_overall_occupancy_rate = (three_month_occupied_units_all / three_month_total_units_all) * 100 if three_month_total_units_all > 0 else 0
        three_month_overall_occupancy_rate = f"{round(three_month_overall_occupancy_rate, 2)}%"
        three_month_bd_ba_summary["Total_Rent"] = three_month_bd_ba_summary["Total_Rent"].apply(lambda x: f"${x:,.2f}")

        # 🔹 **Append "Total" Row**
        three_month_total_row = pd.DataFrame([{
            "BD/BA": "Total",
            "Total_Rent": f"${three_month_total_rent:,.2f}",
            "Occupancy_Rate": three_month_overall_occupancy_rate
        }])

        three_month_bd_ba_summary = three_month_bd_ba_summary.drop(columns=["Total_Units", "Occupied_Units"])
        three_month_bd_ba_summary = three_month_bd_ba_summary.reset_index()
        three_month_bd_ba_summary = pd.concat([three_month_bd_ba_summary, three_month_total_row], ignore_index=True)

        beg_year_df = dfs["Beg Year"]  # Ensure the correct dataset key

        # 1. Clean the Rent column (remove $ and ,)
        beg_year_df["Rent"] = (
            beg_year_df["Rent"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
            .str.strip()
        )

        # 2. Then convert to numeric
        beg_year_df["Rent"] = pd.to_numeric(beg_year_df["Rent"], errors="coerce")

        # ✅ Print to confirm
        beg_year_total_units = beg_year_df.groupby("BD/BA").size()
        beg_year_occupied_units = beg_year_df[beg_year_df["Status"].isin(["Current", "Notice-Unrented", "Notice-Rented"])].groupby("BD/BA").size()
        beg_year_bd_ba_summary = pd.DataFrame({
            "Total_Rent": beg_year_df.groupby("BD/BA")["Rent"].sum(),
            "Total_Units": beg_year_total_units,
            "Occupied_Units": beg_year_occupied_units
        }).fillna(0)  # Fill NaN for BD/BA groups without occupied units

        beg_year_bd_ba_summary["Occupancy_Rate"] = (beg_year_bd_ba_summary["Occupied_Units"] / beg_year_bd_ba_summary["Total_Units"]) * 100
        beg_year_bd_ba_summary["Occupancy_Rate"] = beg_year_bd_ba_summary["Occupancy_Rate"].round(2).astype(str) + "%"


        beg_year_total_rent = beg_year_bd_ba_summary["Total_Rent"].sum()
        beg_year_total_units_all = beg_year_bd_ba_summary["Total_Units"].sum()
        beg_year_occupied_units_all = beg_year_bd_ba_summary["Occupied_Units"].sum()

        beg_year_overall_occupancy_rate = (beg_year_occupied_units_all / beg_year_total_units_all) * 100 if beg_year_total_units_all > 0 else 0
        beg_year_overall_occupancy_rate = f"{round(beg_year_overall_occupancy_rate, 2)}%"
        beg_year_bd_ba_summary["Total_Rent"] = beg_year_bd_ba_summary["Total_Rent"].apply(lambda x: f"${x:,.2f}")

        # 🔹 **Append "Total" Row**
        beg_year_total_row = pd.DataFrame([{
            "BD/BA": "Total",
            "Total_Rent": f"${beg_year_total_rent:,.2f}",
            "Occupancy_Rate": beg_year_overall_occupancy_rate
        }])

        beg_year_bd_ba_summary = beg_year_bd_ba_summary.drop(columns=["Total_Units", "Occupied_Units"])
        beg_year_bd_ba_summary = beg_year_bd_ba_summary.reset_index()
        beg_year_bd_ba_summary = pd.concat([beg_year_bd_ba_summary, beg_year_total_row], ignore_index=True)

        same_day_df = dfs["Sameday"]  # Ensure the correct dataset key

        # 1. Clean the Rent column (remove $ and ,)
        same_day_df["Rent"] = (
            same_day_df["Rent"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
            .str.strip()
        )

        # 2. Then convert to numeric
        same_day_df["Rent"] = pd.to_numeric(same_day_df["Rent"], errors="coerce")

        # ✅ Print to confirm
        same_day_total_units = same_day_df.groupby("BD/BA").size()
        same_day_occupied_units = same_day_df[same_day_df["Status"].isin(["Current", "Notice-Unrented", "Notice-Rented"])].groupby("BD/BA").size()
        same_day_bd_ba_summary = pd.DataFrame({
            "Total_Rent": same_day_df.groupby("BD/BA")["Rent"].sum(),
            "Total_Units": same_day_total_units,
            "Occupied_Units": same_day_occupied_units
        }).fillna(0)  # Fill NaN for BD/BA groups without occupied units

        same_day_bd_ba_summary["Occupancy_Rate"] = (same_day_bd_ba_summary["Occupied_Units"] / same_day_bd_ba_summary["Total_Units"]) * 100
        same_day_bd_ba_summary["Occupancy_Rate"] = same_day_bd_ba_summary["Occupancy_Rate"].round(2).astype(str) + "%"


        same_day_total_rent = same_day_bd_ba_summary["Total_Rent"].sum()
        same_day_total_units_all = same_day_bd_ba_summary["Total_Units"].sum()
        same_day_occupied_units_all = same_day_bd_ba_summary["Occupied_Units"].sum()

        same_day_overall_occupancy_rate = (same_day_occupied_units_all / same_day_total_units_all) * 100 if same_day_total_units_all > 0 else 0
        same_day_overall_occupancy_rate = f"{round(same_day_overall_occupancy_rate, 2)}%"
        same_day_bd_ba_summary["Total_Rent"] = same_day_bd_ba_summary["Total_Rent"].apply(lambda x: f"${x:,.2f}")

        # 🔹 **Append "Total" Row**
        same_day_total_row = pd.DataFrame([{
            "BD/BA": "Total",
            "Total_Rent": f"${same_day_total_rent:,.2f}",
            "Occupancy_Rate": same_day_overall_occupancy_rate
        }])

        same_day_bd_ba_summary = same_day_bd_ba_summary.drop(columns=["Total_Units", "Occupied_Units"])
        same_day_bd_ba_summary = same_day_bd_ba_summary.reset_index()
        same_day_bd_ba_summary = pd.concat([same_day_bd_ba_summary, same_day_total_row], ignore_index=True)

            # Rename columns before merging
        bd_ba_summary = bd_ba_summary.rename(columns={
            "Total_Rent": "Current Total_Rent",
            "Occupancy_Rate": "Current Occupancy_Rate"
        })

        three_month_bd_ba_summary = three_month_bd_ba_summary.rename(columns={
            "Total_Rent": "3Mo Ago Total_Rent",
            "Occupancy_Rate": "3Mo Ago Occupancy_Rate"
        })
        beg_year_bd_ba_summary = beg_year_bd_ba_summary.rename(columns={
            "Total_Rent": "Beginning of Year Total_Rent",
            "Occupancy_Rate": "Beginning of Year Occupancy_Rate"
        })
        same_day_bd_ba_summary = same_day_bd_ba_summary.rename(columns={
            "Total_Rent": "Same Day of Last Year Total_Rent",
            "Occupancy_Rate": "Same Day of Last Year Occupancy_Rate"
        })


        # Merge on "BD/BA"
        combined_summary = pd.merge(
            bd_ba_summary,
            three_month_bd_ba_summary,
            on="BD/BA",
            how="outer"
        )

        # Then merge with beginning of year summary
        combined_summary = pd.merge(
            combined_summary,
            beg_year_bd_ba_summary,
            on="BD/BA",
            how="outer"
        )

        combined_summary = pd.merge(
            combined_summary,
            same_day_bd_ba_summary,
            on="BD/BA",
            how="outer"
        )

        # Optional: Fill missing with "-"
        combined_summary = combined_summary.fillna("-")

        # Display in Streamlit
        st.write("### 📊 Comparison: Current vs 3-Month-Ago Rent & Occupancy")
        st.dataframe(combined_summary, use_container_width=True)

            
    col7, col8 = st.columns(2)

    # Use col2 and col5 for two separate charts
    with col7:
            # Ensure Rent and Market Rent are numeric
        dfs["Tenant Data"]["Rent"] = pd.to_numeric(dfs["Tenant Data"]["Rent"], errors="coerce")
        dfs["Tenant Data"]["Market Rent"] = pd.to_numeric(dfs["Tenant Data"]["Market Rent"], errors="coerce")

        # Drop invalid rows where Rent or Market Rent is NaN
        filtered_df = dfs["Tenant Data"].dropna(subset=["Rent", "Market Rent"])

        # Group by BD/BA and Calculate Avg Rent and Market Rent
        avg_rent_df = filtered_df.groupby("BD/BA")[["Rent", "Market Rent"]].mean().round(0).reset_index()

        # Count the number of units per BD/BA
        unit_count_df = filtered_df.groupby("BD/BA").size().reset_index(name="Unit Count")

        # Merge DataFrames to align BD/BA categories
        final_df = avg_rent_df.merge(unit_count_df, on="BD/BA")

        # Create figure with Bar Chart for Rent & Market Rent
        fig3 = go.Figure()

        # Add Rent bars
        fig3.add_trace(go.Bar(
            x=final_df["BD/BA"], 
            y=final_df["Rent"], 
            name="Avg Rent",
            marker_color="blue",
            text=final_df["Rent"], 
            textposition="auto"
        ))

        # Add Market Rent bars
        fig3.add_trace(go.Bar(
            x=final_df["BD/BA"], 
            y=final_df["Market Rent"], 
            name="Avg Market Rent",
            text=final_df["Market Rent"], 
            textposition="auto"
        ))

        # Add Line Chart for Unit Count (Secondary Y-Axis)
        fig3.add_trace(go.Scatter(
            x=final_df["BD/BA"], 
            y=final_df["Unit Count"], 
            name="Unit Count",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="yellow", width=2),
            marker=dict(size=8, symbol="circle"),
        ))

        fig3.update_layout(
            title="📊 Avg Rent vs. Market Rent with Unit Count by BD/BA",
            xaxis=dict(
                title=dict(text="Bedroom/Bathroom"), 
                tickangle=-45, 
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title=dict(text="Amount ($)"), 
                gridcolor="lightgray"
            ),
            yaxis2=dict(
                title=dict(text="Unit Count"), 
                overlaying="y", 
                side="right", 
                showgrid=False
            ),
            legend=dict(title=dict(text="Legend")),
            width=1000, height=600,
            bargap=0.15,  # Reduce gap between bars
            barmode="group"
        )
                # Display in Streamlit
        st.plotly_chart(fig3, use_container_width=True)

    with col8:
        # Ensure "Status" column exists
        if "Status" in dfs["Tenant Data"].columns:
            status_counts = dfs["Tenant Data"]["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            # **Create Pie Chart**
            fig4 = px.pie(status_counts, 
             values="Count", 
             names="Status", 
             title="🏠 Tenant Status Distribution", 
             hole=0.4,  # Creates a donut-style pie chart
             color_discrete_sequence=px.colors.qualitative.Set3)  # Custom colors

            # 🔹 Improve Layout & Style
            fig4.update_layout(
                width=800, height=600,  # Bigger chart
            )

            # 🔹 Customize Legend
            fig4.update_layout(
                legend=dict(
                    font=dict(size=14),  # Bigger font for legend
                    x=1, y=0.9,  # Position legend to the right
                    xanchor="right"
                )
            )

            # 🔹 Show Percentages & Labels
            fig4.update_traces(
                textinfo="percent+label",  # Display both labels and percentages
                pull=[0.1 if i == 0 else 0 for i in range(len(status_counts))],  # Slightly pull out the first slice

            )   

            # Display the Pie Chart
            st.plotly_chart(fig4, use_container_width=True)
 
        else:
            st.warning("⚠️ 'Status' column not found in dataset.")

    col9 = st.columns(1)[0] 

    # Use col2 and col5 for two separate charts
    with col9:
        df_filtered = dfs["Tenant Data"].dropna(subset=["Tenant", "Late Count"]).copy()

        # **Convert "Late Count" to numeric**
        df_filtered["Late Count"] = pd.to_numeric(df_filtered["Late Count"], errors="coerce")
        df_filtered = df_filtered[df_filtered["Late Count"] > 2]
        df_filtered = df_filtered.sort_values(by="Late Count", ascending=False)

        # **Create Bar Chart**
        fig1 = px.bar(df_filtered, x="Tenant", y="Late Count", 
                    title="📊 Late Payment Frequency by Tenant",
                    labels={"Late Count": "Late Payment Count", "Tenant": "Tenant Name"},
                    color="Late Count",
                    text_auto=True,
                    color_continuous_scale="Blues")
        fig1.update_layout(
        height=600, width=1000,  # Bigger figure
        margin=dict(l=50, r=50, t=50, b=150)  # Adjust margins
    )

# 🔹 Rotate x-axis labels
        fig1.update_xaxes(tickangle=-45) 
        st.plotly_chart(fig1, use_container_width=True)

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
            fig5 = px.pie(status_counts, 
             values="Count", 
             names="Work Order Type", 
             title="🏠 Work Order Type Distribution", 
             hole=0.3,  # Donut chart effect
             color_discrete_sequence=px.colors.sequential.Viridis)  # Custom color scale

            # 🔹 Improve Layout & Style
            fig5.update_layout(
                width=800, height=600,  # Bigger size

            )

            # 🔹 Customize Legend
            fig5.update_layout(
                legend=dict(
                    font=dict(size=14),  # Bigger legend font
                    orientation="h",  # Horizontal legend
                    x=0.5, y=-0.2,  # Centered below chart
                    xanchor="center"
                )
            )

            # 🔹 Show Percentage & Labels
            fig5.update_traces(
                textinfo="percent+label",  # Show % and category
                pull=[0.1 if i == 0 else 0 for i in range(len(status_counts))],  # Emphasize the first slice
            )

            # Display the Pie Chart
            st.plotly_chart(fig5, use_container_width=True)

        else:
            st.warning("⚠️ 'Status' column not found in dataset.")
    with col27:
        df_filtered = dfs["Work Orders"].dropna(subset=["Work Order Issue"]).copy()

        # **Count work order frequency per unit**
        work_order_issue_counts = df_filtered["Work Order Issue"].value_counts().reset_index()
        work_order_issue_counts.columns = ["Work Order Issue", "Work Order Issue Count"]  # Rename columns

        # **Sort by Work Order Count in Descending Order & Show Top 20**
        work_order_issue_counts = work_order_issue_counts.sort_values(by="Work Order Issue Count", ascending=True).tail(20)

        fig6 = px.bar(
            work_order_issue_counts, 
            x="Work Order Issue Count", 
            y="Work Order Issue", 
            title="📊 Work Order Frequency by Issue",
            labels={"Work Order Issue Count": "Work Order Issue Count", "Work Order Issue": "Work Order Issue"},
            color="Work Order Issue Count",
            color_continuous_scale="Viridis",  # Gradient color
            text_auto=True,
            orientation='h'  # Horizontal bars
        )

        # 🔹 Improve Layout & Style
        fig6.update_layout(
            width=1100, height=600,  # Bigger size
            coloraxis_showscale=False,  # Hide the color scale bar
            margin=dict(t=50, b=50, l=200, r=50)  # Adjust margins to give more space
        )

        # 🔹 Customize X-Axis
        fig6.update_xaxes(
            title_text="Work Order Issue Count",
            tickangle=0,  # Keep horizontal for clarity
            showgrid=True,
            gridcolor="lightgray"
        )

        # 🔹 Customize Y-Axis
        fig6.update_yaxes(
            title_text="Work Order Issue",
            showgrid=False,  # Remove grid to keep it clean
            tickmode="array",  # Ensure that each label is spaced out properly
        )
        fig6.update_traces(
            textposition="outside",  # Position text outside the bars
            textfont=dict(size=12),  # Reduce font size to prevent overlap
        )
        # Display the chart
        st.plotly_chart(fig6, use_container_width=True)

with tab3:
    col31, col32, col33, col34 = st.columns(4)

        # **Filter Vacancy and Work Order Counts**
    rent_ready = dfs["Vacancies"][dfs["Vacancies"]["Rent Ready"] == "Yes"].shape[0]
    urgent_work_orders = dfs["Work Orders"][dfs["Work Orders"]["Priority"] == "Urgent"].shape[0]
    next_move_in = dfs["Vacancies"]["Next Move In"].notnull().sum()
    
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
    col33.metric(label="🆕 Upcoming Move In", value=f"{next_move_in}")
    col34.metric(label="📉 Avg Days Vacant", value=f"{avg_days_vacant:.1f} days")

        # **Create Another Row for More Metrics**
    col36, col37 = st.columns(2)

    with col36:
       
        status_counts = dfs["Vacancies"]["Unit Status"].value_counts().reset_index()
        status_counts.columns = ["Unit Status", "Count"]

            # **Create Pie Chart**
        fig9 = px.pie(status_counts, 
              values="Count", 
              names="Unit Status", 
              title="🏠 Unit Status Distribution", 
              hole=0.4,  # Creates a donut-style pie chart
              color_discrete_sequence=px.colors.qualitative.Set3)  # Custom colors

        # 🔹 Improve Layout & Style
        fig9.update_layout(
            width=800, height=600,  # Bigger chart
            margin=dict(l=50, r=50, t=50, b=50)  # Adjust margins
        )

        # 🔹 Customize Legend
        fig9.update_layout(
            legend=dict(
                font=dict(size=14),  # Bigger font for legend
                x=1, y=0.9,  # Position legend to the right
                xanchor="right"
            )
        )

        # 🔹 Show Percentages & Labels
        fig9.update_traces(
            textinfo="percent+label",  # Display both labels and percentages
            pull=[0.1 if i == 0 else 0 for i in range(len(status_counts))]  # Slightly pull out the first slice
        )

        st.plotly_chart(fig9, use_container_width=True)


    with col37:
       
        df1 = dfs["Vacancies"]  # Ensure you're using the correct dataset key

        # Convert "Days Vacant" to numeric
        df1["Days Vacant"] = pd.to_numeric(df1["Days Vacant"], errors="coerce")

        # Drop missing values
        df_filtered1 = df1.dropna(subset=["Bed/Bath", "Days Vacant"])

        # Aggregate data: Calculate average "Days Vacant" per "Bed/Bath"
        df_avg_vacancy = df_filtered1.groupby("Bed/Bath", as_index=False)["Days Vacant"].mean().round(1)

        # Aggregate data: Count the number of units per "Bed/Bath"
        df_units_count = df_filtered1.groupby("Bed/Bath", as_index=False).size()

        # Merge both datasets for consistency in sorting
        df_combined = df_avg_vacancy.merge(df_units_count, on="Bed/Bath").sort_values(by="Bed/Bath")

        # Create Bar Chart for "Avg Days Vacant"
        fig8 = go.Figure()

        fig8.add_trace(
            go.Bar(
                x=df_combined["Bed/Bath"],
                y=df_combined["Days Vacant"],
                name="Avg Days Vacant",
                marker=dict(color=df_combined["Days Vacant"], colorscale="Blugrn"),  # Color scale
                text=df_combined["Days Vacant"],
                textposition="auto"
            )
        )

        # Add Line Chart for "Number of Units"
        fig8.add_trace(
            go.Scatter(
                x=df_combined["Bed/Bath"],
                y=df_combined["size"],  # Number of units
                name="Number of Units",
                mode="lines+markers",
                line=dict(color="red", width=2),
                marker=dict(size=8, symbol="circle"),
                yaxis="y2"  # Use secondary y-axis
            )
        )

        # 🔹 Improve Layout & Style
        fig8.update_layout(
            title="📊 Average Days Vacant & Number of Units by Bed/Bath",
            xaxis=dict(title="Bedroom/Bathroom", title_font=dict(size=14), tickfont=dict(size=12)),
            yaxis=dict(title="Avg Days Vacant", title_font=dict(size=14), tickfont=dict(size=12), gridcolor="lightgray"),
            yaxis2=dict(
                title="Number of Units",
                overlaying="y",
                side="right",
                showgrid=False,
                title_font=dict(size=14),
                tickfont=dict(size=12),
            ),
            legend=dict(title="Metrics", font=dict(size=12)),
            width=1000, height=600,  # Bigger size
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Show the chart in Streamlit
        st.plotly_chart(fig8, use_container_width=True)

    col38, col39 = st.columns(2)

    # Use col2 and col5 for two separate charts
        
    with col38:

        df3 = dfs["Vacancies"]  # Ensure you're using the correct dataset key

        # Drop rows missing key info
        df3 = df3.dropna(subset=["Bed/Bath", "Unit Status"])
     
        # Group by unit type and status
        status_counts = df3.groupby(["Bed/Bath", "Unit Status"]).size().unstack(fill_value=0)
        status_counts = status_counts.reset_index()

       # Create a stacked bar chart
        fig7 = go.Figure()
        custom_colors = {
            "Vacant-Unrented": "#72c0a7",  # Deep orange
            "Vacant-Rented": "#1E90FF",  # Blue
            "Notice-Unrented": "#87CEFA"  # Light blue
        }
        # Loop through each status column to stack bars
        for status in status_counts.columns[1:]:
            fig7.add_trace(go.Bar(
                x=status_counts["Bed/Bath"],
                y=status_counts[status],
                name=status,
                marker=dict(color=custom_colors.get(status, "#CCCCCC")),  # Apply color here
                text=status_counts[status],  # Add data labels
            ))
    
        # Customize layout
        fig7.update_layout(
            barmode="stack",
            title="🏘️ Unit Type Breakdown by Status",
            xaxis_title="Unit Type (BD/BA)",
            yaxis_title="Number of Units",
            width=1000,
            height=600,
            legend_title="Unit Status",
            margin=dict(l=40, r=40, t=60, b=40)
        )

        # Show in Streamlit
        st.plotly_chart(fig7, use_container_width=True)
     
       
    with col39:
                # Today's date
        today = pd.Timestamp.today()

        # 60 days from now
        future_cutoff = today + pd.Timedelta(days=60)
        rent_ready_df = dfs["Vacancies"]

            # Parse the relevant date columns
        rent_ready_df["Last Move Out"] = pd.to_datetime(rent_ready_df["Last Move Out"], errors="coerce")
        rent_ready_df["Next Move In"] = pd.to_datetime(rent_ready_df["Next Move In"], errors="coerce")

        # Filter for the next 60 days
        upcoming_move_outs = rent_ready_df[
            (rent_ready_df["Last Move Out"].notna()) &
            (rent_ready_df["Last Move Out"] >= today) &
            (rent_ready_df["Last Move Out"] <= future_cutoff)
        ]

        upcoming_move_ins = rent_ready_df[
            (rent_ready_df["Next Move In"].notna()) &
            (rent_ready_df["Next Move In"] >= today) &
            (rent_ready_df["Next Move In"] <= future_cutoff)
        ]

        # Count per day
        move_out_counts = upcoming_move_outs["Last Move Out"].dt.date.value_counts().sort_index()
        move_in_counts = upcoming_move_ins["Next Move In"].dt.date.value_counts().sort_index()

        # Combine counts into a DataFrame
        move_summary_df = pd.DataFrame({
            "Last Move Out": move_out_counts,
            "Next Move In": move_in_counts
        }).fillna(0)

        # Convert index to string for plotting
        move_summary_df.index = move_summary_df.index.astype(str)

        # 🔹 **Plot the improved bar chart**
        fig10 = px.bar(
            move_summary_df,
            x=move_summary_df.index,
            y=["Last Move Out", "Next Move In"],
            title="📊 Upcoming Move-Outs and Move-Ins (Next 60 Days)",
            labels={"value": "Count of Units", "index": "Date"},
            barmode="group",
            text_auto=True,
            color_discrete_sequence=["#EF553B", "#636EFA"]  # Red & Blue
        )

        fig10.update_layout(
            xaxis=dict(title="Date", tickangle=45),
            yaxis=dict(title="Count of Units", gridcolor="lightgray"),
            width=1000, height=600,
            margin=dict(l=50, r=50, t=50, b=50)
                )

        # Display in Streamlit
        st.plotly_chart(fig10, use_container_width=True)
                

    with tab1:
        st.subheader("🏠 Tenant Data")
        st.write(dfs["Tenant Data"])

    with tab2:
        st.subheader("🔧 Work Orders")
        st.write(dfs["Work Orders"])

    with tab3:
        st.subheader("🏢 Vacancies")
        st.write(dfs["Vacancies"])


    # Define the metrics dictionary
    def convert_values(data):
        return {key: [{"label": item["label"], "value": str(item["value"])} for item in value] for key, value in data.items()}

    # Convert metrics data
    metrics_data = {
        "metrics1": [
            {"label": "Total Unit", "value": int(all_units)},
            {"label": "Occupancy Rate", "value": f"{occupied:.2f}%"},
            {"label": "Total Rent Collected %", "value": f"{(total_rent)/(market_total_rent)*100:,.2f}%"},
            {"label": "Total Move-outs", "value": int(total_move_out)}
        ],
        "metrics2": [
            {"label": "Total Vacancy", "value": int(total_vacancy)},
            {"label": "Rent Ready Units", "value": int(rent_ready)},
            {"label": "Upcoming Move In", "value": int(next_move_in)},
            {"label": "Avg Days Vacant", "value": f"{avg_days_vacant:.1f} days"}
        ],
        "metrics3": [
            {"label": "Total Workorder", "value": int(all_work_order)},
            {"label": "New work orders", "value": int(new_work_orders)},
            {"label": "Urgent Work Orders", "value": int(urgent_work_orders)},
            {"label": "Total Amounts", "value": f"${total_amount}"}
        ]
    }

    # Convert to JSON-friendly format
    metrics_data_fixed = convert_values(metrics_data)

    # Save to JSON file
    json_file = "metrics.json"
    with open(json_file, "w") as f:
        json.dump(metrics_data_fixed, f, indent=4)
