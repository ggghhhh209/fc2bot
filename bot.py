import telebot
import requests
from bs4 import BeautifulSoup
import re
from telebot import types
import time
import random
import os

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("请在 Railway 设置环境变量 TOKEN")

bot = telebot.TeleBot(TOKEN)

def get_headers():
    return {'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15'
    ])}

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, "🔞 FC2 查询 Bot（Railway版）已启动\n\n支持模糊搜索：输入 4847、3422、大新人 等部分番号或关键词")

def is_fuzzy_match(query, title):
    if not query or not title: return False
    q = query.lower().strip()
    t = title.lower()
    q_clean = re.sub(r'fc2|ppv|-|\s+', '', q)
    t_clean = re.sub(r'fc2|ppv|-|\s+', '', t)
    if q_clean.isdigit() and len(q_clean) >= 3 and q_clean in t_clean:
        return True
    words = [w for w in re.split(r'[\s\-_]+', q) if len(w) > 1]
    match_count = sum(1 for w in words if w in t or w in t_clean)
    return match_count >= max(1, len(words)-1)

def search_source(name, query):
    try:
        bases = {
            "missav": "https://missav.ws/en/search/",
            "spankbang": "https://spankbang.com/s/",
            "fc2db": "https://fc2db.net/search?q="
        }
        url = bases.get(name, bases["missav"]) + requests.utils.quote(query)
        if name == "spankbang":
            url = bases["spankbang"] + requests.utils.quote(query + " fc2 ppv")
        resp = requests.get(url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        for a in soup.find_all('a', href=True)[:12]:
            title = a.get_text(strip=True)[:75]
            if len(title) < 6: continue
            link = a['href']
            if not link.startswith('http'):
                link = "https://missav.ws" + link if "missav" in name else link
            if is_fuzzy_match(query, title) or "fc2" in title.lower():
                prefix = "🎬" if name in ["missav", "spankbang"] else name.upper()
                results.append({"title": f"{prefix}: {title}", "link": link})
        return results
    except:
        return []

@bot.message_handler(func=lambda m: True)
def search(message):
    query = message.text.strip()
    if len(query) < 2:
        return bot.reply_to(message, "请输入至少 2 个字符～")
    results = []
    for name in ["missav", "spankbang", "fc2db"]:
        time.sleep(0.4)
        for item in search_source(name, query):
            results.append((item["title"][:68], item["link"]))
    if not results:
        return bot.reply_to(message, f"“{query}” 未找到结果")
    markup = types.InlineKeyboardMarkup(row_width=1)
    for text, link in results[:15]:
        markup.add(types.InlineKeyboardButton(text, callback_data=link[:64]))
    bot.send_message(message.chat.id, f"找到 {len(results)} 条结果：", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def detail(call):
    bot.answer_callback_query(call.id, "加载中...")
    bot.send_message(call.message.chat.id, f"🔗 链接：\n{call.data}\n\n封面与详细片商功能可后续添加")

print("🔞 FC2 Bot 已启动 - Railway")
bot.infinity_polling(none_stop=True)
