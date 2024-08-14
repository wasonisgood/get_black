import time
from gnews import GNews
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import re
from tqdm import tqdm
import concurrent.futures

def get_gnews_articles(keyword):
    google_news = GNews(language='zh-Hant', country='TW')
    news = google_news.get_news(keyword)
    titles = [item['title'] for item in news]
    urls = [item['url'] for item in news]
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

def fetch_news_for_keyword(keyword):
    print(f"Searching for {keyword}...")
    try:
        titles, urls = get_gnews_articles(keyword)
        if not titles:
            print(f"No news titles found for {keyword}")
            return keyword, {'titles': [], 'urls': []}
        return keyword, {'titles': titles, 'urls': urls}
    except Exception as e:
        print(f"Error retrieving news for keyword {keyword}: {e}")
        return keyword, {'titles': [], 'urls': []}

def main(keywords):
    results = {}
    all_titles = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_keyword = {executor.submit(fetch_news_for_keyword, keyword): keyword for keyword in keywords}
        for future in tqdm(concurrent.futures.as_completed(future_to_keyword), total=len(keywords), desc="Processing keywords"):
            keyword, data = future.result()
            if data['titles']:
                results[keyword] = data
                all_titles.extend(data['titles'])

    if all_titles:
        top_words = get_top_words(all_titles)
        generate_html(results, top_words)
    else:
        print("No titles were found for any of the keywords.")

if __name__ == "__main__":
    keywords = ['周弘憲', '許舒翔', '邱文彥', '鄧家基', '王秀紅', '呂秋慧', '柯麗鈴', '黃東益', '伊萬．納威']
    main(keywords)
