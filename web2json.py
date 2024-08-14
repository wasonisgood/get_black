import re
import json
from bs4 import BeautifulSoup
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# 你可能需要运行以下命令来下载nltk数据包
# nltk.download('punkt')
# nltk.download('stopwords')

# 设置停用词和无用词，包括台湾主要媒体
taiwan_media = {"自由時報", "聯合新聞網", "Yahoo奇摩新聞", "鏡新聞", "風傳媒", "三立新聞網", "中華新聞雲", "民視新聞網", "ETtoday新聞雲", "鏡週刊", "Yahoo奇摩股市", "政大校訊"}
stop_words = set(stopwords.words('chinese')) | taiwan_media | {"報社", "名稱", "人民", "作者", "記者", "新聞", "網"}

# 提取重要词语的函数
def extract_top_words(text):
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words and re.match(r'\w+', word)]
    word_freq = Counter(words)
    return [word for word, _ in word_freq.most_common(10)]

# 解析HTML文件并转换为JSON
def parse_html_to_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}

    sections = soup.find_all('h1')
    for section in sections:
        person_name = section.get_text().replace('News Titles for ', '').strip()
        table = section.find_next_sibling('table')
        rows = table.find_all('tr')[1:]  # 跳过标题行

        # 将人的名字添加到停用词中
        dynamic_stop_words = stop_words | {person_name}

        news_list = []
        for row in rows:
            cols = row.find_all('td')
            title = cols[0].get_text()
            url = cols[1].get_text()

            # 提取词语时使用动态停用词
            words = word_tokenize(title)
            words = [word for word in words if word not in dynamic_stop_words and re.match(r'\w+', word)]
            word_freq = Counter(words)
            top_words = [word for word, _ in word_freq.most_common(10)]

            news_list.append({"Title": title, "URL": url, "TopWords": top_words})

        result[person_name] = news_list

    return result

# 设置HTML文件路径
file_path = 'news_titles.html'

# 解析HTML并转换为JSON
parsed_data = parse_html_to_json(file_path)

# 将结果保存到JSON文件
with open('output.json', 'w', encoding='utf-8') as json_file:
    json.dump(parsed_data, json_file, ensure_ascii=False, indent=4)
