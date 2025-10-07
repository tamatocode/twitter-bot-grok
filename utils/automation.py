from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from services.gemini_api import generate_reply
import time, random
import threading

# Global flag for cursor movement thread
_cursor_moving = False
_cursor_thread = None

def start_continuous_cursor_movement(driver):
    """Start a background thread for continuous cursor movement"""
    global _cursor_moving, _cursor_thread
    
    if _cursor_moving:
        return  # Already running
    
    _cursor_moving = True
    
    def move_cursor():
        """Background task that continuously moves cursor"""
        while _cursor_moving:
            try:
                actions = ActionChains(driver)
                # Small random movements
                x_offset = random.randint(-30, 30)
                y_offset = random.randint(-30, 30)
                actions.move_by_offset(x_offset, y_offset).perform()
                time.sleep(random.uniform(2, 5))  # Move every 2-5 seconds
            except Exception as e:
                # Silently continue if movement fails
                time.sleep(1)
    
    _cursor_thread = threading.Thread(target=move_cursor, daemon=True)
    _cursor_thread.start()
    print("✓ Continuous cursor movement started")

def stop_continuous_cursor_movement():
    """Stop the background cursor movement"""
    global _cursor_moving
    _cursor_moving = False
    print("✓ Continuous cursor movement stopped")

def human_like_mouse_movement(driver, element=None):
    """Simulate human-like mouse movement to specific element"""
    try:
        actions = ActionChains(driver)
        
        if element:
            # Move to element with slight offset
            actions.move_to_element_with_offset(element, random.randint(-5, 5), random.randint(-5, 5))
        else:
            # Random movement
            actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
        
        actions.perform()
        time.sleep(random.uniform(0.1, 0.3))
    except Exception as e:
        print(f"Mouse movement failed: {e}")

def human_like_scroll(driver):
    """Simulate human-like scrolling"""
    try:
        # Scroll down to load more tweets
        scroll_amount = random.randint(400, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        print(f"Scroll failed: {e}")

def is_logged_in(driver):
    """Check if user is logged into Twitter/X"""
    try:
        # Look for elements that indicate logged-in state
        wait = WebDriverWait(driver, 5)
        # Check for compose button or user menu
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[@data-testid="SideNav_NewTweet_Button"]')))
        return True
    except TimeoutException:
        return False

def debug_page_elements(driver):
    """Debug function to see what elements are available"""
    print("=== DEBUG: Available elements on page ===")
    
    # Check for reply buttons
    reply_elements = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Reply")]')
    print(f"Found {len(reply_elements)} reply buttons")
    
    # Check for tweet articles
    articles = driver.find_elements(By.XPATH, '//article[@role="article"]')
    print(f"Found {len(articles)} tweet articles")
    
    # Check for any buttons with "reply" in aria-label
    all_reply_buttons = driver.find_elements(By.XPATH, '//*[contains(@aria-label, "Reply")]')
    print(f"Found {len(all_reply_buttons)} total elements with 'Reply' in aria-label")
    
    print("=== END DEBUG ===")

def save_seen_ids(seen_ids, filename="state/seen_tweets.txt"):
    """Save seen tweet IDs to file"""
    try:
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            for tweet_id in seen_ids:
                f.write(f"{tweet_id}\n")
    except Exception as e:
        print(f"Error saving seen IDs: {e}")

def load_seen_ids(filename="state/seen_tweets.txt"):
    """Load seen tweet IDs from file"""
    seen_ids = set()
    try:
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'r') as f:
            for line in f:
                tweet_id = line.strip()
                if tweet_id:
                    seen_ids.add(tweet_id)
        print(f"Loaded {len(seen_ids)} seen tweet IDs")
    except FileNotFoundError:
        print("No previous seen tweets file found, starting fresh")
    except Exception as e:
        print(f"Error loading seen IDs: {e}")
    return seen_ids

def extract_tweet_text_only(tweet_element):
    """Extract only the written text content from a tweet, ignoring images and media"""
    try:
        # Try to find the main tweet text content
        text_selectors = [
            './/div[@data-testid="tweetText"]',
            './/div[contains(@class, "tweet-text")]',
            './/span[contains(@class, "tweet-text")]',
            './/div[@lang]',
            './/span[@lang]'
        ]
        
        tweet_text = ""
        for selector in text_selectors:
            try:
                text_elements = tweet_element.find_elements(By.XPATH, selector)
                if text_elements:
                    tweet_text = text_elements[0].text.strip()
                    if tweet_text:
                        break
            except:
                continue
        
        # If no specific text element found, try to get all text and filter
        if not tweet_text:
            all_text = tweet_element.text
            lines = all_text.split('\n')
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.isdigit() and
                    not any(word in line.lower() for word in ['ago', 'h', 'm', 's', 'reply', 'retweet', 'like', 'share']) and
                    len(line) > 3):
                    content_lines.append(line)
            
            tweet_text = ' '.join(content_lines)
        
        tweet_text = tweet_text.strip()
        
        if len(tweet_text) < 10 or tweet_text.count(' ') < 2:
            return None
            
        return tweet_text
        
    except Exception as e:
        print(f"Error extracting tweet text: {e}")
        return None

