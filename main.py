import subprocess
import time

# Define the scripts to run
scripts = [
    'python appfolio_data.py',
    'streamlit run streamlit.py',  # This must be run in the background
    'python make_pdf.py',
]

# Run first script normally
subprocess.run(scripts[0], shell=True)
time.sleep(2)  # Give some time before next execution

# Run Streamlit as a background process
streamlit_process = subprocess.Popen(scripts[1], shell=True)  # Keeps running in background

# Allow some time for Streamlit to initialize
time.sleep(5)

# Run PDF generation script
subprocess.run(scripts[2], shell=True)
