from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils.automation import (
    is_logged_in, 
    get_new_tweets, 
    reply_to_tweet, 
    save_seen_ids, 
    load_seen_ids,
    human_like_scroll,
    start_continuous_cursor_movement,
    stop_continuous_cursor_movement,
    like_tweet
)
import time
import random
from datetime import datetime, timedelta

def setup_driver():
    """Setup Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # IMPORTANT: User data dir to persist login session
    # This keeps you logged in between runs
    import os
    profile_path = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f"user-data-dir={profile_path}")
    
    # Optional: Use a specific profile (recommended for stability)
    options.add_argument("profile-directory=Default")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def main():
    driver = setup_driver()
    seen_ids = load_seen_ids()
    tweets_replied = 0  # Initialize at the start
    reply_timestamps = []  # Track when replies were sent
    MAX_REPLIES_PER_HOUR = 30
    
    try:
        # Open Twitter
        print("Opening Twitter/X...")
        driver.get("https://twitter.com/home")
        time.sleep(3)
        
        # Check if logged in
        if not is_logged_in(driver):
            print("Please log into Twitter/X in the browser window...")
            time.sleep(30)  # Wait for manual login
            
            if not is_logged_in(driver):
                print("Not logged in. Exiting...")
                return
        
        print("Login detected! Starting bot...")
        
        # Start continuous cursor movement in background
        start_continuous_cursor_movement(driver)
        
        # Main loop - runs continuously
        scroll_count = 0
        max_scrolls_before_break = random.randint(10, 15)
        
        while True:
            try:
                # Remove old timestamps (older than 1 hour)
                current_time = datetime.now()
                reply_timestamps = [ts for ts in reply_timestamps if current_time - ts < timedelta(hours=1)]
                
                # Check if we've hit the hourly limit
                if len(reply_timestamps) >= MAX_REPLIES_PER_HOUR:
                    oldest_reply = min(reply_timestamps)
                    wait_time = (oldest_reply + timedelta(hours=1) - current_time).total_seconds()
                    wait_minutes = int(wait_time / 60)
                    print(f"\n⏰ Hit hourly limit ({MAX_REPLIES_PER_HOUR} replies/hour)")
                    print(f"⏰ Waiting {wait_minutes} minutes before resuming...")
                    time.sleep(wait_time + 10)  # Wait plus a little buffer
                    continue
                
                # Get new tweets
                new_tweets = get_new_tweets(driver, seen_ids)
                print(f"Found {len(new_tweets)} new tweets")
                print(f"📊 Replies in last hour: {len(reply_timestamps)}/{MAX_REPLIES_PER_HOUR}")
                
                if new_tweets:
                    # Reply to a random subset (not all at once to seem more human)
                    tweets_to_reply = random.sample(new_tweets, min(len(new_tweets), random.randint(1, 3)))
                    
                    for tweet in tweets_to_reply:
                        # Check limit again before each reply
                        reply_timestamps = [ts for ts in reply_timestamps if datetime.now() - ts < timedelta(hours=1)]
                        if len(reply_timestamps) >= MAX_REPLIES_PER_HOUR:
                            print(f"⏰ Reached hourly limit during batch, stopping this cycle")
                            break
                        
                        print(f"\nProcessing tweet: {tweet['text'][:50]}...")
                        
                        # Randomly decide to like the tweet (40% chance)
                        if random.random() < 0.4:
                            print("💖 Attempting to like tweet...")
                            like_success = like_tweet(driver, tweet["element"])
                            if like_success:
                                print("✓ Tweet liked")
                            time.sleep(random.uniform(1, 2))
                        
                        success = reply_to_tweet(driver, tweet["element"], tweet["text"])
                        
                        if success:
                            seen_ids.add(tweet["id"])
                            save_seen_ids(seen_ids)
                            tweets_replied += 1
                            reply_timestamps.append(datetime.now())
                            print(f"✓ Total replies sent: {tweets_replied} (Last hour: {len(reply_timestamps)}/{MAX_REPLIES_PER_HOUR})")
                        else:
                            print("✗ Failed to reply, skipping...")
                        
                        # Random delay between replies
                        time.sleep(random.uniform(5, 10))
                
                # Scroll to load more tweets
                print("Scrolling to load more tweets...")
                human_like_scroll(driver)
                scroll_count += 1
                time.sleep(random.uniform(3, 6))
                
                # Take occasional breaks to seem more human
                if scroll_count >= max_scrolls_before_break:
                    break_time = random.randint(30, 90)
                    print(f"\n💤 Taking a {break_time}s break to seem more human...")
                    time.sleep(break_time)
                    scroll_count = 0
                    max_scrolls_before_break = random.randint(10, 15)
                
                # Random pause between cycles
                time.sleep(random.uniform(2, 5))
                
            except KeyboardInterrupt:
                print("\n\nStopping bot...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)
                continue
    
    finally:
        stop_continuous_cursor_movement()
        save_seen_ids(seen_ids)
        print(f"\nBot stopped. Total replies sent: {tweets_replied}")
        driver.quit()

if __name__ == "__main__":
    main()