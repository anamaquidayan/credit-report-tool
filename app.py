import streamlit as st
import os
import pdfplumber
import re
import pandas as pd
import tempfile

# -----------------------------------------------------------------
# 1. YOUR CORE FUNCTIONS (Copied directly from your notebook)
# -----------------------------------------------------------------

# Set up the uploads directory (though we'll use temp files)
UPLOADS_DIR = 'pdf_uploads'
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# FUNCTION 1: PDF DATA EXTRACTOR (Your Version 6)
def extract_data_from_pdf(pdf_path):
    """
    Opens a PDF, extracts all text, and searches for specific,
    flexible patterns.
    """
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1) 
                if page_text:
                    full_text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return {} # Return empty dict on error

    
    # This helper function will try a list of patterns and return the first match
    def find_first_match(patterns_list, text):
        for pattern in patterns_list:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip() # Return the first captured group
        return 'Not Found'

    # --- DEFINE ALL PATTERNS TO TRY ---
    name_patterns = [
        r"INPUT:\s+(.*),\s+[MU],\s+[\d\-A-Z]+,\s+(?:MALE|FEMALE|UNKNOWN)"
    ]
    dob_patterns = [
        r"INPUT:.*?, [MU], ([\d\-A-Z]+), (?:MALE|FEMALE|UNKNOWN)"
    ]
    id_patterns = [
        r"INPUT:.*?(?:PHL|PHILLIPINES)\s*,\s*([A-Z0-9]+)\s*,\s*(?:PRC|DL|[A-Z]{2,3})"
    ]
    segment_patterns = [
        r"SEGMENT:\s*([\d]+)"
    ]
    score_patterns = [
        r"(?:SCORE:\s+|\"SCORE:\s*\",\s*\")(\d+)\"?"
    ]

    # --- RUN THE EXTRACTION ---
    extracted_data = {}
    extracted_data['Name'] = find_first_match(name_patterns, full_text)
    extracted_data['Date of Birth'] = find_first_match(dob_patterns, full_text)
    extracted_data['Primary ID'] = find_first_match(id_patterns, full_text)
    extracted_data['Segment'] = find_first_match(segment_patterns, full_text)
    extracted_data['Credit Score'] = find_first_match(score_patterns, full_text)
            
    return extracted_data

# FUNCTION 2: CSV SAVING
def save_to_csv(data_list, filename="credit_report_data.csv"):
    """
    Appends a list of extracted data dictionaries to a CSV file.
    """
    if not data_list:
        print("No new data to save.")
        return False
        
    df = pd.DataFrame(data_list)
    file_exists = os.path.exists(filename)
    
    df.to_csv(
        filename, 
        mode='a',
        header=not file_exists,
        index=False
    )
    return True

# -----------------------------------------------------------------
# 2. YOUR NEW STREAMLIT WEB INTERFACE
# -----------------------------------------------------------------

st.title("?? Credit Report Extractor")
st.write("Upload one or more PDF credit reports to extract data and save to a CSV.")

# Replaces ipywidgets.FileUpload
uploaded_files = st.file_uploader(
    "Choose PDF files", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    all_new_data = []
    
    # Show a progress bar
    progress_bar = st.progress(0, text="Starting...")
    
    for i, uploaded_file in enumerate(uploaded_files):
        
        # Streamlit reads files in-memory. We need to save it to a
        # temporary file so pdfplumber can open it by its path.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name

        file_name = uploaded_file.name
        st.write(f"Processing: {file_name}...")
        
        # Run your extraction function on the temp file
        data = extract_data_from_pdf(temp_file_path)
        
        if data:
            data['Filename'] = file_name
            all_new_data.append(data)
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        # Update progress bar
        progress_bar.progress((i + 1) / len(uploaded_files), text=f"Processed: {file_name}")

    if all_new_data:
        st.success("? All files processed successfully!")
        
        # Save the data to CSV
        save_to_csv(all_new_data, "credit_report_data.csv")
        
        # Display the extracted data in a table
        st.subheader("Extracted Data")
        display_df = pd.DataFrame(all_new_data)
        st.dataframe(display_df)
        
        # Add a button to download the CSV
        with open("credit_report_data.csv", "rb") as f:
            st.download_button(
                label="Download Running CSV File",
                data=f,
                file_name="credit_report_data.csv",
                mime="text/csv",
            )
            
    else:
        st.error("No data was extracted. Check your PDF files or regex patterns.")
