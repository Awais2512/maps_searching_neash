from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import csv
from selenium.webdriver.firefox.options import Options 
# # Setup the driver and navigate to the page


def map_search(neash,country):
    print(f'--------searching for the {neash} in {country}--------')
    with open(f'{neash}_in_{country}.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(['Title', 'Rating', 'Address', 'Directions', 'Contact'])
    options = Options()
    options.add_argument("--headless") 
    driver = webdriver.Firefox(options=options)
    driver.get('https://www.google.com/maps/@31.4971628,74.440827,15z?entry=ttu')  # Replace this with the actual URL

    #  Perform a search
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Search Google Maps']"))
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
    time.sleep(5)
    results_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]'))
    )

    current_scroll = 1
    last_height = driver.execute_script("return arguments[0].scrollHeight", results_container)
    result_list = []
    # Scroll within the container
     # Set a limit on the number of scrolls to prevent infinite loops
    while True:
        results = results_container.find_elements(By.CLASS_NAME,'hfpxzc')
        print('Total found results',len(results))
        # Extract business elements within the container
        for result in results:
            if result not in result_list:
                try:
                    result_list.append(result)
                    title = result.get_attribute('aria-label')
                    direction = result.get_attribute('href')
                    

                    result.click()
                    try:
                        rate = driver.find_element(By.CSS_SELECTOR,'div[class="F7nice "]').text
                        
                    except Exception as e:
                        # rate = result.find_element(By.CSS_SELECTOR ,'div[class="W4Efsd"]')
                        rate =  'None'
                    try:
                        address = driver.find_element(By.CSS_SELECTOR,'button[class="CsEnBe"][data-item-id="address"]').find_element(By.CSS_SELECTOR,'div[class="AeaXub"]').find_element(By.CSS_SELECTOR,'div[class="Io6YTe fontBodyMedium kR99db "]').text
                    except Exception as e:
                        address= 'None'

                    try:
                        contact = driver.find_element(By.CSS_SELECTOR,'button[data-tooltip="Copy phone number"]').find_element(By.CSS_SELECTOR,'div[class="AeaXub"]').find_element(By.CSS_SELECTOR,'div[class="Io6YTe fontBodyMedium kR99db "]').text
                    except Exception as e:  
                        contact = 'None'

                    print('Title:',title)
                    print("rating:",rate)
                    print('address:',address)
                    print('directions:',direction)
                    print('contact:',contact)
                    if contact!= 'None':
                        with open(f'{neash}_in_{country}.csv', mode='a', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            # Write the header row
                            writer.writerow([title, rate, address, direction, contact])
                        time.sleep(2)
                except:
                    continue
        # driver.find_element(By.CSS_SELECTOR,'button[class="VfPpkd-icon-LgbsSe yHy1rc eT1oJ mN1ivc"][aria-label="Close"]')
        time.sleep(2)
        print('Total new results found:',len(result_list))
        # Scroll down to the bottom of the element
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_container)

        print(f"Scrolled {current_scroll} times")
        # Wait for new elements to load
        time.sleep(2)
        current_scroll+=1
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return arguments[0].scrollHeight", results_container)
        if new_height == last_height:
            print('scroll limit completed')
            print("Total result found finally",len(result_list))
            break  # Break the loop if no new content is loaded
        last_height = new_height

    time.sleep(5)
    driver.quit()


neashes = ['plumbers','electricians','gardeners','cleaners','mouers']


for neash in neashes:
    country = 'california'
    map_search(neash,country)