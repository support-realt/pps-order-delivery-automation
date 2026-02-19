import os
import json
import time
import requests
import pyotp

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from logger import logger
from constant import BASE_API_URL, PORTAL_LOGIN_URL, ABSTRACT_QUEUE_URL
from helpers import safe_click
from utils import get_download_dir, get_token
from selenium.webdriver.firefox.service import Service
from validators import is_valid_effective_date



class TS:
    def __init__(self, credential):
        self.username = credential["username"]
        self.password = credential["password"]
        self.orders = credential["orders"]

        
        logger.info("Initializing Firefox driver") 
        options = Options() 
        options.add_argument("--headless")              # REQUIRED in Docker
        options.add_argument("--private")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("network.http.use-cache", False)

        service = Service(log_path="/tmp/geckodriver.log")


        self.driver = webdriver.Firefox(options=options,service=service)
        self.wait = WebDriverWait(self.driver, 20)

        self.login_url = PORTAL_LOGIN_URL
        self.queue_url = ABSTRACT_QUEUE_URL

    # ==============================
    # LOGIN
    # ==============================

    def login(self, use_mfa=False, mfa_secret=None):
        d = self.driver
        d.get(self.login_url)

        self.wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys(self.username)

        safe_click(d, By.NAME, "action")

        self.wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        ).send_keys(self.password)

        safe_click(d, By.NAME, "action")

        if use_mfa and mfa_secret:
            code = pyotp.TOTP(mfa_secret).now()
            self.wait.until(EC.presence_of_element_located((By.NAME, "code"))).send_keys(code)
            safe_click(d, By.NAME, "action")

        safe_click(self.driver, By.CSS_SELECTOR, 'a[href="Abstractor/Queue.aspx"]')

        self.abstract_button = WebDriverWait(self.driver, 10).until(
            lambda d: d.find_element(By.XPATH, '//input[@type="search"]')
        )

        logger.info("Logged in and abstract page opened successfully")
        return 'Logged In on TS Portal. Abstract page Opened.'

    # ==============================
    # OPEN ORDER
    # ==============================

    def open_order_from_queue(self, client_ref):
        driver = self.driver

        try:
            self.abstract_button = WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.XPATH, '//input[@type="search"]')
            )
        except:
            safe_click(self.driver, By.ID, "ctl00_Menus1_hlnkAbstract1")
            self.abstract_button = WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.XPATH, '//input[@type="search"]')
            )

        logger.info(f"starting the upload of order : #{client_ref}")

        self.abstract_button.clear()
        self.abstract_button.send_keys(client_ref)

        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.CLASS_NAME, "dataTables_empty")
            )
            logger.info(f"Order with client_ref: {client_ref} Not Found On TS Portal")
            return False

        except:
            logger.info(f"found order #{client_ref} on TS portal")

            tr_list = WebDriverWait(driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "#gviewAbstractQueue tr")
            )

            for tr in tr_list:
                if client_ref in tr.text:
                    try:
                        clickable = tr.find_element(By.TAG_NAME, "a")
                    except:
                        clickable = tr.find_element(By.TAG_NAME, "td")

                    self.driver.execute_script("arguments[0].click();", clickable)
                    break

            time.sleep(1)
            logger.info(f"Order with client_ref: {client_ref} opened successfully")
            return True

    # ==============================
    # ACCEPT ORDER
    # ==============================

    def accept_order_if_needed(self):
        try:
            logger.info("Checking if order needs acceptance")
            
            wait = WebDriverWait(self.driver, 10)

            # Check if Accept button exists & clickable
            accept_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lbtnAcceptOrder"))
            )
            accept_btn.click()

            # Fill "accepted by"
            accepted_by = wait.until(
                EC.visibility_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtAcceptedBy"))
            )
            accepted_by.clear()
            accepted_by.send_keys('arv')

            submit_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lbtnSubmitAccept"))
        )
            submit_btn.click()

            # Handle alert
            wait.until(EC.alert_is_present())
            self.driver.switch_to.alert.accept()

            # Optional: wait for page refresh or button disappear
            wait.until(EC.invisibility_of_element_located(
                (By.ID, "ctl00_ContentPlaceHolder1_lbtnAcceptOrder")
            ))

            logger.info("Order accepted successfully")
            
        except TimeoutException:
            logger.info("Order already accepted or accept button not present")
        except Exception as e:
            logger.exception("Error during order acceptance:")
            pass

    # ==============================
    # FILL ORDER
    # ==============================

    def fill_order(self, order, file_path):
        logger.info(f"Filling order #{order[0]}")

        d = self.driver
        time.sleep(1)

        try:
            date_value = order[3]

            search_pd = WebDriverWait(d, 30).until(
                EC.presence_of_element_located(
                    (By.ID, "ctl00_ContentPlaceHolder1_dateSearchPeriodStart_txtDate")
                )
            )

            d.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('change'));
                arguments[0].dispatchEvent(new Event('blur'));
            """, search_pd, date_value)

            filled_psd = search_pd.get_attribute("value")
            logger.info(f"Period Search Start Date field value after fill: {filled_psd}")

            time.sleep(1)

    
            if is_valid_effective_date(order[2]):
                effective_Date_textbx = WebDriverWait(d, 30).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_dateEffective_txtDate"))
                )
                effective_Date_textbx.click()
                effective_Date_textbx.send_keys(Keys.CONTROL + "a")
                effective_Date_textbx.send_keys(Keys.DELETE)
                effective_Date_textbx.send_keys(order[2].replace('/', ''))

                self.wait.until(
                    EC.element_to_be_clickable(
                        (By.ID, "ctl00_ContentPlaceHolder1_rblNameInTitle_0")
                    )
                ).click()
                filled_effective = effective_Date_textbx.get_attribute("value")
                logger.info(f"Effective Date field value after fill: {filled_effective}")

            else:
                print("effective date is wrong")
                url = "https://api.trumpyts.com/api/orders/{}/".format(order[7])
                data = {'status': 9}
                headers = {
                                    'content-type': 'application/json',
                                    'Authorization': 'Token ' + get_token()
                                }
                requests.patch(url, data=json.dumps(data), headers=headers)
                print("order moved to examine")
                return False
                    
            
            


            if order[6] == "PPS Update":
                if order[5] == "Yes":
                    radio_id = "ctl00_ContentPlaceHolder1_rblOnlyEffectiveDateChanged_0"
                else:
                    radio_id = "ctl00_ContentPlaceHolder1_rblOnlyEffectiveDateChanged_1"

                    note = self.wait.until(
                        EC.presence_of_element_located(
                            (By.ID, "ctl00_ContentPlaceHolder1_txtVendorNotes")
                        )
                    )
                    note.clear()
                    note.send_keys("Please see attached")

                radio_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, radio_id))
                )
                radio_btn.click()

            time.sleep(1)
            print("uploading doc")

            if (order[6] == "Prior Policy Search" and order[5] == "Yes") or (
                order[6] == "PPS Update" and order[5] == "No"
            ):
                print("uploading doc - condition met")
                add_doc_btn = self.wait.until(
        EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_ibtnAddDoc"))
    )
                add_doc_btn.click()

                time.sleep(5)  # same as old working version

                uploader = self.driver.find_element(By.XPATH, "//input[@type='file']")
                uploader.clear()
                uploader.send_keys(file_path)

                add_doc_sub = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lbtnAddDoc"))
                )
                add_doc_sub.click()

                WebDriverWait(self.driver, 90).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

                # 2️⃣ Wait until no AJAX loader exists (if any)
                try:
                    WebDriverWait(self.driver, 30).until_not(
                        EC.presence_of_element_located((By.ID, "progressBackgroundFilter"))
                    )
                except:
                    pass

                # 3️⃣ Small buffer
                time.sleep(5)

            else:
                try:
                    safe_click(self.driver, By.ID, "ctl00_ContentPlaceHolder1_chkNoChanges")
                except:
                    pass

            logger.info("before notes")

            note = self.wait.until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtVendorNotes"))
            )
            note.clear()
            note.send_keys(order[9])

            filled_notes = note.get_attribute("value")
            logger.info(f"Vendor Notes field value after fill: {filled_notes}")
            return True

        except Exception:
            logger.exception(f"Error filling order #{order[0]}")
            raise


    # ==============================
    # COMPLETE ORDER
    # ==============================

  


    def complete_order(self, order):

        from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
        d = self.driver
        wait = WebDriverWait(d, 60)

        try:
            wait.until(lambda driver: driver.execute_script(
                "return document.readyState") == "complete"
            )

            wait.until(
                EC.invisibility_of_element_located(
                    (By.ID, "progressBackgroundFilter")
                )
            )

            jurisdiction_dropdown = wait.until(
                EC.visibility_of_element_located(
                    (By.ID, "ctl00_ContentPlaceHolder1_ddlRecordingJurisdiction")
                )
            )

            select = Select(jurisdiction_dropdown)

            if select.first_selected_option.text.strip() == "Select One":
                select.select_by_visible_text(order[-2][0].title())

            wait.until(
                EC.invisibility_of_element_located(
                    (By.ID, "progressBackgroundFilter")
                )
            )

            submit_btn = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "ctl00_ContentPlaceHolder1_lbtnSubmitOrder")
                )
            )

            d.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
            time.sleep(1)

            wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "ctl00_ContentPlaceHolder1_lbtnSubmitOrder")
                )
            )

            try:
                submit_btn.click()
            except ElementClickInterceptedException:
                d.execute_script("arguments[0].click();", submit_btn)

            # Handle alert
            try:
                WebDriverWait(d, 5).until(EC.alert_is_present())
                d.switch_to.alert.accept()
            except TimeoutException:
                pass
            #mark order as sent



            # Wait overlay after submit
            wait.until(
                EC.invisibility_of_element_located(
                    (By.ID, "progressBackgroundFilter")
                )
            )

            # Wait for success panel
            WebDriverWait(d, 60).until(
                EC.presence_of_element_located(
                    (By.ID, "ctl00_ContentPlaceHolder1_pnlAbstractOrderSubmitSuccess")
                )
            )

               
            url = "https://api.trumpyts.com/api/orders/{}/".format(order[7])
            data = {'status': 8}
            headers = {
                                'content-type': 'application/json',
                                'Authorization': 'Token ' + get_token()
                            }
            requests.patch(url, data=json.dumps(data), headers=headers)
            print("order moved to sent")

            logger.info("Order completed successfully")

        except Exception:
            # self.logger.exception("Error inside complete_order")
            d.save_screenshot("/ap/logs/complete_order_error.png")
            raise


    # ==============================
    # PROCESS ORDER
    # ==============================

    def process_order(self, order):
        file_path = None
        try:
            print("in process order ")
            client_ref = order[0]

            if not self.open_order_from_queue(client_ref):
                return

            self.accept_order_if_needed()

          
            head, tail = os.path.split(order[1])

            logger.info(f"Downloading {order[1]}")

            file_path = os.path.join(get_download_dir(), tail)

            with requests.get(order[1], stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            

            fill_result = self.fill_order(order, file_path)
            if fill_result is False:
                self.remove_pdf(file_path)
                return 
            self.complete_order(order)
            self.remove_pdf(file_path)

        except Exception:
            logger.exception(f"Error processing order #{order[0]}")
            self.quit()
            raise

    def remove_pdf(self,file_path):
            
        if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed file {file_path}")
        else:
            logger.info("pdf already removed")


    def search_order(self):
        for order in self.orders:
            try:
                logger.info(f"\nProcessing {order[0]}")
                self.process_order(order)
            except Exception:
                self.quit()
                raise

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            logger.exception("Error quitting driver:")
            pass
