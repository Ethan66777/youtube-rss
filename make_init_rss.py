import os
import pandas as pd
import feedparser
import requests

# ==================== 统一配置 ====================
EXCEL_FILE = 'rss.xlsx'
COLUMN_NAME = 'ID'
OUTPUT_XML_PATH = 'youtube_rss.xml' # 直接保存在仓库根目录
# ==================================================

def generate_true_youtube_rss():
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ 错误：找不到文件 {EXCEL_FILE}")
        return

    df = pd.read_excel(EXCEL_FILE)
    if COLUMN_NAME not in df.columns:
        print(f"❌ 错误：Excel中找不到列 '{COLUMN_NAME}'")
        return

    channel_ids = df[COLUMN_NAME].dropna().tolist()
    all_video_items = []

    print(f"🚀 [GitHub云端模式] 开始抓取 {len(channel_ids)} 个频道的最新视频...")

    # 标准浏览器伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for cid in channel_ids:
        cid = str(cid).strip()
        if not cid or cid.startswith('#'):
            continue
        
        youtube_feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        print(f" 正在抓取频道: {cid} ...", end="", flush=True)
        
        try:
            # GitHub海外机房直接请求，绝无封锁
            response = requests.get(youtube_feed_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f" ⚠️ 抓取失败 (状态码: {response.status_code})")
                continue
                
            feed = feedparser.parse(response.text)
            if not feed.entries:
                print(" ⚠️ 暂无具体视频")
                continue

            count = 0
            for entry in feed.entries[:3]: # 每个博主取最新的 3 个视频
                title = entry.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                link = entry.link
                pub_date = entry.published if 'published' in entry else ''
                guid = entry.id if 'id' in entry else link
                channel_name = feed.feed.title if 'title' in feed.feed else 'YouTube博主'

                item_xml = f"""        <item>
            <title>[{channel_name}] {title}</title>
            <link>{link}</link>
            <guid isPermaLink="false">{guid}</guid>
            <pubDate>{pub_date}</pubDate>
            <description>您关注的博主 {channel_name} 发布了新视频！</description>
        </item>"""
                all_video_items.append(item_xml)
                count += 1
            print(f" ✅ 成功抓取 {count} 个最新视频")

        except Exception as e:
            print(f" ❌ 异常: {e}")

    items_string = "\n".join(all_video_items)
    rss_final_template = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
    <channel>
        <title>我的YouTube全自动追更总线</title>
        <link>https://github.com</link>
        <description>Custom Aggregated Feed</description>
{items_string}
    </channel>
</rss>"""

    with open(OUTPUT_XML_PATH, 'w', encoding='utf-8') as f:
        f.write(rss_final_template)
    
    print(f"\n🎉 云端处理大功告成！文件已成功更新。")

if __name__ == "__main__":
    generate_true_youtube_rss()