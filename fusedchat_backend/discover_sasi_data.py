import requests
from bs4 import BeautifulSoup

def discover_pdfs(url):
    print(f"🔍 Scanning for documents at: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    links = soup.find_all('a', href=True)
    pdf_count = 0
    
    print("\n--- FOUND DOCUMENTS ---")
    for link in links:
        href = link['href']
        if href.endswith(".pdf"):
            # Clean the name for display
            display_name = link.text.strip() or href.split("/")[-1]
            print(f"📄 {display_name}")
            print(f"🔗 URL: {href}\n")
            pdf_count += 1
            
    print(f"Total PDFs found on this page: {pdf_count}")

if __name__ == "__main__":
    # Test it on the main CSE page
    discover_pdfs("https://sasi.ac.in/computer-science-engineering-and-allied-branches/")