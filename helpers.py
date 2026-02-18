import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
)


def wait_for_page_ready(driver, timeout=120):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modalBgd"))
        )
    except:
        pass
    time.sleep(1)


def safe_click(driver, by, locator):
    try:
        wait_for_page_ready(driver)

        element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((by, locator))
        )

        element.click()
        wait_for_page_ready(driver)
        return True

    except (ElementClickInterceptedException, StaleElementReferenceException, TimeoutException):
        time.sleep(1)
