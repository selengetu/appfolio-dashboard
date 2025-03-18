import plotly.express as px
import plotly.io as pio

# Set Orca as the image export engine
pio.orca.config.executable = "orca"

# Create a test chart
fig = px.bar(x=["A", "B", "C"], y=[1, 3, 2], title="Test Chart")

# Save as PNG using Orca
output_path = "test_chart_orca.png"
print(f"Saving chart to: {output_path}")

try:
    pio.write_image(fig, output_path, engine="orca")
    print("✅ Image saved successfully using Orca!")
except Exception as e:
    print(f"❌ Error saving image with Orca: {e}")
