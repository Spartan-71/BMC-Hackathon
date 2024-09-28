import pdfplumber

def extract_headings_from_index(pdf_path, start_page=2, end_page=9):
    headings = []
    
    # Open the PDF file
    with pdfplumber.open(pdf_path) as pdf:
        # Loop through the specified range of pages
        for page_num in range(start_page, end_page + 1):  # pages are 0-indexed
            if page_num < len(pdf.pages):  # Check if page exists
                page = pdf.pages[page_num]
                text = page.extract_text()
                
                if text:
                    lines = text.split('\n')  # Split the text into lines
                    for line in lines:
                        line = line.strip()  # Clean up whitespace
                        
                        # Check for keywords or patterns that indicate headings
                        if line and ("Table of Contents" in line or "Index" in line or "Section" in line):
                            headings.append(line)  # Append the heading line

    return headings

# Test the function
if __name__ == "__main__":
    pdf_file_path = "CIS_Ubuntu_Linux_24.04_LTS.pdf"  # Change to your PDF path
    headings = extract_headings_from_index(pdf_file_path, start_page=2, end_page=4)
    
    # Print the extracted headings
    print("Extracted Headings:")
    for heading in headings:
        print(heading)
