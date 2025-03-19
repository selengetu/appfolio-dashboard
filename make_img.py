import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import os
import json
from datetime import datetime

try:
    import kaleido  # Required for Plotly image export
except ImportError:
    st.warning("Installing required package: kaleido")
    os.system("pip install kaleido")

# Define directory paths
BASE_DIR = os.path.join('/Users/selengetulga/Downloads')  # Use relative path
IMG_DIR = "plotly_pdf_images"
os.makedirs(IMG_DIR, exist_ok=True)

# Define file prefixes
file_prefixes = {
    "Tenant Data": "rent_roll",
    "Work Orders": "work_order",
    "Vacancies": "unit_vacancy_detail"
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
}
image_paths = []
dfs = {}

# Load CSV files
for name, path in FILES.items():
    if os.path.exists(path):  # Check if file exists
        dfs[name] = pd.read_csv(path)
    else:
        st.warning(f"⚠️ File not found: {path}")

# Process the tenant data
tenant_data = dfs.get("Tenant Data")
if tenant_data is not None:
    # Extract unit status
    current_units = tenant_data[tenant_data["Status"] == "Current"].shape[0]
    vacant_units = tenant_data[tenant_data["Status"] == "Vacant-Rented"].shape[0]
    all_units = tenant_data.shape[0]

    # Occupancy percentage
    occupied = (current_units / all_units) * 100

    # Clean rent columns
    tenant_data["Rent"] = tenant_data["Rent"].replace("[\$,]", "", regex=True)
    tenant_data["Rent"] = pd.to_numeric(tenant_data["Rent"], errors="coerce")
    tenant_data["Market Rent"] = tenant_data["Market Rent"].replace("[\$,]", "", regex=True)
    tenant_data["Market Rent"] = pd.to_numeric(tenant_data["Market Rent"], errors="coerce")

    # Calculate total rents
    total_rent = tenant_data["Rent"].sum()
    market_total_rent = tenant_data["Market Rent"].sum()
    total_move_out = tenant_data["Move-out"].notnull().sum()

    # Filter for late payments
    df_filtered = tenant_data.dropna(subset=["Tenant", "Late Count"]).copy()
    df_filtered["Late Count"] = pd.to_numeric(df_filtered["Late Count"], errors="coerce")
    df_filtered = df_filtered[df_filtered["Late Count"] > 2]
    df_filtered = df_filtered.sort_values(by="Late Count", ascending=False)

    # Create Bar Chart for Late Payments
    fig1 = px.bar(df_filtered, x="Tenant", y="Late Count", 
                  title="📊 Late Payment Frequency by Tenant",
                  labels={"Late Count": "Late Payment Count", "Tenant": "Tenant Name"},
                  color="Late Count", text_auto=True, color_continuous_scale="Blues")
    fig1.update_layout(height=600, width=1000, margin=dict(l=50, r=50, t=50, b=150))
    fig1.update_xaxes(tickangle=-45)
    img_path1 = os.path.join(IMG_DIR, "tenant_status.png")
    fig1.write_image(img_path1)
    image_paths.append(img_path1)

    # Process move-in data
    tenant_data["Move-in"] = pd.to_datetime(tenant_data["Move-in"], errors="coerce")
    df_move_in = tenant_data.dropna(subset=["Move-in"]).sort_values("Move-in")

    # Create Line Chart for Rent Trends
    fig2 = px.line(df_move_in, x="Move-in", y=["Rent", "Market Rent"], 
                   title="📈 Rent Trends Over Time", markers=True,
                   labels={"value": "Amount ($)", "Move-in": "Move-in Date"},
                   line_shape="spline", color_discrete_sequence=["#FF5733", "#33FF57"])
    fig2.update_layout(width=1000, height=600)
    fig2.update_xaxes(title_text="Move-in Date", showgrid=True, gridcolor="lightgray", tickangle=-45)
    fig2.update_yaxes(title_text="Amount ($)", showgrid=True, gridcolor="lightgray")
    img_path2 = os.path.join(IMG_DIR, "move-in.png")
    fig2.write_image(img_path2)
    image_paths.append(img_path2)

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

    fig3 = px.bar(avg_lease_days_df, 
                 x="Sqft Group", 
                 y="Lease Days", 
                 title="📊 Avg Lease Days by Sqft Group",
                 labels={"Lease Days": "Avg Lease Duration (Days)", "Sqft Group": "Square Footage Range"},
                 color="Lease Days",
                 text_auto=True,
                 color_continuous_scale="Viridis")  # Gradient color

        # 🔹 Improve Layout & Style
    fig3.update_layout(
            width=1000, height=600,  # Bigger size
        )

        # 🔹 Customize X-Axis
    fig3.update_xaxes(
            title_text="Square Footage Range",
            tickangle=-45,  # Rotate x-axis labels for better visibility
            showgrid=True,
            gridcolor="lightgray"
        )

        # 🔹 Customize Y-Axis
    fig3.update_yaxes(
            title_text="Avg Lease Duration (Days)",
            gridcolor="lightgray"
        )
        
    img_path3 = os.path.join(IMG_DIR, "lease_date.png")
    fig3.write_image(img_path3)
    image_paths.append(img_path3)

    status_counts = dfs["Tenant Data"]["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
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

    img_path4 = os.path.join(IMG_DIR, "status.png")
    fig4.write_image(img_path4)
    image_paths.append(img_path4)
    status_counts = dfs["Work Orders"]["Work Order Type"].value_counts().reset_index()
    status_counts.columns = ["Work Order Type", "Count"]

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
    img_path5 = os.path.join(IMG_DIR, "work-order-type.png")
    fig5.write_image(img_path5)
    image_paths.append(img_path5)
    
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

    img_path6 = os.path.join(IMG_DIR, "order-issue.png")
    fig6.write_image(img_path6)
    image_paths.append(img_path6)
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

    fig7 = px.line(move_trends, 
                    x=move_trends.index, 
                    y=["Move In", "Move Out"],
                    markers=True,
                    title="📈 Move-In and Move-Out Trends by Month",
                    labels={"value": "Number of Vacancies", "index": "Month"},
                    line_shape="spline",  # Smooth curves
                    color_discrete_sequence=["#1f77b4", "#ff7f0e"])  # Custom colors (Blue & Orange)

        # 🔹 Improve Layout & Style
    fig7.update_layout(
            width=1000, height=600,  # Bigger figure size
            margin=dict(l=50, r=50, t=50, b=100),  # Adjust margins
            legend=dict(
                x=0.5, y=-0.2,  # Center legend below the chart
                orientation="h",
                xanchor="center",
                font=dict(size=14)
            )
        )

        # 🔹 Customize X-Axis
    fig7.update_xaxes(
            title_text="Month",
            tickangle=-45,  # Rotate x-axis labels
            showgrid=True,  # Show gridlines
            gridcolor="lightgray"
        )

        # 🔹 Customize Y-Axis
    fig7.update_yaxes(
            title_text="Number of Vacancies",
            showgrid=True,
            gridcolor="lightgray"
        )

    img_path7 = os.path.join(IMG_DIR, "move-in-out.png")
    fig7.write_image(img_path7)
    image_paths.append(img_path7)

    df1 = dfs["Vacancies"]  # Ensure you're using the correct dataset key

        # **Convert "Days Vacant" to Numeric**
    df1["Days Vacant"] = pd.to_numeric(df["Days Vacant"], errors="coerce")
    df1["Sqft"] = pd.to_numeric(df1["Sqft"], errors="coerce")

        # **Drop NaN values**
    df_filtered1 = df1.dropna(subset=["Sqft", "Days Vacant"])
    
    fig8 = px.scatter(df_filtered1, 
                 x="Sqft", 
                 y="Days Vacant",
                 title="📊 Relationship Between Square Footage and Days Vacant",
                 labels={"Sqft": "Square Footage", "Days Vacant": "Days Vacant"},
                 color="Days Vacant",  # Color based on vacancy duration
                 size="Days Vacant",  # Marker size based on days vacant
                 hover_data=["Sqft", "Days Vacant"],  # Display additional data on hover
                 color_continuous_scale="Viridis",  # Gradient color scheme
                 opacity=0.7,  # Reduce opacity for better visualization
                 size_max=15)  # Adjust marker size

        # 🔹 Improve Layout & Style
    fig8.update_layout(
            width=1000, height=600,  # Bigger size
            margin=dict(l=50, r=50, t=50, b=50)  # Adjust margins

        )

        # 🔹 Customize X-Axis
    fig8.update_xaxes(
            title_text="Square Footage",
            showgrid=True,  # Show gridlines
            gridcolor="lightgray"
        )

        # 🔹 Customize Y-Axis
    fig8.update_yaxes(
            title_text="Days Vacant",
            showgrid=True,
            gridcolor="lightgray"
        )

    img_path8 = os.path.join(IMG_DIR, "sqt.png")
    fig8.write_image(img_path8)
    image_paths.append(img_path8)


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

    img_path9 = os.path.join(IMG_DIR, "unit.png")
    fig9.write_image(img_path9)
    image_paths.append(img_path9)

    rent_ready_df = dfs["Vacancies"][dfs["Vacancies"]["Rent Ready"] == "Yes"]

        # Ensure "Available On" and "Next Move In" columns are in datetime format
    rent_ready_df["Available On"] = pd.to_datetime(rent_ready_df["Available On"], errors="coerce")
    rent_ready_df["Next Move In"] = pd.to_datetime(rent_ready_df["Next Move In"], errors="coerce")
        

        # Extract month and year from "Available On" and "Next Move In"
    rent_ready_df["Available On Month"] = rent_ready_df["Available On"].dt.to_period("M")
    rent_ready_df["Next Move In Month"] = rent_ready_df["Next Move In"].dt.to_period("M")

        # Count the number of available units for each month (Available On)
    available_on_month_counts = rent_ready_df["Available On Month"].value_counts().sort_index()

        # Count the number of units with a "Next Move In" for each month
    next_move_in_month_counts = rent_ready_df["Next Move In Month"].value_counts().sort_index()

        # Combine both counts into a DataFrame for easier plotting
    month_counts_df = pd.DataFrame({
            "Available On": available_on_month_counts,
            "Next Move In": next_move_in_month_counts
        }).fillna(0)  # Fill NaN values with 0

        # Plot the bar chart
    fig10 = px.bar(
            month_counts_df,
            x=month_counts_df.index.astype(str),  # Convert PeriodIndex to string for x-axis labels
            y=["Available On", "Next Move In"],
            title="📊 Available On and Next Move In by Month (Rent Ready Units)",
            labels={"value": "Count of Units", "index": "Month"},
            barmode="group",  # Display bars for each month side by side
            text_auto=True,  # Display text inside bars
            color_discrete_sequence=["#636EFA", "#EF553B"],  # Custom color palette for bars
        )

        # Update layout for better aesthetics
    fig10.update_layout(
            width=1000, height=600,  # Bigger size
            xaxis_title="Month",
            yaxis_title="Count of Units",
            xaxis=dict(
                tickangle=45,  # Angle the x-axis labels for better readability
                tickmode="array",  # Ensure that all months are displayed properly
            ),
            yaxis=dict(
                showgrid=True,  # Show gridlines for better readability
                gridcolor='lightgray',  # Light gridlines for better contrast
            ),
            margin=dict(t=50, b=80, l=50, r=50),  # Add space around the plot
            hovermode="x unified",  # Display hover information for all bars in the same month
            showlegend=True,  # Show legend for "Available On" and "Next Move In"
        )

        # Update bar text for better visibility
    fig10.update_traces(textposition="inside", texttemplate="%{text:.2s}", textfont_size=12)

        # Save the chart as an image
    img_path = os.path.join(IMG_DIR, "available_vs_next_move_in_improved_design.png")
    fig10.write_image(img_path)
    image_paths.append(img_path)

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
