import time
import requests
import json
import os
from urllib.parse import urlparse, parse_qs
import base64
from flask import Flask, request, jsonify

i = 0
platoboost = "https://gateway.platoboost.com/a/8?id="
discord_webhook_url = "https://discord.com/api/webhooks/1286007233653641246/vjUsAvEcuyxAzJyGh3VZU2txZfa9FO5H1Ohdb1i2WHYlrrrFv-JMfdbveH8xVsBTiAPI" # enter your webhook if security check detected

app = Flask(__name__)

def time_convert(n):
    hours = n // 60
    minutes = n % 60
    return f"{hours} Hours {minutes} Minutes"

def send_discord_webhook(link):
    payload = {
        "embeds": [{
            "title": "Security Check!",
            "description": f"**Please solve the Captcha**: [Open]({link})",
            "color": 5763719
        }]
    }

    try:
        response = requests.post(discord_webhook_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        print(f"\033[31m ERROR \033[0m Error: {error}")

def sleep(ms):
    time.sleep(ms / 1000)

def get_turnstile_response():
    time.sleep(1)
    return "turnstile-response"

def delta(url):
    start_time = time.time()
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        id = query_params.get('id', [None])[0]

        if not id:
            raise ValueError("Invalid URL: 'id' parameter is missing")

        response = requests.get(f"https://api-gateway.platoboost.com/v1/authenticators/8/{id}")
        response.raise_for_status()
        already_pass = response.json()

        if 'key' in already_pass:
            time_left = time_convert(already_pass['minutesLeft'])
            print(f"\033[32m INFO \033[0m Time left:  \033[32m{time_left}\033[0m - KEY: \033[32m{already_pass['key']}\033[0m")
            return {
                "status": "success",
                "key": already_pass['key'],
                "time_left": time_left
            }

        captcha = already_pass.get('captcha')

        if captcha:
            print("\033[32m INFO \033[0m hCaptcha detected! Trying to resolve...")
            # If captcha exists, make sure to solve it before continuing
            response = requests.post(
                f"https://api-gateway.platoboost.com/v1/sessions/auth/8/{id}",
                json={
                    "captcha": get_turnstile_response(),
                    "type": "Turnstile"
                }
            )
        else:
            # if no captcha, continue without it
            response = requests.post(
                f"https://api-gateway.platoboost.com/v1/sessions/auth/8/{id}",
                json={}
            )

        if response.status_code != 200:
            security_check_link = f"{platoboost}{id}"
            send_discord_webhook(security_check_link)
            raise Exception("Security Check, Notified on Discord!")

        loot_link = response.json()
        sleep(1000)
        decoded_lootlink = requests.utils.unquote(loot_link['redirect'])
        parsed_loot_url = urlparse(decoded_lootlink)
        r_param = parse_qs(parsed_loot_url.query)['r'][0]
        decoded_base64 = base64.b64decode(r_param).decode('utf-8')
        tk = parse_qs(urlparse(decoded_base64).query)['tk'][0]
        sleep(5000)

        response = requests.put(f"https://api-gateway.platoboost.com/v1/sessions/auth/8/{id}/{tk}")
        response.raise_for_status()

        response_plato = requests.get(f"https://api-gateway.platoboost.com/v1/authenticators/8/{id}")
        pass_info = response_plato.json()

        if 'key' in pass_info:
            time_left = time_convert(pass_info['minutesLeft'])
            execution_time = time.time() - start_time
            print(f"\033[32m INFO \033[0m Time left:  \033[32m{time_left}\033[0m - KEY: \033[32m{pass_info['key']}\033[0m")
            return {
                "status": "success",
                "key": pass_info['key'],
                
                "time taken": f"{execution_time:.2f} seconds"
            }

    except Exception as error:
        print(f"\033[31m ERROR \033[0m Error: {error}")
        execution_time = time.time() - start_time
        return {
            "status": "error",
            "error": "please solve the hcaptcha nigga",
            "time taken": f"{execution_time:.2f} seconds"
        }

@app.route('/api/delta', methods=['GET'])
def deltax():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    result = delta(url)
    return jsonify(result)
if __name__ == "__main__":
    app.run()
