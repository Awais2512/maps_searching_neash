from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options 
import time
import csv
import os
# # Setup the driver and navigate to the page
file_dir = 'map_files'

def get_driver():
    options = Options()
    options.add_argument("--headless") 
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)
    return driver

def save_to_csv(filename, items:list):
    """
    Save data to a CSV file. If the file exists, append the data. If not, create the file and add the data.

    :param filename: Name of the CSV file (e.g., 'neash_in_country.csv')
    :param items: List of lists, where each inner list represents a row of data
    """
    # Check if the file exists

    file_path = os.path.join(file_dir,filename)
    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row if the file is being created
        if not file_exists:
            writer.writerow(['Title', 'Rating', 'Address', 'Directions', 'Contact', "Web Link"])
        
        # Write the data rows
        writer.writerow(items)

def map_search(neash, country , limit: int=100):

    print(f'--------searching for the {neash} in {country}--------')
    driver = get_driver()

    driver.get('https://www.google.com/maps/@31.4971628,74.440827,15z?entry=ttu')  # Replace this with the actual URL

    #  Perform a search
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "searchboxinput"))
    )
    search_box.send_keys(f'{neash} in {country}')
    search_box.send_keys(Keys.RETURN)

    # Wait for the results to be clickable
    try:
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'hfpxzc'))
        )
    except TimeoutException:
        print("Timed out waiting for search results to load.")
        driver.quit()
    # Wait for the element to be present
    results_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]'))
    )

    current_scroll = 1
    last_height = driver.execute_script("return arguments[0].scrollHeight", results_container)
    result_list = []
    retry_count = 0
    while len(result_list)<=limit:
        results = results_container.find_elements(By.CLASS_NAME,'hfpxzc')
        print("*"*80)
        print('Total found results',len(results))
        print("*"*80)
        # Extract business elements within the container
        for result in results:
            if result not in result_list:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", result)
                    result_list.append(result)
                    title = result.get_attribute('aria-label').strip()
                    direction = result.get_attribute('href')
                    
                    result.click()

                    try:
                        rate = driver.find_element(By.CSS_SELECTOR,'div[class="F7nice "]').text.strip()
                    except Exception as e:
                        rate =  None
                        
                    try:
                        address = driver.find_element(By.CSS_SELECTOR,'button[class="CsEnBe"][data-item-id="address"]').text.strip()
                    except Exception as e:
                        address= None

                    try:
                        contact = driver.find_element(By.CSS_SELECTOR,'button[class="CsEnBe"][data-tooltip="Copy phone number"]').text.strip()
                    except Exception as e:  
                        contact = None
                    try:
                        web_link = driver.find_element(By.CSS_SELECTOR,'a[class="CsEnBe"][data-item-id="authority"]').get_attribute('href')
                    except:
                        try:
                            web_link = driver.find_element(By.CSS_SELECTOR,'a[class="CsEnBe"][data-tooltip="Open booking link"]').get_attribute('href')
                        except:
                            web_link = None

                    print('Title:',title)
                    print("rating:",rate)
                    print('directions:',direction)
                    print('address:',address)
                    print('contact:',contact)
                    print("Web link:",web_link)
                    print("-"*50)
                    if contact!= None:
                        filename = f'{neash}_in_{country}.csv'
                        items = [title, rate, address, direction, contact, web_link]
                        # saving to csv file  
                        save_to_csv(filename,items)

                        # time.sleep(2)
                except:
                    time.sleep(2)
        # driver.find_element(By.CSS_SELECTOR,'button[class="VfPpkd-icon-LgbsSe yHy1rc eT1oJ mN1ivc"][aria-label="Close"]')
        print('Total new results found:',len(result_list))
        # Scroll down to the bottom of the element
        time.sleep(2)
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_container)

        print(f"Scrolled {current_scroll} times")
        # Wait for new elements to load
        current_scroll+=1
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return arguments[0].scrollHeight", results_container)
        if new_height == last_height:
            retry_count += 1
            print(f"No new content loaded. Retry attempt: {retry_count}")
            if retry_count >= 3:  # Break after 3 retries
                print('Scroll limit completed after 3 retries')
                print("Total results found finally:", len(result_list))
                break
            time.sleep(2)  # Wait for 2 seconds before retrying
        else:
            retry_count = 0  # Reset retry counter if new content is loaded

        last_height = new_height
    driver.quit()


neashes = [
        # "Surgeon", 'Dermatologist',  "Lawyer", "Anaesthesiologist",
        # "Paediatrician", "Ophthalmologist", 
        "Radiologist"
           ]

for neash in neashes:
    country = 'california'
    try:
        map_search(neash,country)
    except Exception as e:
        print("Error:",e)