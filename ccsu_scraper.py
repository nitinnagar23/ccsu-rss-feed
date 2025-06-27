import requests
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime, timezone
import time
import re

def scrape_ccsu_news_and_generate_rss(base_url, num_pages=3, output_filename="ccsu_news_feed.xml"):
    all_items_data = []
    
    print(f"Starting to scrape from {base_url}...")

    for page_num in range(1, num_pages + 1):
        url = f"{base_url}&page={page_num}"
        print(f"Fetching page: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status() 
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        news_table = soup.find('table', class_='table')
        
        if not news_table:
            print(f"No news table found on page {page_num}. Ending scrape.")
            break
            
        rows = news_table.find_all('tr')
        if len(rows) <= 1 and page_num > 1: 
            print(f"No more news items found on page {page_num}. Ending pagination.")
            break
            
        for row in rows:
            if row.find('th'):
                continue

            cols = row.find_all('td')
            
            if len(cols) >= 3:
                date_str = cols[1].get_text(strip=True)
                title_link_tag = cols[2].find('a')
                
                if title_link_tag:
                    title = title_link_tag.get_text(strip=True)
                    link = requests.compat.urljoin(base_url, title_link_tag['href'])
                    description = title 

                    try:
                        pub_date = datetime.strptime(date_str, '%d-%m-%Y')
                        pub_date_str = pub_date.astimezone(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
                    except ValueError:
                        pub_date_str = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
                        print(f"Warning: Could not parse date '{date_str}'. Using current time for '{title}'.")

                    item_data = {
                        'title': title,
                        'link': link,
                        'description': description,
                        'pubDate': pub_date_str,
                        'guid': link
                    }
                    all_items_data.append(item_data)
                else:
                    pass # Skip items without a clear title/link
            
        time.sleep(1) 

    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    SubElement(channel, 'title').text = "CCS University Latest News"
    SubElement(channel, 'link').text = base_url.split('&page=')[0]
    SubElement(channel, 'description').text = f"Latest news and updates from CCS University, scraped from {base_url.split('&page=')[0]}"
    SubElement(channel, 'language').text = "en-in"
    SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    SubElement(channel, 'generator').text = "Custom Python Scraper"

    for item_data in all_items_data:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = item_data['title']
        SubElement(item, 'link').text = item_data['link']
        SubElement(item, 'description').text = item_data['description']
        SubElement(item, 'pubDate').text = item_data['pubDate']
        SubElement(item, 'guid', isPermaLink='true').text = item_data['guid']

    pretty_xml = minidom.parseString(tostring(rss, encoding='utf-8')).toprettyxml(indent="  ")

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"\nRSS feed successfully generated to {output_filename}")
    print(f"Total items scraped: {len(all_items_data)}")

if __name__ == "__main__":
    TARGET_BASE_URL = "https://www.ccsuniversity.ac.in/search-news?title=&category=&month=&year=" 
    NUMBER_OF_PAGES_TO_SCRAPE = 2 # Adjust this number as needed
    OUTPUT_FILE = "ccsu_news_feed.xml"

    scrape_ccsu_news_and_generate_rss(TARGET_BASE_URL, NUMBER_OF_PAGES_TO_SCRAPE, OUTPUT_FILE)
  
