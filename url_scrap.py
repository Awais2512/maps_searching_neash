import csv
import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
from urllib.parse import urljoin
from time import sleep
load_dotenv()
# OpenAI API key
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Function to extract all URLs from a sitemap
def extract_urls_from_sitemap(base_url):
    sitemap_candidates = [
        urljoin(base_url, 'sitemap.xml'),
        urljoin(base_url, 'pages-sitemap.xml')
    ]
    
    def parse_sitemap(sitemap_url):
        try:
            print("Trying for the sitemap:",sitemap_url)
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml-xml')
                
                # Check if it's a sitemap index file
                if soup.find('sitemapindex'):
                    nested_sitemaps = [loc.text.strip() for loc in soup.find_all('loc')]
                    all_urls = []
                    for nested in nested_sitemaps:
                        all_urls.extend(parse_sitemap(nested) or [])
                    return all_urls
                
                # Regular sitemap with URLs
                urls = [loc.text.strip() for loc in soup.find_all('loc')]
                return urls if urls else None
                
        except Exception as e:
            print(f"Error parsing {sitemap_url}: {str(e)}")
            return None

    # Check all sitemap candidates
    for candidate in sitemap_candidates:
        urls = parse_sitemap(candidate)
        if urls:
            return (urls, True)

    # Fallback to contact page check (existing code)
    contact_urls_to_try = [
        urljoin(base_url, 'contact'),
        urljoin(base_url, 'contact-us'),
        urljoin(base_url, 'contact.html')
    ]
    
    for contact_url in contact_urls_to_try:
        try:
            response = requests.head(contact_url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                return ([contact_url], False)
        except Exception as e:
            continue

    return ([], False)

# Function to scrape text content from a webpage
# Modified scrape_page_content function
def scrape_page_content(url):
    try:
        print("Scraping the URL:", url)
        
        # Skip known binary file extensions
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']):
            print(f"Skipping binary file: {url}")
            return None

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Check content type before parsing
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f"Skipping non-HTML content: {content_type}")
            return None

        # Handle encoding properly
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript', 'meta', 'link']):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)
        return text if text else None

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
# Function to process text data with OpenAI LLM
def extract_contact_info_with_llm(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Extract contact information from text. Return JSON format with:
{
    "emails": [""],
    "phones": [""],
    "contact_persons": [""],
    "other_info": {}
}

Example:
{
    "emails": ["sales@example.com", "support@company.com"],
    "phones": ["+1-555-123-4567", "(888) 987-6543"],
    "contact_persons": ["John Doe", "Sarah Smith"],
    "other_info": {
        "address": "123 Main St, City, State",
        "social_media": {
            "linkedin": "https://linkedin.com/company/example",
            "facebook": "https://facebook.com/exampleco"
        }
    }
}
Return only these fields. If no information found for a category, return empty array/object."""},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing text with OpenAI: {e}")
        return None
    
def filter_contact_urls(urls):
    contact_keywords = ["contact", "about", "support", "help", "team", "connect"]
    filtered_urls = [url for url in urls if any(keyword in url.lower() for keyword in contact_keywords)]
    return filtered_urls


def process_website(web_link):
    result = {
        'sitemap_found': False,
        'contact_page_url': None,
        'llm_contacts': {}
    }
    
    try:
        # Get URLs from sitemap or contact page
        urls, sitemap_found = extract_urls_from_sitemap(web_link)
        result['sitemap_found'] = sitemap_found
        
        # Filter contact-related URLs
        filtered_urls = filter_contact_urls(urls)
        print(f"Total Urls fetched: {len(filtered_urls)} \n FOr Weblink: {web_link}")
        # Scrape content from filtered URLs
        all_text = ""
        for url in filtered_urls:
            text = scrape_page_content(url)
            if text:
                all_text += text + "\n "
            sleep(1)  # Add delay between requests

        # If contact page found but no sitemap
        if not sitemap_found and len(urls) == 1:
            result['contact_page_url'] = urls[0]

        # Process text with LLM
        if all_text:
            contact_info = extract_contact_info_with_llm(all_text)
            if contact_info:
                try:
                    contact_info = json.loads(contact_info)
                    print("LLM collected info:\n",contact_info)
                    result['llm_contacts'] = contact_info
                except json.JSONDecodeError:
                    print("Json Response unable to LOAD")
    except Exception as e:
        print(f"Error processing {web_link}: {e}") 
    return result

def process_csv(input_file, output_file):
    # First get fieldnames by reading one row
    with open(input_file, 'r', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames + [
            'SitemapExists',
            'ContactPageURL',
            'Emails',
            'Phones',
            'ContactPersons',
            'OtherInfo'
        ]    
        for row in reader:
            try:
                web_link = row['Web Link'].strip()
                if not web_link.startswith(('http://', 'https://')):
                    print(f"Skipping invalid URL: {web_link}")
                    continue

                print(f"\nProcessing: {web_link}")
                processed = process_website(web_link)
                
                # Build output row
                output_row = {
                    **row,
                    'SitemapExists': processed['sitemap_found'],
                    'ContactPageURL': processed['contact_page_url'] or '',
                    'Emails': ', '.join(processed.get('emails', [])),
                    'Phones': ', '.join(processed.get('phones', [])),
                    'ContactPersons': ', '.join(processed['llm_contacts'].get('contact_persons', [])),
                    'OtherInfo': json.dumps(processed['llm_contacts'].get('other_info', {}))
                }
                print("*"*100)
                print("Output Response Row:\n ",output_row)
                input("enter to move further")
                
                # Write to file immediately after processing
                file_exists = os.path.isfile(output_file)
                with open(output_file, 'a', newline='', encoding='utf-8') as fout:
                    writer = csv.DictWriter(fout, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(output_row)
                
                print(f"Completed: {web_link}")
                sleep(2)

            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue

process_csv("csv_files/input.csv",'output.csv')