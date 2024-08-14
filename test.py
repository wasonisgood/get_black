import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import re

# 多个User-Agent列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
]

def get_driver():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 暫時關閉無頭模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    return driver

def solve_cloudflare_challenge(driver):
    try:
        # 等待Cloudflare JS挑战页面加载
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'cf-challenge-form')))
        # 等待JS挑战完成
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.challenge-body-text')))
        print("Cloudflare challenge passed.")
    except Exception as e:
        print(f"Error solving Cloudflare challenge: {e}")

def get_total_pages(keyword, driver):
    url = f'https://www.chinatimes.com/search/{keyword}?chdtv'
    print(f"Requesting URL: {url}")
    
    try:
        driver.get(url)
        solve_cloudflare_challenge(driver)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'search-result-count')))
        total_results_elem = driver.find_element(By.CLASS_NAME, 'search-result-count')
        total_results = int(total_results_elem.text.replace(',', ''))
        total_pages = (total_results // 20) + 1 if total_results % 20 != 0 else total_results // 20
        return total_pages
    except Exception as e:
        print(f"Error retrieving search results for keyword {keyword}: {e}")
        return 0

def get_news_titles(keyword, total_pages, driver):
    titles = []
    urls = []
    for page in range(1, total_pages + 1):
        url = f'https://www.chinatimes.com/search/{keyword}?page={page}&chdtv'
        print(f"Requesting URL: {url}")
        
        try:
            driver.get(url)
            solve_cloudflare_challenge(driver)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'title')))
            
            # 模擬人類行為：隨機滾動
            for _ in range(random.randint(1, 3)):
                driver.execute_script(f"window.scrollTo(0, {random.randint(300, 700)});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # 隨機點擊頁面上的某些元素（例如廣告）
            try:
                ads = driver.find_elements(By.CSS_SELECTOR, 'div.ad-container')
                if ads:
                    ad = random.choice(ads)
                    driver.execute_script("arguments[0].click();", ad)
                    time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"Error clicking ads for page {page} of keyword {keyword}: {e}")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            news_items = soup.find_all('h3', class_='title')
            
            for item in news_items:
                title = item.get_text(strip=True)
                link = item.find('a')['href']
                titles.append(title)
                urls.append(link)
            
            # 添加更長的隨機延遲
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"Error retrieving page {page} for keyword {keyword}: {e}")
            continue
    
    return titles, urls

def get_top_words(titles, top_n=5):
    text = ' '.join(titles)
    words = re.findall(r'\b\w+\b', text)
    counter = Counter(words)
    most_common_words = counter.most_common(top_n)
    return most_common_words

def generate_html(results, top_words):
    html = ""
    for person, data in results.items():
        df = pd.DataFrame({'Title': data['titles'], 'URL': data['urls']})
        html += f"<h1>News Titles for {person}</h1>"
        html += df.to_html(index=False, escape=False)

    top_words_html = '<ul>'
    for word, count in top_words:
        top_words_html += f'<li>{word}: {count}</li>'
    top_words_html += '</ul>'

    full_html = f"""
    <html>
    <head>
    <title>News Titles and Top Words</title>
    </head>
    <body>
    {html}
    <h2>Top {len(top_words)} Words</h2>
    {top_words_html}
    </body>
    </html>
    """

    with open('news_titles.html', 'w', encoding='utf-8') as f:
        f.write(full_html)

def main(keywords):
    results = {}
    all_titles = []
    
    for keyword in keywords:
        print(f"Searching for {keyword}...")
        driver = get_driver()
        try:
            total_pages = get_total_pages(keyword, driver)
            if total_pages == 0:
                print(f"No results found for {keyword}")
                continue
            titles, urls = get_news_titles(keyword, total_pages, driver)
            if not titles:
                print(f"No news titles found for {keyword}")
                continue
            results[keyword] = {'titles': titles, 'urls': urls}
            all_titles.extend(titles)
        finally:
            driver.quit()
        
        # 添加關鍵詞之間的隨機延遲
        time.sleep(random.uniform(10, 20))
    
    if all_titles:
        top_words = get_top_words(all_titles)
        generate_html(results, top_words)
    else:
        print("No titles were found for any of the keywords.")

if __name__ == "__main__":
    keywords = ['周弘憲', '許舒翔', '邱文彥', '鄧家基', '王秀紅', '呂秋慧', '柯麗鈴', '黃東益', '伊萬．納威']
    main(keywords)
