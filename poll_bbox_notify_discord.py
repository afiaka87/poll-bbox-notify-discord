import argparse
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import discord

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def setup_driver() -> webdriver.Chrome:
    """
    Set up and return a configured Chrome WebDriver.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def find_video_element(driver: webdriver.Chrome) -> Optional[WebElement]:
    """
    Find the video element on the page.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        Optional[WebElement]: The video element if found, None otherwise.
    """
    try:
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
    except:
        return None

def check_video_playback(driver: webdriver.Chrome, video: WebElement) -> bool:
    """
    Check if the video is currently playing.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        video (WebElement): The video element.

    Returns:
        bool: True if the video is playing, False otherwise.
    """
    return driver.execute_script("return arguments[0].paused === false;", video)

def check_video_events(driver: webdriver.Chrome) -> bool:
    """
    Set up a listener for the 'playing' event on the video and check if it's triggered.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        bool: True if the 'playing' event is detected, False otherwise.
    """
    script = """
    var video = document.querySelector('video');
    if (video) {
        video.addEventListener('playing', function() {
            window.videoPlayingEvent = true;
        });
        setTimeout(function() {
            return window.videoPlayingEvent === true;
        }, 1000);
    }
    return false;
    """
    return driver.execute_script(script)

def detect_stream(driver: webdriver.Chrome) -> bool:
    """
    Attempt to detect if a stream is currently playing.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        bool: True if a stream is detected, False otherwise.
    """
    video = find_video_element(driver)
    if video:
        return check_video_playback(driver, video) or check_video_events(driver)
    return False

class DiscordClient(discord.Client):
    def __init__(self, channel_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = channel_id

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}')

    async def send_notification(self, message: str):
        channel = self.get_channel(self.channel_id)
        if channel:
            await channel.send(message)
        else:
            logger.error(f"Unable to find channel with ID {self.channel_id}")

async def monitor_stream(url: str, discord_client: DiscordClient, check_interval: int = 60) -> None:
    """
    Continuously monitor the given URL for streaming activity and send Discord notifications.

    Args:
        url (str): The URL to monitor.
        discord_client (DiscordClient): The Discord client for sending notifications.
        check_interval (int): Time in seconds between checks. Defaults to 60.
    """
    driver = setup_driver()
    driver.get(url)
    
    try:
        previous_status = None
        while True:
            is_streaming = detect_stream(driver)
            status = "streaming" if is_streaming else "not streaming"
            
            if status != previous_status:
                message = f"{url} is currently {status}"
                logger.info(message)
                await discord_client.send_notification(message)
                previous_status = status
            
            await asyncio.sleep(check_interval)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")
    finally:
        driver.quit()

async def main_async(url: str, check_interval: int) -> None:
    """
    Asynchronous main function to set up Discord client and start stream monitoring.
    """
    token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = int(os.getenv('DISCORD_CHANNEL_ID', 0))

    if not token or not channel_id:
        logger.error("Discord bot token or channel ID not found in environment variables.")
        return

    intents = discord.Intents.default()
    discord_client = DiscordClient(channel_id, intents=intents)
    
    async with discord_client:
        await discord_client.start(token)
        await monitor_stream(url, discord_client, check_interval)

def main() -> None:
    """
    Main function to parse command line arguments and start stream monitoring.
    """
    parser = argparse.ArgumentParser(description="Monitor WebRTC stream status and send Discord notifications.")
    parser.add_argument("--url", required=True, help="URL to monitor for streaming")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    args = parser.parse_args()

    asyncio.run(main_async(args.url, args.interval))

if __name__ == "__main__":
    main()