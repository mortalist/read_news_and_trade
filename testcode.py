from newspaper import Article
# import lxml.html.clean
import nltk
from newspaper import fulltext

# Download necessary NLTK resources
nltk.download('punkt_tab')

# 1. Download the article
url = 'https://www.yahoo.com/news/us/article/groundhog-day-2026-punxsutawney-phil-sees-his-shadow-predicting-6-more-weeks-of-winter-122739121.html'
article = Article(url)
article.download()

# 2. Parse the HTML
article.parse()

article.nlp()

# 3. Optional NLP (requires nltk)
article.nlp()

print(f"Title: {article.title}")
print(f"Authors: {article.authors}")
# print(f"Summary: {article.summary}")
print(f"Keywords: {article.keywords}")
print(f"Text: {article.text}")
