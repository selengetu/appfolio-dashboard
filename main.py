import subprocess
import time

# Define the scripts to run in order
scripts = [
    'python appfolio_data.py',
    'python make_img.py',
    'python make_pdf.py',
]

# Run each script sequentially
for script in scripts:
    subprocess.run(script, shell=True)
    time.sleep(2)

# Optional: Sleep for 3 seconds before running the next command
time.sleep(5)

# Run Streamlit app
subprocess.run('streamlit run streamlit.py', shell=True)
