import csv
import requests
from bs4 import BeautifulSoup
import json
import openai
import os

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to extract all URLs from a sitemap
def extract_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        return urls
    except Exception as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return None

# Function to scrape text content from a webpage
def scrape_page_content(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text from the page
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Function to process text data with OpenAI LLM
def extract_contact_info_with_llm(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract contact information (emails, phone numbers, and contact person names) from the following text. Return the results in JSON format."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error processing text with OpenAI: {e}")
        return None

# Read the input CSV file
# input_csv = 'websites.csv'
# output_json = 'contact_info.json'

# # Read the list of websites
# websites = []
# with open(input_csv, mode='r', encoding='utf-8') as file:
#     reader = csv.reader(file)
#     next(reader)  # Skip header
#     for row in reader:
#         websites.append(row[5])  # Assuming URLs are in the first column

# # Scrape sitemaps, collect text data, and process with OpenAI
# contact_info = []

# for website in websites:
#     print(f"Processing {website}...")

#     # Step 1: Fetch the sitemap
#     sitemap_url = f"{website}/sitemap.xml" if not website.endswith('sitemap.xml') else website
#     urls = extract_urls_from_sitemap(sitemap_url)
#     if not urls:
#         continue

#     # Step 2: Scrape all pages and collect text data
#     all_text = ""
#     for url in urls:
#         print(f"Scraping {url}...")
#         text = scrape_page_content(url)
#         if text:
#             all_text += text + " "

#     # Step 3: Process text data with OpenAI LLM
#     if all_text:
#         print("Extracting contact information with OpenAI...")
#         contact_info_json = extract_contact_info_with_llm(all_text)
#         if contact_info_json:
#             try:
#                 contact_info.append(json.loads(contact_info_json))
#             except json.JSONDecodeError:
#                 print("Failed to parse OpenAI response as JSON.")
#         else:
#             print("No contact information extracted.")
#     else:
#         print("No text data collected.")

# # Step 4: Save the results to a JSON file
# with open(output_json, mode='w', encoding='utf-8') as file:
#     json.dump(contact_info, file, indent=4)

# print(f"Contact information saved to {output_json}")

url = "https://aschauffage.com/"
sites = extract_urls_from_sitemap(url)
print(sites)