# poll-bbox-notify-discord

This Python script monitors a specified URL for WebRTC streaming activity and sends notifications to a Discord channel when the streaming status changes.

## Features

- Detects WebRTC streams using Selenium WebDriver
- Sends notifications to a Discord channel
- Configurable check interval
- Uses environment variables for sensitive information

## Prerequisites

- Python 3.7+
- Google Chrome browser

## Installation

1. Clone this repository or download the script:

   ```
   git clone https://github.com/afiaka87/poll-bbox-notify-discord.git
   cd poll-bbox-notify-discord
   ```

2. Install the required Python packages:

   ```
   pip install selenium webdriver_manager discord.py python-dotenv
   ```

3. Set up a Discord bot and get its token:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" tab and add a bot to your application
   - Copy the bot token

4. Invite the bot to your Discord server and note the channel ID where you want to receive notifications

5. Create a `.env` file in the same directory as the script with the following content:

   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   DISCORD_CHANNEL_ID=your_discord_channel_id_here
   ```

   Replace `your_discord_bot_token_here` with your actual Discord bot token and `your_discord_channel_id_here` with the ID of the channel where you want to receive notifications.

## Usage

Run the script with the following command:

```
python poll_bbox_notify_discord.py --url https://example.com/stream --interval 30
```

Arguments:
- `--url`: The URL to monitor for streaming (required)
- `--interval`: Check interval in seconds (optional, default is 60)

The script will continuously monitor the specified URL and send notifications to the configured Discord channel when the streaming status changes.

## How it works

1. The script uses Selenium WebDriver to load the specified URL in a headless Chrome browser.
2. It checks for the presence of a video element and monitors its playback status.
3. If a change in streaming status is detected, it sends a notification to the specified Discord channel.
4. This process repeats at the specified interval.

## Troubleshooting

- If you encounter issues with Chrome driver, ensure you have the latest version of Google Chrome installed.
- Make sure your Discord bot has the necessary permissions to send messages in the specified channel.
- Check that your `.env` file is in the same directory as the script and contains the correct Discord bot token and channel ID.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.