import time
import logging
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='web_test_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://the-internet.herokuapp.com"
LOGIN_URL = f"{BASE_URL}/login"
USERNAME = "tomsmith"
PASSWORD = "SuperSecretPassword!"
REPORT_FILE = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

@pytest.fixture(scope="module")
def browser():
    """Set up Selenium WebDriver."""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    yield driver
    driver.quit()
    logger.info("Browser closed successfully.")

class TestWebAutomation:
    """Class to encapsulate web automation tests."""

    def test_login_functionality(self, browser):
        """Test login functionality with valid credentials."""
        logger.info("Starting login test...")
        browser.get(LOGIN_URL)
        
        # Fill login form
        browser.find_element(By.ID, "username").send_keys(USERNAME)
        browser.find_element(By.ID, "password").send_keys(PASSWORD)
        browser.find_element(By.CLASS_NAME, "radius").click()
        
        # Verify successful login
        time.sleep(1)  # Wait for page load
        assert "secure" in browser.current_url, "Login failed - URL mismatch"
        success_msg = browser.find_element(By.CLASS_NAME, "flash").text
        assert "You logged into a secure area" in success_msg, "Login message not found"
        logger.info("Login test passed!")

    def test_element_presence(self, browser):
        """Verify key elements are present on the homepage."""
        logger.info("Checking homepage elements...")
        browser.get(BASE_URL)
        
        # Check for specific elements
        elements = {
            "h1_heading": (By.TAG_NAME, "h1"),
            "subheader": (By.CLASS_NAME, "subheader"),
            "footer": (By.ID, "page-footer")
        }
        
        for name, locator in elements.items():
            assert browser.find_element(*locator).is_displayed(), f"{name} not found"
        logger.info("All homepage elements verified!")

    def test_broken_links(self):
        """Check for broken links on the homepage using requests."""
        logger.info("Starting broken link check...")
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a', href=True)]
        
        broken_links = []
        for link in links:
            if not link.startswith('http'):
                link = BASE_URL + link
            try:
                link_response = requests.head(link, timeout=5)
                if link_response.status_code >= 400:
                    broken_links.append((link, link_response.status_code))
                    logger.warning(f"Broken link found: {link} - {link_response.status_code}")
            except requests.RequestException as e:
                broken_links.append((link, f"Error: {str(e)}"))
                logger.error(f"Error checking {link}: {str(e)}")
        
        assert not broken_links, f"Found {len(broken_links)} broken links: {broken_links}"
        logger.info("No broken links found!")

def generate_report(passed_tests, failed_tests):
    """Generate a CSV report of test results."""
    data = {
        "Test Name": [t.__name__ for t in passed_tests + failed_tests],
        "Status": ["Passed" for _ in passed_tests] + ["Failed" for _ in failed_tests],
        "Timestamp": [datetime.now().strftime('%Y-%m-%d %H:%M:%S')] * (len(passed_tests) + len(failed_tests))
    }
    df = pd.DataFrame(data)
    df.to_csv(REPORT_FILE, index=False)
    logger.info(f"Test report generated: {REPORT_FILE}")

if __name__ == "__main__":
    # Run pytest programmatically and capture results
    pytest_args = ["-v", "--disable-warnings"]
    result = pytest.main(pytest_args, plugins=[TestWebAutomation()])
    
    # Simulate test result tracking (in real use, integrate with pytest hooks)
    passed_tests = [TestWebAutomation.test_login_functionality, 
                    TestWebAutomation.test_element_presence, 
                    TestWebAutomation.test_broken_links]
    failed_tests = [] if result == 0 else passed_tests  # Simplified for demo
    generate_report(passed_tests, failed_tests)