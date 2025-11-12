from flask import Flask
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
