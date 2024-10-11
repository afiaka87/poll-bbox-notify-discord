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
from discord import TextChannel

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("poll_bbox_notify_discord.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("poll-bbox-notify-discord")

# Configuration from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

class StreamDetector:
    @staticmethod
    def setup_driver() -> webdriver.Chrome:
        logger.info("Setting up Chrome WebDriver")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        logger.debug("Chrome WebDriver set up successfully")
        return driver

    @staticmethod
    def find_video_element(driver: webdriver.Chrome) -> Optional[WebElement]:
        logger.debug("Attempting to find video element")
        try:
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            logger.info("Video element found")
            return video_element
        except:
            logger.warning("No video element found")
            return None

    @staticmethod
    def check_video_playback(driver: webdriver.Chrome, video: WebElement) -> bool:
        logger.debug("Checking video playback status")
        is_playing = driver.execute_script("return arguments[0].paused === false;", video)
        logger.info(f"Video playback status: {'playing' if is_playing else 'paused'}")
        return is_playing

    @staticmethod
    def check_video_events(driver: webdriver.Chrome) -> bool:
        logger.debug("Checking for video playing event")
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
        event_detected = driver.execute_script(script)
        logger.info(f"Video playing event detected: {event_detected}")
        return event_detected

    @staticmethod
    def detect_stream(driver: webdriver.Chrome) -> bool:
        logger.info("Detecting stream")
        video = StreamDetector.find_video_element(driver)
        if video:
            is_streaming = StreamDetector.check_video_playback(driver, video) or StreamDetector.check_video_events(driver)
            logger.info(f"Stream detection result: {'streaming' if is_streaming else 'not streaming'}")
            return is_streaming
        logger.warning("No video element found, assuming not streaming")
        return False

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
from discord import TextChannel

# ... (previous code remains the same)

class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ready = asyncio.Event()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        self.ready.set()

    async def send_notification(self, url: str):
        await self.ready.wait()  # Wait until the bot is ready
        logger.info(f"Attempting to send notification for URL: {url}")
        if not all([GUILD_ID, CHANNEL_ID, url]):
            logger.error("Missing required configuration. Please check your environment variables.")
            return

        try:
            guild = await self.fetch_guild(GUILD_ID)
            if guild:
                logger.debug(f"Guild found: {guild.name}")
                channel = await guild.fetch_channel(CHANNEL_ID)
                if isinstance(channel, TextChannel):
                    message = f"{url} is currently streaming"
                    await channel.send(message)
                    logger.info(f"Notification sent: {message}")
                else:
                    logger.error(f"Channel with ID {CHANNEL_ID} not found or is not a TextChannel.")
            else:
                logger.error(f"Guild with ID {GUILD_ID} not found.")
        except discord.errors.HTTPException as e:
            logger.error(f"Failed to send Discord notification: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while sending notification: {str(e)}")

class StreamMonitor:
    def __init__(self, url: str, bot: DiscordBot, poll_interval_in_seconds: int = 60):
        self.url = url
        self.bot = bot
        self.poll_interval_in_seconds = poll_interval_in_seconds
        self.previously_streaming = False
        self.consecutive_streaming_checks = 0
        self.consecutive_not_streaming_checks = 0
        logger.info(f"StreamMonitor initialized for URL: {url}")
        logger.debug(f"Poll interval set to {poll_interval_in_seconds} seconds")
        self.driver = None

    async def setup_driver(self):
        logger.info("Setting up Chrome WebDriver")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        logger.debug("Chrome WebDriver set up successfully")
        self.driver.get(self.url)

    async def monitor_stream(self):
        logger.info(f"Starting stream monitoring for URL: {self.url}")
        await self.setup_driver()
        try:
            while True:
                logger.debug(f"Checking stream status for {self.url}")
                is_streaming = StreamDetector.detect_stream(self.driver)

                if is_streaming:
                    self.consecutive_streaming_checks += 1
                    self.consecutive_not_streaming_checks = 0
                    logger.debug(f"Streaming detected. Consecutive streaming checks: {self.consecutive_streaming_checks}")
                else:
                    self.consecutive_not_streaming_checks += 1
                    self.consecutive_streaming_checks = 0
                    logger.debug(f"Not streaming. Consecutive not streaming checks: {self.consecutive_not_streaming_checks}")

                if self.consecutive_streaming_checks == 2 and not self.previously_streaming:
                    logger.info(f"Stream started at {self.url}. Sending notification.")
                    await self.bot.send_notification(self.url)
                    self.previously_streaming = True
                elif self.consecutive_not_streaming_checks >= 3 and self.previously_streaming:
                    logger.info(f"Stream ended at {self.url}")
                    self.previously_streaming = False

                logger.debug(f"Waiting for {self.poll_interval_in_seconds} seconds before next check")
                await asyncio.sleep(self.poll_interval_in_seconds)
        except asyncio.CancelledError:
            logger.info("Stream monitoring task cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error during stream monitoring: {str(e)}")
        finally:
            if self.driver:
                logger.info("Closing WebDriver")
                self.driver.quit()

async def main(url: str, poll_interval_in_seconds: int = 60):
    logger.info(f"Starting main function with URL: {url} and poll interval: {poll_interval_in_seconds} seconds")
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = DiscordBot(intents=intents)
    logger.info("Discord bot initialized")

    try:
        # Start the bot in the background
        bot_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
        logger.info("Discord bot task created")

        # Wait for the bot to be ready
        await bot.ready.wait()
        logger.info("Discord bot is ready")

        # Start the stream monitor
        monitor = StreamMonitor(url, bot, poll_interval_in_seconds)
        monitor_task = asyncio.create_task(monitor.monitor_stream())
        logger.info("Stream monitor task created")

        # Wait for the monitor task to complete (which it never will unless there's an error)
        await monitor_task
    except asyncio.CancelledError:
        logger.info("Main function tasks cancelled")
    except Exception as e:
        logger.error(f"Unexpected error in main function: {str(e)}")
    finally:
        # Ensure the bot is closed properly
        await bot.close()
        logger.info("Discord bot closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor WebRTC stream status and send Discord notifications.")
    parser.add_argument("--url", required=True, help="URL to monitor for streaming")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    args = parser.parse_args()

    logger.info(f"Script started with arguments: URL={args.url}, interval={args.interval}")
    asyncio.run(main(args.url, args.interval))