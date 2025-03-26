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
        description_to_return += "Job Title:\n" + job_title + "\n"
        description_to_return += "Job Description:\n" + job_description
        return description_to_return
    except Exception as e:
        return {'error': str(e)}
    

def fetch_html_with_selenium(url):
    options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)

    driver.get(url)    
    time.sleep(5)
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

#TODO: explore fallback option with learn4good.com as example, getting more detailed return values
def extract_job_data_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    # print (soup.prettify())
    job_title = ""
    job_description = ""

    # Job title
    title = soup.find('meta', property="og:title")
    if title:
        job_title += title.get_text(strip=True)
    # Job short description
    short_description = soup.find('meta', property="og:description")
    if short_description:
        job_description += 'Short: ' + short_description["content"] + '\n'
    
    # Responsibilities
    responsibilities_section = soup.find('section', {'id': 'responsibilities'})
    if responsibilities_section:
        job_description += 'Responsibilities: ' + responsibilities_section.get_text(strip=True) + '\n'

    # Qualifications
    qualifications_section = soup.find('section', {'id': 'qualifications'})
    if qualifications_section:
        job_description += 'Qualifications: ' + qualifications_section.get_text(strip=True) + '\n'

    # Location
    location = soup.find('span', class_='location')
    if location:
        job_description += 'Location: ' + location.get_text(strip=True) + '\n'

    # Company (if available)
    company = soup.find('a', class_='company-name')
    if company:
        job_description += 'Company: ' + company.get_text(strip=True) + '\n'

    # fill with 'None' if still empty
    if (job_title == ""):
        job_title += "None"
    if (job_description == ""):
        job_description += "None"
    return job_title, job_description
