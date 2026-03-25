@echo off
:: 自动切换到该脚本所在的目录 (ai-news-center)
cd /d "c:\Users\Ethan Ling\.gemini\antigravity\playground\harmonic-copernicus\ai-news-center"

:: 执行抓取脚本 (这里建议使用 fetcher.py 的非循环版本，或者只运行一次)
echo --- [%DATE% %TIME%] AI 情报中心正在自动入库并传送至微信... ---
python fetcher.py

exit
