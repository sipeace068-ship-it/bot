import os
import json
import logging
import time
import threading
from datetime import datetime
from flask import Flask, jsonify
import requests

# === CONFIGURATION ===
TOKEN = os.environ.get('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 8080))
DATA_FILE = 'vip_reload_users.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === STORAGE ===
class Storage:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_data(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Save error: {e}")

    def get_user(self, user_id):
        if user_id not in self.data:
            self.data[user_id] = {
                'user_id': user_id,
                'joined_at': datetime.now().isoformat(),
                'username': '',
                'first_name': ''
            }
            self._save_data()
        return self.data[user_id]

    def save_user(self, user_id, data):
        self.data[user_id] = data
        self._save_data()

    def get_all_users(self):
        return self.data

storage = Storage()

# === TELEGRAM API ===
def send_message(chat_id, text, parse_mode='Markdown'):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }, timeout=10)
    except Exception as e:
        logger.error(f"Send error: {e}")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {'timeout': 30}
    if offset:
        params['offset'] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get('result', [])
    except Exception as e:
        logger.error(f"Get updates error: {e}")
    return []

def delete_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=10)
    except:
        pass

# === CONTENT ===
VIP_TOOLS = """
🛠 *VIP Digital Tools*
• Premium productivity templates
• High-speed VPN alternatives
• Cloud storage optimization guides
• AI prompt libraries for work
"""

VIP_NEWS = """
📰 *Tech & Finance Insights*
• Weekly market trend summaries
• Tech startup news
• Productivity hacks
• Automation workflows
"""

def handle_start(chat_id, user_data):
    user_id = str(chat_id)
    user = storage.get_user(user_id)
    user['username'] = user_data.get('username', '')
    user['first_name'] = user_data.get('first_name', 'Member')
    storage.save_user(user_id, user)

    welcome = f"""
👑 Welcome to *VIP Reload*, {user['first_name']}!

You have unlocked access to our premium digital network. We provide high-value insights, tech trends, and productivity tools.

📋 *Your VIP Access:*
/dashboard - View your VIP status
/tools - Access VIP digital tools
/insights - Read latest tech & finance insights
/help - View commands

Stay ahead. Stay reloaded. 🚀
    """
    send_message(chat_id, welcome)

def handle_dashboard(chat_id):
    send_message(
        chat_id,
        """
👑 *VIP Dashboard*

Status: *ACTIVE* 🟢
Access Level: *Tier 1*

Welcome to the network. Use the commands below to explore your benefits.
        """
    )

def handle_tools(chat_id):
    send_message(chat_id, VIP_TOOLS)

def handle_insights(chat_id):
    send_message(chat_id, VIP_NEWS)

def handle_help(chat_id):
    send_message(
        chat_id,
        """
📚 *VIP Reload Commands*

/dashboard - Check VIP status
/tools - Get premium tools
/insights - Read latest insights
/help - Show this menu

*Disclaimer:*
This bot provides digital information and tools only. It does not offer financial advice, trading signals, or gambling services.
        """
    )

# === POLLING ===
def process_updates():
    last_update_id = 0
    delete_webhook()
    logger.info("Polling started...")

    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)
            for update in updates:
                uid = update.get('update_id')
                if uid:
                    last_update_id = uid

                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    user_data = msg.get('from', {})

                    if 'text' in msg:
                        text = msg['text']

                        if text.startswith('/start'):
                            handle_start(chat_id, user_data)
                        elif text.startswith('/dashboard'):
                            handle_dashboard(chat_id)
                        elif text.startswith('/tools'):
                            handle_tools(chat_id)
                        elif text.startswith('/insights'):
                            handle_insights(chat_id)
                        elif text.startswith('/help'):
                            handle_help(chat_id)
                        else:
                            send_message(
                                chat_id,
                                "Command not recognized. Use /help to see available commands."
                            )
            time.sleep(2)
        except Exception as e:
            logger.error(f"Process updates error: {e}")
            time.sleep(5)

# === FLASK ===
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    users = storage.get_all_users()
    return f"<h1>VIP Reload Bot</h1><p>Members: {len(users)}</p><p>Status: Active</p>"

@app.route('/stats', methods=['GET'])
def stats():
    users = storage.get_all_users()
    return jsonify({'members': len(users)})

# === MAIN ===
def main():
    logger.info("Starting VIP Reload Bot...")
    threading.Thread(target=process_updates, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    main()
