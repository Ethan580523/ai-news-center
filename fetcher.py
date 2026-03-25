import asyncio
import httpx
import json
import logging
from datetime import datetime

# ==========================================
# ⚙️ 配置中心 (Configuration)
# ==========================================
# 已从您之前的配置自动提取 Token
APP_TOKEN = "AT_O3BhwBWixNav2KkGcmxLbp9mw4ZrwP3I"
USER_UIDS = ["UID_0oRVQ80s7PlznWiTPPxKkdIBv0MI"]

DB_FILE = "news_db.json"
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
WEIBO_API = "https://api.vvhan.com/api/hotlist/wbHot"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==========================================
# 🤖 逻辑核心 (Core Logic)
# ==========================================

async def mock_ai_summarization(title: str, url: str):
    """
    [AI 摘要引擎] 模拟 AI 的深度解剖功能。
    实际应用中此处可以对接 OpenAI 或 Gemini 的 API 接口。
    """
    # 模拟一个有深度的 AI 前瞻摘要逻辑
    prefix = [
        "【AI 视角】该技术可能彻底重构现有开发范式。",
        "【深度财考】此话题背后折射出当下国内社交媒体的情绪共振点。",
        "【行业前瞻】该开源项目正在 GitHub 上引发千万级关注，其核心在于极简的架构选择。"
    ]
    import random
    return f"{random.choice(prefix)} 核心价值点：1. 解决了痛点 X；2. 大幅提升了效率。建议重点关注：{url[:30]}..."

async def fetch_everything():
    """
    全量抓取并将结果存入本地 JSON 数据库
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        all_results = {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "news": []
        }
        
        # 1. 抓取 Hacker News 
        try:
            hn_res = await client.get(HN_TOP_URL)
            ids = hn_res.json()[:8]
            tasks = [client.get(HN_ITEM_URL.format(item_id=i)) for i in ids]
            hn_items = await asyncio.gather(*tasks)
            
            for res in hn_items:
                if res.status_code == 200:
                    d = res.json()
                    summary = await mock_ai_summarization(d.get("title"), d.get("url", ""))
                    all_results["news"].append({
                        "type": "HackerNews",
                        "title": d.get("title"),
                        "url": d.get("url"),
                        "summary": summary,
                        "score": d.get("score")
                    })
        except Exception as e:
            logging.error(f"HN 抓取失败: {e}")

        # 2. 抓取 微博热搜
        try:
            wb_res = await client.get(WEIBO_API)
            wb_data = wb_res.json()
            if wb_data["success"]:
                for item in wb_data["data"][:10]:
                    summary = await mock_ai_summarization(item["title"], item["url"])
                    all_results["news"].append({
                        "type": "Weibo",
                        "title": item["title"],
                        "url": item["url"],
                        "summary": summary,
                        "hot": item["hot"]
                    })
        except Exception as e:
            logging.error(f"Weibo 抓取失败: {e}")

        # 3. 存储到本地数据库 (data.json)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        logging.info(f"✅ 数据入库完毕！共处理 {len(all_results['news'])} 条情报。")
        return all_results

async def send_daily_wx(results):
    """
    同步发送简报到微信 (WxPusher)
    """
    async with httpx.AsyncClient() as client:
        # 增加鲁棒性检查：防止列表为空导致 IndexError
        hn_list = [n for n in results["news"] if n["type"] == "HackerNews"]
        wb_list = [n for n in results["news"] if n["type"] == "Weibo"]
        
        hn_title = hn_list[0]['title'] if hn_list else "今日无重大技术更新"
        wb_title = wb_list[0]['title'] if wb_list else "当前微博热搜离线"
        
        msg_content = f"""
        <h3>📅 AI 极客每日简报 (自动补全版)</h3>
        <p><b>🌍 全球之眼:</b> {hn_title}</p>
        <p><b>🔥 微博之眼:</b> {wb_title}</p>
        <hr>
        <p>✅ 本次本地同步共记录 {len(results['news'])} 条深度报告。</p>
        """
        
        url = "https://wxpusher.zjiecode.com/api/send/message"
        payload = {
            "appToken": APP_TOKEN,
            "content": msg_content,
            "summary": "🤖 AI 情报中心已同步库内容",
            "contentType": 2,
            "uids": USER_UIDS
        }
        await client.post(url, json=payload)
        logging.info("📫 已同步更新推送至您的微信！")

async def main():
    # 周期性工作的间隔时间 (单位: 秒)。3600 秒 = 1 小时
    INTERVAL = 3600 

    logging.info("🚀 全自动 AI 情报机器人进入「长驻后台」模式...")
    logging.info(f"⏰ 设置为每隔 {INTERVAL/60:.1f} 分钟自动同步一次数据并推送到微信。")

    import os
    run_once = os.environ.get("RUN_ONCE", "false").lower() == "true"

    while True:
        try:
            logging.info("--- 🔄 开始新一轮自动化情报同步流程 ---")
            results = await fetch_everything()
            await send_daily_wx(results)
            
            if run_once:
                logging.info("🚀 [云端模式] 任务已顺利完成，正在提交并释放算力...")
                break
                
            logging.info(f"💤 任务圆满完成！进入休眠，将在 {INTERVAL} 秒后开启下一轮监控...")
        except Exception as e:
            logging.error(f"⚠️ 自动化流程中遭遇突发异常: {e}")
            if run_once: break # 云端遇到错误也要退出
            await asyncio.sleep(60)
            continue
            
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⏹️ 机器人已手动离岗，感谢使用！")
