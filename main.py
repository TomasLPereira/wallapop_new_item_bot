import threading
import time

import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from winotify import Notification, audio

from Item import Item

stop_threads = threading.Event()


def acceptCookies(driver):
    WebDriverWait(driver, timeout=40).until(lambda d: d.find_element(By.ID, "onetrust-accept-btn-handler"))

    cookiesAcpt = driver.find_element(By.ID, "onetrust-accept-btn-handler")
    cookiesAcpt.click()


def skipHelp(driver):
    for i in range(0, 3):
        WebDriverWait(driver, timeout=40).until(lambda d: d.find_element(By.CLASS_NAME, "TooltipWrapper__skip"))
        driver.find_element(By.CLASS_NAME, "TooltipWrapper__skip").click()


def startupData(link, driver):
    try:
        driver.get(link)
        acceptCookies(driver)
        skipHelp(driver)
        WebDriverWait(driver, timeout=40).until(lambda d: d.find_element(By.CLASS_NAME, "ItemCardList__item"))

        return getData(driver)

    except requests.exceptions.ConnectionError:
        print("No connection")


def getData(driver):
    # Scroll to load all items

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for new items to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    time.sleep(2)
    allItems = driver.find_elements(By.CLASS_NAME, "ItemCardList__item")
    print("Found: " + str(len(allItems)))

    itemNames = []
    itemPrices = []

    for item in allItems:
        try:
            itemNames.append(item.find_element(By.CLASS_NAME, "ItemCard__title"))
            itemPrices.append(item.find_element(By.CLASS_NAME, "ItemCard__price"))
        except Exception as e:
            print(f"Error retrieving item details: {e}")
            continue

    gotItems = []
    for i, name in enumerate(itemNames):
        itemPrice = itemPrices[i].text
        gotItems.append(Item(name.text, itemPrice))

    return gotItems


def refreshData(driver):
    driver.refresh()
    WebDriverWait(driver, timeout=40).until(lambda d: d.find_element(By.CLASS_NAME, "ItemCardList__item"))

    gotItems = getData(driver)

    for item in gotItems:
        print("Name: " + item.name)
        print("Price: " + item.price)

    print("\n---------------------------------\n")

    return gotItems


# Driver config

def start(link):
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    mainDriver = webdriver.Chrome(options=options)

    items = startupData(link, mainDriver)  # First request

    while True:
        time.sleep(6)  # Time between requests

        newItems = refreshData(mainDriver)

        notifItems = [item for item in newItems if item not in items]

        print("\n---------------------------------\n")
        print(notifItems)
        print("\n---------------------------------\n")

        for item in notifItems:
            # Notification config
            notif = Notification(app_id="Wallapop Alert",
                                 title="New item",
                                 msg=f"Item: {item.name}\nPrice: {item.price}",
                                 duration="short")

            notif.set_audio(audio.SMS, loop=False)
            notif.show()

        items = newItems

    input()


if __name__ == "__main__":
    links = input("Input links separated by commas: ").split(',')
    threads = []

    for link in links:
        thread = threading.Thread(target=start, args=(link,))
        threads.append(thread)
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing...")
        stop_threads.set()

    for thread in threads:
        thread.join()