def get_new_tweets(driver, seen_ids):
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, '//article[@role="article"]')))
        
        tweets = driver.find_elements(By.XPATH, '//article[@role="article"]')
        new_tweets = []

        for t in tweets:
            try:
                tweet_text = extract_tweet_text_only(t)
                if not tweet_text:
                    continue
                    
                tweet_id = t.get_attribute("data-tweet-id") or hash(tweet_text)
                if tweet_id not in seen_ids:
                    new_tweets.append({"id": tweet_id, "text": tweet_text, "element": t})
            except Exception as e:
                print(f"Error processing tweet: {e}")
                continue
                
        return new_tweets
    except Exception as e:
        print(f"Error getting tweets: {e}")
        return []

def like_tweet(driver, tweet_element):
    """Like a tweet with human-like behavior"""
    try:
        # Find like button within the tweet
        like_selectors = [
            './/button[@data-testid="like"]',
            './/div[@data-testid="like"]',
            './/button[contains(@aria-label, "Like")]',
        ]
        
        for selector in like_selectors:
            try:
                like_buttons = tweet_element.find_elements(By.XPATH, selector)
                if like_buttons:
                    like_button = like_buttons[0]
                    
                    # Check if already liked (aria-label contains "Liked" or "Unlike")
                    aria_label = like_button.get_attribute('aria-label')
                    if aria_label and ('liked' in aria_label.lower() or 'unlike' in aria_label.lower()):
                        print("Tweet already liked, skipping")
                        return False
                    
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", like_button)
                    time.sleep(random.uniform(0.3, 0.6))
                    
                    # Human-like movement to like button
                    human_like_mouse_movement(driver, like_button)
                    time.sleep(random.uniform(0.2, 0.5))
                    
                    # Click with JavaScript to avoid interception
                    driver.execute_script("arguments[0].click();", like_button)
                    time.sleep(random.uniform(0.5, 1))
                    return True
                    
            except Exception as e:
                continue
        
        print("Could not find like button")
        return False
        
    except Exception as e:
        print(f"Error liking tweet: {e}")
        return False


