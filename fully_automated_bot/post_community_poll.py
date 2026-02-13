import json
import time
import os
import undetected_chromedriver as uc # Updated for better automation
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_community_poll(json_file):
    if not os.path.exists(json_file):
        print("❌ JSON file not found!")
        return

    with open(json_file, "r") as f:
        items = json.load(f)

    # --- CONFIGURATION ---
    user_data_path = os.path.join(os.environ['LOCALAPPDATA'], "Google", "Chrome", "User Data")
    
    options = uc.ChromeOptions()
    # Path to your Chrome Profile
    options.add_argument(f"--user-data-dir={user_data_path}")
    options.add_argument("--profile-directory=Default") 

    print("🤖 Starting Undetected Chrome (Bypassing PATH & Bot detection)...")
    
    # uc.Chrome handles the driver download and service setup internally
    try:
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        return

    wait = WebDriverWait(driver, 20)

    try:
        for item in items:
            print(f"🚀 Processing: {item['headline']}")
            driver.get("https://www.youtube.com/community")
            time.sleep(5) # Give YouTube time to recognize the login

            try:
                # 1. Click 'Create Post'
                post_box = wait.until(EC.element_to_be_clickable((By.ID, "placeholder-area")))
                post_box.click()
                time.sleep(2)

                # 2. Select Poll Icon
                poll_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//yt-icon[@type='poll']")))
                poll_btn.click()
                time.sleep(2)

                # 3. Parse and Enter Poll Data
                poll_lines = item['poll'].split('\n')
                question = poll_lines[0].strip()
                options_list = [line.strip() for line in poll_lines[1:] if line.strip()]

                text_input = driver.find_element(By.TAG_NAME, "textarea")
                text_input.send_keys(question)

                # 4. Fill Options
                for idx, opt_text in enumerate(options_list):
                    inputs = driver.find_elements(By.CSS_SELECTOR, "input#poll-choice-input")
                    if idx < len(inputs):
                        inputs[idx].send_keys(opt_text)
                    elif idx < 5:
                        add_btn = driver.find_element(By.ID, "add-option-button")
                        add_btn.click()
                        time.sleep(1)
                        inputs = driver.find_elements(By.CSS_SELECTOR, "input#poll-choice-input")
                        inputs[idx].send_keys(opt_text)

                # 5. POST
                submit_btn = driver.find_element(By.ID, "submit-button")
                if submit_btn.is_enabled():
                    submit_btn.click()
                    print(f"✅ Posted: {question[:30]}...")
                
                time.sleep(5) 

            except Exception as inner_e:
                print(f"⚠️ Item failed: {inner_e}")
                continue

    finally:
        print("🏁 Automation complete.")
        driver.quit()

if __name__ == "__main__":
    post_community_poll("news_data.json")