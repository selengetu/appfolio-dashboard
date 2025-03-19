import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

BASE_DIR = os.path.join(os.getcwd(), "data")
FILES = {
    "Tenant Data": os.path.join(BASE_DIR, "rent_roll-20250317.csv"),
    "Work Orders": os.path.join(BASE_DIR, "work_order-20250317.csv"),
    "Vacancies": os.path.join(BASE_DIR, "unit_vacancy_detail-20250318.csv"),
}
dfs = {}
for name, path in FILES.items():
    if os.path.exists(path):
        dfs[name] = pd.read_csv(path)

current_units = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Current"].shape[0]
vacant_units = dfs["Tenant Data"][dfs["Tenant Data"]["Status"] == "Vacant-Rented"].shape[0]
all_units = dfs["Tenant Data"].shape[0]
occupied = (current_units / all_units) * 100

dfs["Tenant Data"]["Rent"] = dfs["Tenant Data"]["Rent"].replace(r"[\$,]", "", regex=True)
dfs["Tenant Data"]["Rent"] = pd.to_numeric(dfs["Tenant Data"]["Rent"], errors="coerce")
dfs["Tenant Data"]["Market Rent"] = dfs["Tenant Data"]["Market Rent"].replace(r"[\$,]", "", regex=True)
dfs["Tenant Data"]["Market Rent"] = pd.to_numeric(dfs["Tenant Data"]["Market Rent"], errors="coerce")

total_rent = dfs["Tenant Data"]["Rent"].sum()
market_total_rent = dfs["Tenant Data"]["Market Rent"].sum()
total_move_out = dfs["Tenant Data"]["Move-out"].notnull().sum()
df_filtered = dfs["Tenant Data"].dropna(subset=["Tenant", "Late Count"]).copy()

df_filtered["Late Count"] = pd.to_numeric(df_filtered["Late Count"], errors="coerce")
df_filtered = df_filtered[df_filtered["Late Count"] > 2]
df_filtered = df_filtered.sort_values(by="Late Count", ascending=False)

fig = px.bar(
    df_filtered,
    x="Tenant",
    y="Late Count",
    title="📊 Late Payment Frequency by Tenant",
    labels={"Late Count": "Late Payment Count", "Tenant": "Tenant Name"},
    color="Late Count",
    text_auto=True,
)

# Download the figure as PNG
pio.write_image(fig, "late_payment_chart.png")

# You can also use other formats:
# pio.write_image(fig, "late_payment_chart.jpeg")
# pio.write_image(fig, "late_payment_chart.svg")
# pio.write_image(fig, "late_payment_chart.pdf")

fig.show()