from gnews import GNews

# 创建GNews实例，设置语言为繁体中文，国家为台湾
google_news = GNews(language='zh-Hant', country='TW')

# 获取新闻
news = google_news.get_news('周弘憲')

# 打印所有新闻
for index, item in enumerate(news):
    print(f"新闻 {index + 1}:")
    print(f"标题: {item['title']}")
    print(f"链接: {item['url']}")
    print(f"发布日期: {item['published date']}")
    print(f"描述: {item['description']}")
    print("\n")
