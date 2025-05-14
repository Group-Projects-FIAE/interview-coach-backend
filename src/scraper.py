import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def scrape_for_job_description(url):
    try:
        html_content = fetch_html_with_selenium(url)
        soup = BeautifulSoup(html_content, 'lxml')
        if not check_for_valid_job_posting(soup):
            return ([{'error': "URL is unlikely to be a job posting."}, None])
        json_data = extract_json_ld(soup)
        # Return structured data if available
        if json_data:
            job_title = json_data.get('title')
            job_description = json_data.get('description')
        # Fallback to scraping
        else:
            job_title, job_description = extract_job_data_from_html(soup)
        return [job_title, job_description]
    except Exception as e:
        return [{'error': str(e)}, None]

def fetch_html_with_selenium(url):
    options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html    

def check_for_valid_job_posting(soup):
    if not has_job_keywords(soup):
        return False
    return True

def has_job_keywords(soup):
    job_keywords = ["job", "beruf", "stelle",
                    "company", "firma", "unternehmen",
                    "apply now", "apply here", "bewerben", "bewerbung",
                    "salary", "gehalt", "lohn",
                    "job responsibilities", "requirements", "anforderungen"]
    text = soup.get_text(separator=' ').lower()
    return any(keyword in text for keyword in job_keywords)

def extract_json_ld(soup):
    json_ld_script = soup.find('script', type='application/ld+json')
    if json_ld_script:
        data = json.loads(json_ld_script.string)
        return data
    return None

def extract_job_data_from_html(soup):
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
