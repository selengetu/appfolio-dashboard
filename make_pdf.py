from fpdf import FPDF
import os
import json

# Define image paths for the first page
image_paths_page1 = [
    "plotly_pdf_images/move-in.png",
    "plotly_pdf_images/tenant_status.png",   
    "plotly_pdf_images/lease_date.png", 
    "plotly_pdf_images/status.png",  
]

# Define image paths for the second page
image_paths_page2 = [
    "plotly_pdf_images/move-in-out.png",  
    "plotly_pdf_images/sqt.png",  
    "plotly_pdf_images/unit.png",
    "plotly_pdf_images/available_vs_next_move_in_improved_design.png",
]
image_paths_page3 = [
    "plotly_pdf_images/work-order-type.png",  
    "plotly_pdf_images/order-issue.png" 
]

# Load metrics from the JSON file
json_file = "metrics.json"
with open(json_file, "r") as f:
    metrics_data = json.load(f)

# Extract metrics
metrics1 = [(m["label"], m["value"]) for m in metrics_data["metrics1"]]
metrics2 = [(m["label"], m["value"]) for m in metrics_data["metrics2"]]
metrics3 = [(m["label"], m["value"]) for m in metrics_data["metrics3"]]

# Create PDF with FPDF in Landscape Mode
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)  # Title font
        self.ln(1)  # Adjusted spacing for better alignment

pdf = PDF(orientation="L", unit="mm", format="A4")  #  Landscape Mode
pdf.set_auto_page_break(auto=True, margin=15)

### ** First Page: Business Dashboard Report**
pdf.add_page()

#  Add Metrics for First Page
pdf.set_font("Arial", "B", 12)
pdf.cell(280, 8, "Tenant Analysis", ln=True, align="C")  # Second page title
x_positions_first_page = [10, 85, 160, 235]  # Adjusted positions
y_position_metrics1 = 18  # Consistent Y position

for i, (label, value) in enumerate(metrics1):
    pdf.set_xy(x_positions_first_page[i], y_position_metrics1)  # Position
    pdf.cell(50, 6, label, ln=True)  
    pdf.set_font("Arial", "", 10)  # Bold value
    pdf.set_xy(x_positions_first_page[i], y_position_metrics1 + 5)
    pdf.cell(50, 6, value, ln=True)  
    pdf.set_font("Arial", "B", 9)  # Reset font

pdf.ln(8)  # Less space before graphs

# Image size (Landscape A4 = 297mm wide)
img_width = 140  
img_height = 85  

# Arrange images in a 2x2 grid (First Page)
x_positions = [10, 155]  
y_positions = [35, 120]  # Adjusted to avoid overlapping

for i, img in enumerate(image_paths_page1):
    col = i % 2  
    row = i // 2  
    pdf.image(img, x=x_positions[col], y=y_positions[row], w=img_width, h=img_height)

### ** Second Page: Vacant Analysis**
pdf.add_page()
pdf.set_font("Arial", "B", 12)
pdf.cell(280, 8, "Vacant Analysis", ln=True, align="C")  # Second page title
pdf.ln(1)

#  Add Metrics for Second Page
pdf.set_font("Arial", "B", 9)  # Smaller font
x_positions_second_page = [10, 85, 160, 235]  # Adjusted positions for page 2
y_position_metrics2 = 18  # Adjusted Y position for second-page metrics

for i, (label, value) in enumerate(metrics2):
    pdf.set_xy(x_positions_second_page[i], y_position_metrics2)  
    pdf.cell(50, 6, label, ln=True)  
    pdf.set_font("Arial", "", 10)  
    pdf.set_xy(x_positions_second_page[i], y_position_metrics2 + 5)
    pdf.cell(50, 6, value, ln=True)  
    pdf.set_font("Arial", "B", 9)  

pdf.ln(8)  # Less space before graphs

#  Arrange images in a 2x2 grid (Second Page)
for i, img in enumerate(image_paths_page2):
    col = i % 2  
    row = i // 2  
    pdf.image(img, x=x_positions[col], y=y_positions[row], w=img_width, h=img_height)

### ** Third Page: Vacant Analysis**
pdf.add_page()
pdf.set_font("Arial", "B", 12)
pdf.cell(280, 8, "Work order Analysis", ln=True, align="C")  # Second page title
pdf.ln(1)

#  Add Metrics for Second Page
pdf.set_font("Arial", "B", 9)  # Smaller font
x_positions_third_page = [10, 85, 160, 235]  # Adjusted positions for page 2
y_position_metrics3 = 18  # Adjusted Y position for second-page metrics

for i, (label, value) in enumerate(metrics3):
    pdf.set_xy(x_positions_third_page[i], y_position_metrics3)  
    pdf.cell(50, 6, label, ln=True)  
    pdf.set_font("Arial", "", 10)  
    pdf.set_xy(x_positions_third_page[i], y_position_metrics3 + 5)
    pdf.cell(50, 6, value, ln=True)  
    pdf.set_font("Arial", "B", 9)  

pdf.ln(8)  # Less space before graphs

# Arrange images in a 2x2 grid (Second Page)
for i, img in enumerate(image_paths_page3):
    col = i % 2  
    row = i // 2  
    pdf.image(img, x=x_positions[col], y=y_positions[row], w=img_width, h=img_height)

#  Save PDF
pdf_file = "appfolio_dashboard.pdf"
pdf.output(pdf_file)

print(f"PDF generated successfully with two pages: {pdf_file}")
