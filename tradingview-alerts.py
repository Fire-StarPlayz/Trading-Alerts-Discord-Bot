from flask import Flask, request, jsonify
import requests
from discord_webhook import DiscordWebhook
from datetime import datetime
import time

app = Flask(__name__)

# Replace with actual values
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1345732610910982255/641aSmpD53GHAb2E-9krSn1783B3A_3cavuaCUpgz3tGNuo-nGNl80puXHL7IwLMTvQD"
GOVEE_API_KEY = "a6ca3963-25de-4bc7-a08c-11c3e2a3f188"
GOVEE_DEVICE = "your_govee_device_id"
GOVEE_MODEL = "your_govee_model"

# Function to send a Discord message
def send_discord_message(content):
    timestamp = datetime.now().strftime("%I:%M %p")  # Format: 03:00 PM
    message = f"[{timestamp}]: {content}"
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=message)
    webhook.execute()

# Function to control Govee light with color
def control_govee_light(turn_on=False, color=(255, 255, 255)):  # Default: White
    url = "https://developer-api.govee.com/v1/devices/control"
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "device": GOVEE_DEVICE,
        "model": GOVEE_MODEL,
        "cmd": {
            "name": "turn",
            "value": "on" if turn_on else "off"
        }
    }
    requests.put(url, json=payload, headers=headers)

    # Change light color if turning on
    if turn_on:
        color_payload = {
            "device": GOVEE_DEVICE,
            "model": GOVEE_MODEL,
            "cmd": {
                "name": "color",
                "value": {"r": color[0], "g": color[1], "b": color[2]}
            }
        }
        requests.put(url, json=color_payload, headers=headers)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received webhook data:", data)

    message = data.get("message", "")

    if not message:
        send_discord_message("❓ No valid stock data received.")
        return jsonify({"status": "error", "message": "No stock data"}), 400

    # Expected format: "AAPL Crossing Down 241.84"
    parts = message.split()
    if len(parts) < 4:
        send_discord_message("❓ Unexpected message format received.")
        return jsonify({"status": "error", "message": "Invalid format"}), 400

    stock_symbol = parts[0]  # e.g., "AAPL"
    direction = parts[2]  # "Up" or "Down"
    price = parts[3]  # e.g., "241.84"

    # Determine light color based on direction
    if direction.lower() == "down":
        color = (255, 0, 0)  # Red for Down
        emoji = "📉"
    elif direction.lower() == "up":
        color = (0, 255, 0)  # Green for Up
        emoji = "📈"
    else:
        color = (255, 255, 255)  # White for unknown
        emoji = "❓"

    # Format Discord message
    stock_message = f"{emoji} **{stock_symbol}**: **{direction}** - **${price}**"

    # Send to Discord & control light
    send_discord_message(stock_message)
    control_govee_light(turn_on=True, color=color)
    
    # Turn off light after 5 seconds
    time.sleep(5)
    control_govee_light(turn_on=False)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
