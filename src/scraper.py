import re
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def scrape_for_job_description(url):
    try:
        html_content = fetch_html_with_selenium(url)
        json_data = extract_json_ld(html_content)
        description_to_return = ""
        # Return structured data if available
        if json_data:
            job_title = json_data.get('title')
            job_description = json_data.get('description')
        # Fallback to scraping
        else:
            job_title, job_description = extract_job_data_from_html(html_content)
        #description_to_return += "Job Title:\n" + job_title + "\n"
        #description_to_return += "Job Description:\n" + job_description
        return job_title, job_description
    except Exception as e:
        return {'error': str(e)}
    

def fetch_html_with_selenium(url):
    options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html    

def extract_json_ld(html):
    soup = BeautifulSoup(html, 'lxml')
    json_ld_script = soup.find('script', type='application/ld+json')
    if json_ld_script:
        data = json.loads(json_ld_script.string)
        print (data)
        return data
    return None

def extract_job_data_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    # print (soup)
    job_title = ""
    job_description = ""

    # Job title
    title = soup.find('meta', property="og:title")
    if title:
        job_title += title["content"]
        
    # Job description, short
    short_description = soup.find('meta', property="og:description")
    if short_description:
        short_description_string = re.sub(r'<.*?>', '', short_description["content"])
    # Job description, long
    long_description = soup.find('div', itemprop="description")
    if long_description:
        long_description_string = long_description.get_text(strip=True)

    # if both descriptions exist and short is not part of long, then use both
    if (short_description_string and long_description_string) and (short_description_string not in long_description_string):
        job_description += f"Short: {short_description_string}\n" 
        job_description += f"Long: {long_description_string}\n"
    # otherwise use long (if available)
    elif long_description_string:
        job_description += f"{long_description_string}\n"
    # if long is not available, look for short description
    elif short_description_string:
        job_description += f"{short_description_string}\n"
    # if neither exist, do nothing


    # fill with 'None' if still empty
    if (job_title == ""):
        job_title += "None"
    if (job_description == ""):
        job_description += "None"
    return job_title, job_description
