# main.py －－ Flask + LINE Webhook 入口
# 這是整個 Line Bot 的入口檔案
# main.py  —— 入口＋Adapter（Flask + LINE SDK）
import os
import traceback
from flask import Flask, request, abort
from importlib import import_module

from linebot.v3.messaging import MessagingApi, ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks.models import (
    MessageEvent, TextMessageContent,
    FollowEvent, PostbackEvent, UnfollowEvent
)

# ---------- 專案共用設定 ----------
from utils.api_helper import conf
from config import (
    LINE_CHANNEL_SECRET,
    LINE_CHANNEL_ACCESS_TOKEN,
    IS_DEBUG_MODE,
    ENABLE_DAILY_NOTIFICATIONS,
    setup_logging
)

# Rich‑menu 別名常數
from rich_menu_manager.rich_menu_configs import (
    MAIN_MENU_ALIAS, WEATHER_QUERY_ALIAS,
    TYPHOON_ZONE_ALIAS, LIFE_REMINDER_ALIAS,
    SETTINGS_ALIAS, ALL_RICH_MENU_CONFIGS
)

from main_initializer import initialize

logger = setup_logging(__name__)

# ========== 1) 初始化 SDK（原 line_adapter.py 的內容） ==========
handler = WebhookHandler(LINE_CHANNEL_SECRET)
app = Flask(__name__)

# ========== 3) 綁定事件 ==========
@handler.add(MessageEvent, message=TextMessageContent)
def on_text(event):
    import_module("handlers.text_router").handle(event)

@handler.add(FollowEvent)
def on_follow(event):
    import_module("handlers.follow").handle(event)

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    print(f"User {event.source.user_id} unfollowed the bot.")

@handler.add(PostbackEvent)
def on_postback(event):
    import_module("handlers.postback_router").handle(event)

# ========== 4) Flask webhook ==========
@app.route("/callback", methods=["POST"])
def callback():
    sig  = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except Exception as e:
        print("❌ Webhook 處理錯誤：", e)
        traceback.print_exc()
        abort(400)
    return "OK"

# ---------- 準備初始化用的共用物件 ----------
# 建立一次 ApiClient，供 Rich‑menu 部署、排程等啟動邏輯使用
api_client      = ApiClient(conf)
line_bot_api    = MessagingApi(api_client)
rich_menu_api   = MessagingApi(api_client)

# app_config 供 initialize() 用（可依實際專案再加欄位）
APP_CONFIG = {
    "MAIN_MENU_ALIAS":      MAIN_MENU_ALIAS,
    "WEATHER_QUERY_ALIAS":  WEATHER_QUERY_ALIAS,
    "TYPHOON_ZONE_ALIAS":   TYPHOON_ZONE_ALIAS,
    "LIFE_REMINDER_ALIAS":  LIFE_REMINDER_ALIAS,
    "SETTINGS_ALIAS":       SETTINGS_ALIAS,
    "ALL_RICH_MENU_CONFIGS": ALL_RICH_MENU_CONFIGS,  # <- 你的 rich‑menu JSON + 圖片清單
    "RICH_MENU_ALIAS_MAP":  {}        # initialize() 會寫入實際 ID
}

# ---------- 執行專案啟動初始化 ----------
initialize(
    global_line_bot_api_instance=line_bot_api,
    global_rich_menu_api_instance=rich_menu_api,
    app_config=APP_CONFIG,
    is_debug_mode=IS_DEBUG_MODE,
    enable_daily_notifications=ENABLE_DAILY_NOTIFICATIONS,
    line_channel_access_token=LINE_CHANNEL_ACCESS_TOKEN
)

# ---------- 啟動 Flask ----------
if __name__ == "__main__":
    app.run(port=5000, debug=True)