from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import requests
import json
from typing import List, Dict
from dotenv import load_dotenv
from anthropic import Anthropic
class FlashcardAutomation:
    def __init__(self, claude_api_key: str):
        # Setup Chrome options for better stability
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-popup-blocking')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.claude_client = Anthropic(api_key=claude_api_key)
        
    def wait_and_click(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 10) -> bool:
        """Enhanced utility method to wait for element and click it using multiple strategies"""
        try:
            # First attempt: Standard wait and click
            print(f"Attempting to find element: {selector}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            
            # Scroll into view
            print("Scrolling element into view...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)  # Wait for scroll to complete
            
            # Try multiple click strategies
            try:
                print("Attempting standard click...")
                element.click()
                return True
            except Exception as e1:
                print(f"Standard click failed: {str(e1)}")
                
                try:
                    print("Attempting JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception as e2:
                    print(f"JavaScript click failed: {str(e2)}")
                    
                    try:
                        print("Attempting Actions chain click...")
                        actions = ActionChains(self.driver)
                        actions.move_to_element(element).click().perform()
                        return True
                    except Exception as e3:
                        print(f"Actions chain click failed: {str(e3)}")
                        
                        # Final attempt: Try to locate by href and navigate
                        try:
                            print("Attempting href navigation...")
                            href = element.get_attribute('href')
                            if href:
                                self.driver.get(href)
                                return True
                        except Exception as e4:
                            print(f"Href navigation failed: {str(e4)}")
            
            return False
            
        except Exception as e:
            print(f"Error finding/clicking element '{selector}': {str(e)}")
            return False

    def expand_subcategory(self, subcategory_element) -> bool:
        """Expand subcategory and check for flashcards"""
        try:
            print(f"Attempting to expand subcategory...")
            
            # Scroll the subcategory into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", subcategory_element)
            time.sleep(0.5)
            
            # Click to expand
            subcategory_element.click()
            time.sleep(1)
            
            # Look for flashcards link
            flashcards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a.exercise.nav-flashcards"
            )
            
            if flashcards:
                print(f"Found {len(flashcards)} flashcard links")
                return True
            else:
                print("No flashcard links found")
                return False
            
        except Exception as e:
            print(f"Error expanding subcategory: {str(e)}")
            return False
        
    def navigate_to_flashcards(self) -> bool:
        """Navigate to flashcards section with improved link finding"""
        try:
            print("Looking for flashcard link...")
            
            # First try to find the link
            link = self.find_flashcard_link()
            if not link:
                print("No flashcard link found")
                return False
            
            # Try clicking first
            success = self.driver.execute_script('''
                const links = document.querySelectorAll('a.exercise.nav-flashcards');
                for (const link of links) {
                    if (link.href === arguments[0]) {
                        link.click();
                        return true;
                    }
                }
                return false;
            ''', link)
            
            if success:
                print("Successfully clicked flashcard link")
                time.sleep(2)  # Wait for navigation
                return True
                
            # If clicking fails, try direct navigation
            print("Click failed, trying direct navigation...")
            self.driver.get(link)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"Error navigating to flashcards: {str(e)}")
            self.driver.save_screenshot("flashcard-navigation-error.png")
            return False


    def get_flashcard_progress(self) -> tuple[int, int]:
        """Get current progress (completed/total) from flashcard stats"""
        try:
            # Wait for stats message to be visible
            self.wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                "div[data-flashcards-mastering-target='deckStatsMessage']"
            )))
            
            # Extract both completed and total numbers
            stats = self.driver.execute_script('''
                const statsElement = document.querySelector("div[data-flashcards-mastering-target='deckStatsMessage'] p");
                if (!statsElement) return null;
                
                const text = statsElement.textContent;
                const match = text.match(/(\\d+)\\s+out of\\s+(\\d+)\\s+cards/);
                if (!match) return null;
                
                return {
                    completed: parseInt(match[1]),
                    total: parseInt(match[2])
                };
            ''')
            
            if stats:
                print(f"Current progress: {stats['completed']}/{stats['total']} cards")
                return (stats['completed'], stats['total'])
            
            print("Could not determine flashcard progress")
            return (0, 0)
            
        except Exception as e:
            print(f"Error getting flashcard progress: {str(e)}")
            self.driver.save_screenshot("progress-error.png")
            return (0, 0)

    def process_flashcards_section(self):
        """Process all remaining flashcards in current section"""
        try:
            print("\nProcessing flashcard section...")
            
            # Navigate to flashcards first
            if not self.navigate_to_flashcards():
                print("Failed to navigate to flashcards")
                return
            
            # Get initial progress
            completed, total = self.get_flashcard_progress()
            if total == 0:
                print("No flashcards found in this section")
                return
                
            remaining = total - completed
            print(f"\nFound {remaining} remaining flashcards to complete")
            
            if remaining == 0:
                print("All flashcards in this section are already complete")
                return
            
            consecutive_errors = 0
            max_errors = 3
            cards_processed = 0
            
            # Process remaining cards
            while cards_processed < remaining:
                success = self.handle_flashcard()
                if success:
                    cards_processed += 1
                    consecutive_errors = 0
                    print(f"\nProgress: {cards_processed}/{remaining} remaining cards completed")
                    print(f"Overall progress: {completed + cards_processed}/{total}")
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        print(f"\nToo many consecutive errors ({max_errors}) - stopping this section")
                        break
                
                time.sleep(1)
            
            # Verify final progress
            final_completed, final_total = self.get_flashcard_progress()
            print(f"\nSection complete. Final progress: {final_completed}/{final_total}")
            
            if final_completed < final_total:
                print(f"Warning: Section not fully completed. {final_total - final_completed} cards remaining")
                self.driver.save_screenshot(f"incomplete-section-{time.strftime('%Y%m%d-%H%M%S')}.png")
                
        except Exception as e:
            print(f"Error processing flashcards section: {str(e)}")
            self.driver.save_screenshot("section-error.png")
            
        finally:
            print("\nFinished processing section")
        
    def get_total_flashcards(self) -> int:
        """Get total number of flashcards in current section"""
        try:
            # Wait for the stats message to be visible
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "deck-stats-message")))
            
            # Use JavaScript to extract the number from the text
            total_cards = self.driver.execute_script('''
                const statsText = document.querySelector("div[data-flashcards-mastering-target='deckStatsMessage'] p").textContent;
                const match = statsText.match(/out of (\\d+) cards/);
                return match ? parseInt(match[1]) : 0;
            ''')
            
            if total_cards:
                print(f"Found {total_cards} total flashcards in this section")
                return total_cards
            
            # Fallback method if the above doesn't work
            stats_element = self.driver.find_element(By.CSS_SELECTOR, 
                "div[data-flashcards-mastering-target='deckStatsMessage'] strong")
            if stats_element:
                text = stats_element.text
                try:
                    number = int(text)
                    print(f"Found {number} total flashcards using fallback method")
                    return number
                except ValueError:
                    print(f"Could not parse number from text: {text}")
                    
            print("Could not determine total number of flashcards")
            return 0
            
        except Exception as e:
            print(f"Error getting total flashcards: {str(e)}")
            # Take screenshot for debugging
            self.driver.save_screenshot("flashcard-count-error.png")
            return 0

    def handle_flashcard(self) -> bool:
        """Process a single flashcard using JavaScript selectors"""
        try:
            print("\nAnalyzing flashcard state...")
            
            # Check for question using JavaScript
            question = self.driver.execute_script(
                'const el = document.querySelector("#flashcard > div > div.flashcard-game-card-front > div > div.flashcard-game-card-content > div > p"); return el ? el.textContent : null;'
            )
            
            if not question:
                print("No question found - checking if deck is complete")
                return False
                
            print(f"Found question: {question}")
            
            # Check for answer field
            answer_field = self.driver.execute_script(
                'return document.querySelector("#user-guess-text-area")'
            )
            
            if not answer_field:
                print("No answer field found")
                return False
                
            # Get existing text
            existing_text = self.driver.execute_script(
                'return document.querySelector("#user-guess-text-area").value'
            )
            
            # Check if we need to input an answer
            if not existing_text:
                print("Getting Claude's response...")
                answer = self.get_claude_response(question)
                print("Got response from Claude")
                
                # Input answer using JavaScript
                self.driver.execute_script(
                    'arguments[0].value = arguments[1];', 
                    answer_field, 
                    answer
                )
                print("Entered answer")
            else:
                print("Answer field already has text - using existing answer")
            
            # Click flip button using JavaScript
            print("Clicking flip button...")
            success = self.driver.execute_script('''
                const flipButton = document.querySelector("#flashcard > div > div.flashcard-game-card-front > div > div.flashcard-game-card-content > button");
                if (flipButton) {
                    flipButton.click();
                    return true;
                }
                return false;
            ''')
            
            if not success:
                print("Failed to click flip button")
                return False
                
            time.sleep(1)
            
            # Click "I knew it" button using JavaScript
            print("Clicking 'I knew it' button...")
            success = self.driver.execute_script('''
                const knewItButton = document.querySelector("#played-card-submit-know");
                if (knewItButton) {
                    knewItButton.click();
                    return true;
                }
                return false;
            ''')
            
            if not success:
                print("Failed to click 'I knew it' button")
                return False
                
            time.sleep(2)
            
            print("Successfully completed flashcard")
            return True
            
        except Exception as e:
            print(f"Error processing flashcard: {str(e)}")
            self.driver.save_screenshot(f"flashcard-error-{time.strftime('%Y%m%d-%H%M%S')}.png")
            return False

    def start(self, homepage_url: str):
        """Start automation from homepage"""
        self.driver.get(homepage_url)
        time.sleep(3)  # Wait for initial page load
        
    def find_all_modules(self) -> List[Dict]:
        """Find all main module categories"""
        modules = []
        module_elements = self.driver.find_elements(By.CSS_SELECTOR, ".module-header")
        
        for element in module_elements:
            try:
                name = element.find_element(By.CSS_SELECTOR, ".module-header-name").text
                href = element.get_attribute("href")
                modules.append({
                    "name": name,
                    "href": href,
                    "element": element
                })
            except NoSuchElementException:
                continue
                
        return modules
    
    def expand_module(self, module_element) -> List[Dict]:
        """Click on module and find all subcategories"""
        module_element.click()
        time.sleep(1)
        
        subcategories = []
        day_elements = self.driver.find_elements(By.CSS_SELECTOR, ".day")
        
        for day in day_elements:
            try:
                title = day.find_element(By.CSS_SELECTOR, "div").text
                subcategories.append({
                    "title": title,
                    "element": day
                })
            except NoSuchElementException:
                continue
                
        return subcategories
    
    def get_claude_response(self, question: str) -> str:
        """Get response from Claude API using official client"""
        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": question}
                ]
            )
            return response.content[0].text
            
        except Exception as e:
            print(f"Error calling Claude API: {str(e)}")
            return "Error connecting to Claude API"
    
    def find_all_modules(self) -> List[Dict]:
        """Find all main module categories using improved JavaScript"""
        try:
            print("Searching for modules...")
            
            modules = self.driver.execute_script('''
                const moduleElements = document.querySelectorAll(".modules-nav > a");
                return Array.from(moduleElements).map(element => {
                    // Get the name from the module-header-name element
                    const nameElement = element.querySelector(".module-header-name");
                    const name = nameElement ? nameElement.textContent.trim() : "";
                    
                    // Get the href attribute
                    const href = element.href;
                    
                    // Get data attributes that might be useful for navigation
                    const path = element.getAttribute("href");
                    
                    // Debug info
                    console.log("Found module:", {
                        name: name,
                        href: href,
                        path: path
                    });
                    
                    return {
                        name: name || "Unknown",
                        href: href || "",
                        path: path || "",
                        isActive: element.classList.contains("active")
                    };
                }).filter(module => module.href); // Only return modules with valid hrefs
            ''')
            
            if not modules:
                print("No modules found - trying alternative selector...")
                # Try an alternative method
                modules = self.driver.execute_script('''
                    const moduleElements = document.querySelectorAll("[data-original-title]");
                    return Array.from(moduleElements).map(element => ({
                        name: element.getAttribute("data-original-title") || "Unknown",
                        href: element.href,
                        path: element.getAttribute("href"),
                        isActive: element.classList.contains("active")
                    })).filter(module => module.href);
                ''')
            
            print(f"\nFound {len(modules)} modules:")
            for module in modules:
                print(f"- {module['name']} ({module['path']})")
                
            return modules
        except Exception as e:
            print(f"Error finding modules: {str(e)}")
            # Take a screenshot for debugging
            self.driver.save_screenshot("module-detection-error.png")
            return []

    def get_subcategories(self) -> List[Dict]:
        """Get all subcategories with improved flashcard detection"""
        try:
            print("\nFinding subcategories...")
            
            subcategories = self.driver.execute_script('''
                const subcategoryElements = Array.from(
                    document.querySelectorAll("#days-nav > div.days-nav > div > div.day")
                );
                
                return subcategoryElements.map((element, index) => {
                    const titleElement = element.querySelector("div");
                    const title = titleElement ? titleElement.textContent.trim() : "Unknown";
                    
                    // Check next sibling for flashcards
                    const exercisesContainer = element.nextElementSibling;
                    const hasFlashcards = exercisesContainer && 
                                        exercisesContainer.querySelector("a.exercise.nav-flashcards");
                    
                    return {
                        title: title,
                        index: index + 1,
                        selector: `#days-nav > div.days-nav > div > div:nth-child(${2 * index + 1})`,
                        hasFlashcards: Boolean(hasFlashcards)
                    };
                });
            ''')
            
            if subcategories:
                print(f"\nFound {len(subcategories)} subcategories:")
                for subcat in subcategories:
                    print(f"- {subcat['title']} {'(has flashcards)' if subcat['hasFlashcards'] else ''}")
            else:
                print("No subcategories found")
                
            return subcategories
            
        except Exception as e:
            print(f"Error finding subcategories: {str(e)}")
            self.driver.save_screenshot("subcategory-error.png")
            return []

    def navigate_to_module(self, module: Dict) -> bool:
        """Navigate to a specific module with improved error handling"""
        try:
            if not module.get('path') and not module.get('href'):
                print("No valid navigation path found for module")
                return False
                
            print(f"\nNavigating to module: {module['name']}")
            
            # Try clicking first
            try:
                element = self.driver.execute_script(f'''
                    return document.querySelector(`a[href="{module['path']}"]`) ||
                        document.querySelector(`a[href="{module['href']}"]`);
                ''')
                
                if element:
                    print("Found module element, attempting to click...")
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(2)
                    return True
            except Exception as click_error:
                print(f"Click navigation failed: {click_error}")
            
            # Fallback to direct navigation
            print("Attempting direct navigation...")
            navigation_url = module.get('href') or module.get('path')
            if navigation_url:
                if not navigation_url.startswith('http'):
                    base_url = self.driver.current_url.split('?')[0]
                    navigation_url = f"{base_url}{navigation_url}"
                
                print(f"Navigating to: {navigation_url}")
                self.driver.get(navigation_url)
                time.sleep(2)
                return True
                
            print("All navigation attempts failed")
            return False
            
        except Exception as e:
            print(f"Error navigating to module: {str(e)}")
            self.driver.save_screenshot("navigation-error.png")
            return False


    def expand_subcategory(self, subcategory: Dict) -> bool:
        """Expand a specific subcategory using JavaScript"""
        try:
            print(f"\nExpanding subcategory: {subcategory['title']}")
            
            success = self.driver.execute_script('''
                const element = document.querySelector(arguments[0]);
                if (!element) return false;
                
                // First scroll into view
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Check if it's already expanded
                const nextElement = element.nextElementSibling;
                const isExpanded = nextElement && 
                                nextElement.classList.contains('exercises') && 
                                !nextElement.classList.contains('no-height');
                                
                if (!isExpanded) {
                    // Click to expand if not already expanded
                    element.click();
                }
                
                return true;
            ''', subcategory['selector'])
            
            if success:
                print("Successfully expanded subcategory")
                time.sleep(2)  # Wait longer for expansion and content load
                return True
            else:
                print("Failed to find subcategory element")
                return False
                
        except Exception as e:
            print(f"Error expanding subcategory: {str(e)}")
            self.driver.save_screenshot("subcategory-expansion-error.png")
            return False

        
    def find_flashcard_link(self) -> str:
        """Find the flashcard link in the current subcategory"""
        try:
            link = self.driver.execute_script('''
                // Find all exercise containers
                const exerciseContainers = document.querySelectorAll('.exercises');
                
                // Look through each container for flashcard links
                for (const container of exerciseContainers) {
                    const flashcardLink = container.querySelector('a.exercise.nav-flashcards');
                    if (flashcardLink) {
                        // Return the href value
                        return flashcardLink.href;
                    }
                }
                return null;
            ''')
            
            if link:
                print(f"Found flashcard link: {link}")
                return link
            
            print("No flashcard link found")
            return None
            
        except Exception as e:
            print(f"Error finding flashcard link: {str(e)}")
            return None
        
    def process_all_content(self):
        """Main method to process all flashcards with improved subcategory handling"""
        try:
            # Get all modules
            modules = self.find_all_modules()
            
            if not modules:
                print("No modules found")
                self.driver.save_screenshot("no-modules-found.png")
                return
            
            for module in modules:
                print(f"\n{'='*20}")
                print(f"Processing module: {module['name']}")
                print(f"{'='*20}")
                
                # Navigate to module
                if not self.navigate_to_module(module):
                    print(f"Skipping module {module['name']} due to navigation error")
                    continue
                
                time.sleep(2)  # Wait for page load
                
                # Get subcategories
                subcategories = self.get_subcategories()
                
                if not subcategories:
                    print("No subcategories found in this module")
                    continue
                
                for subcategory in subcategories:
                    print(f"\n{'-'*20}")
                    print(f"Checking subcategory: {subcategory['title']}")
                    
                    # Skip if no flashcards
                    if not subcategory.get('hasFlashcards'):
                        print("No flashcards in this subcategory - skipping")
                        continue
                    
                    # Expand subcategory
                    if not self.expand_subcategory(subcategory):
                        print("Failed to expand subcategory - skipping")
                        continue
                    
                    # Process flashcards
                    print("Processing flashcards...")
                    self.process_flashcards_section()
                    
                    # Return to module page to maintain clean state
                    print("Returning to module page...")
                    if not self.navigate_to_module(module):
                        print("Failed to return to module page - breaking")
                        break
                
                print(f"\nCompleted module: {module['name']}")
                
        except Exception as e:
            print(f"Critical error in process_all_content: {str(e)}")
            self.driver.save_screenshot("critical-error.png")

    def cleanup(self):
        """Close the browser"""
        self.driver.quit()

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key with better error handling
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    if not claude_api_key:
        print("ERROR: CLAUDE_API_KEY not found in environment variables")
        print("Please create a .env file with your API key like: CLAUDE_API_KEY=your_key_here")
        return
        
    if not claude_api_key.startswith("sk-"):
        print("WARNING: API key format looks incorrect (should start with 'sk-')")
    
    # Starting URL
    homepage_url = "https://kitt.lewagon.com/camps/1720/challenges?path=00-Setup"
    
    bot = FlashcardAutomation(claude_api_key)
    try:
        bot.start(homepage_url)
        input("Please log in manually and press Enter when ready...")
        print("\nStarting automation...\n")
        bot.process_all_content()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        bot.driver.save_screenshot("final-error.png")
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()