def reply_to_tweet(driver, tweet_element, tweet_text, min_delay=3, max_delay=6):
    try:
        print(f"Original tweet text: {tweet_text[:100]}...")
        reply_text = generate_reply(tweet_text)
        print(f"Generated reply: {reply_text}")

        wait = WebDriverWait(driver, 15)
        
        # Step 1: Scroll tweet into view naturally
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tweet_element)
        time.sleep(random.uniform(1, 2))
        
        # Step 2: Find and click reply button
        reply_clicked = False
        reply_selectors = [
            './/button[@data-testid="reply"]',
            './/div[@data-testid="reply"]',
            './/button[contains(@aria-label, "Reply")]',
        ]
        
        for selector in reply_selectors:
            try:
                reply_buttons = tweet_element.find_elements(By.XPATH, selector)
                if reply_buttons:
                    reply_button = reply_buttons[0]
                    
                    # Move cursor to button naturally
                    human_like_mouse_movement(driver, reply_button)
                    time.sleep(random.uniform(0.5, 1))
                    
                    # Click with JavaScript to avoid interception
                    driver.execute_script("arguments[0].click();", reply_button)
                    reply_clicked = True
                    print("✓ Reply button clicked")
                    time.sleep(random.uniform(2, 3))
                    break
                    
            except Exception as e:
                continue
        
        if not reply_clicked:
            print("✗ Could not click reply button")
            return False

        # Step 3: Find reply textbox
        textbox_selectors = [
            '//div[@data-testid="tweetTextarea_0"]',
            '//div[@role="textbox"][@contenteditable="true"]',
        ]
        
        reply_box = None
        for selector in textbox_selectors:
            try:
                reply_box = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                print(f"✓ Found reply textbox")
                break
            except TimeoutException:
                continue
        
        if not reply_box:
            print("✗ Could not find reply textbox")
            return False
        
        # Step 4: Focus and clear textbox
        try:
            human_like_mouse_movement(driver, reply_box)
            time.sleep(random.uniform(0.3, 0.6))
            
            reply_box.click()
            time.sleep(random.uniform(0.3, 0.5))
            
            # Clear any existing text
            driver.execute_script("arguments[0].innerText = '';", reply_box)
            time.sleep(random.uniform(0.2, 0.4))
            
            reply_box.click()
            time.sleep(random.uniform(0.2, 0.4))
            
            print("✓ Textbox focused and cleared")
            
        except Exception as e:
            print(f"✗ Error focusing textbox: {e}")
            return False
        
        # Step 5: Type reply with realistic human-like typing (no errors)
        try:
            print("Typing reply...")
            
            # Natural thinking pause before typing
            time.sleep(random.uniform(0.5, 1.5))
            
            words = reply_text.split()
            typed_chars = 0
            
            for word_idx, word in enumerate(words):
                # Occasional pause before starting a word (thinking)
                if random.random() < 0.15:  # 15% chance
                    time.sleep(random.uniform(0.3, 0.9))
                
                # Type each character in the word
                for char_idx, char in enumerate(word):
                    # Refocus occasionally to ensure characters appear
                    if typed_chars % 10 == 0 and typed_chars > 0:
                        reply_box.click()
                        time.sleep(random.uniform(0.05, 0.1))
                    
                    reply_box.send_keys(char)
                    typed_chars += 1
                    
                    # Realistic typing speed with variation
                    if typed_chars <= 3:
                        # Start slow (finding keys)
                        delay = random.uniform(0.15, 0.35)
                    elif typed_chars >= len(reply_text) - 3:
                        # End slower (careful)
                        delay = random.uniform(0.12, 0.28)
                    else:
                        # Normal typing speed with bursts
                        base_speed = random.uniform(0.06, 0.15)
                        
                        # Occasionally faster bursts (2-4 chars)
                        if random.random() < 0.2 and char_idx > 0:
                            base_speed *= 0.5  # Type faster
                        
                        delay = base_speed
                    
                    # Slower on certain keys (shift, punctuation)
                    if char in '.,!?;:':
                        delay += random.uniform(0.1, 0.2)
                    elif char.isupper():
                        delay += random.uniform(0.05, 0.15)
                    
                    time.sleep(delay)
                
                # Add space after word (except last word)
                if word_idx < len(words) - 1:
                    reply_box.send_keys(' ')
                    # Slightly longer pause after space
                    space_delay = random.uniform(0.08, 0.2)
                    
                    # Longer pauses after punctuation
                    if word and word[-1] in '.,!?':
                        space_delay += random.uniform(0.3, 0.7)
                    
                    time.sleep(space_delay)
                
                # Occasional mid-sentence pauses (thinking/reading)
                if random.random() < 0.1 and word_idx < len(words) - 1:
                    time.sleep(random.uniform(0.5, 1.5))
            
            print("✓ Finished typing")
            
            # Natural pause before clicking send (review message)
            review_pause = random.uniform(1.5, 3.5)
            print(f"Reviewing message for {review_pause:.1f}s...")
            time.sleep(review_pause)
            
        except Exception as e:
            print(f"✗ Error typing reply: {e}")
            return False

        # Step 6: Click send button
        send_clicked = False
        send_selectors = [
            '//button[@data-testid="tweetButton"]',
            '//button[@data-testid="tweetButtonInline"]',
            '//div[@data-testid="tweetButton"]',
        ]
        
        for selector in send_selectors:
            try:
                send_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                
                human_like_mouse_movement(driver, send_button)
                time.sleep(random.uniform(0.5, 1))
                
                driver.execute_script("arguments[0].click();", send_button)
                send_clicked = True
                print("✓ Reply posted successfully!")
                break
                
            except:
                continue
        
        if not send_clicked:
            print("✗ Could not click send button")
            return False

        # Step 7: Post-reply behavior
        time.sleep(random.uniform(1, 2))
        
        # Close reply modal if it exists
        try:
            close_button = driver.find_element(By.XPATH, '//div[@aria-label="Close"]')
            driver.execute_script("arguments[0].click();", close_button)
            time.sleep(random.uniform(0.5, 1))
        except:
            pass
        
        # Random scroll after posting
        if random.random() < 0.4:
            human_like_scroll(driver)
        
        # Natural delay before next action
        delay = random.randint(min_delay, max_delay)
        print(f"Waiting {delay} seconds before next action...")
        time.sleep(delay)
        return True
        
    except Exception as e:
        print(f"✗ Error replying to tweet: {e}")
        return False