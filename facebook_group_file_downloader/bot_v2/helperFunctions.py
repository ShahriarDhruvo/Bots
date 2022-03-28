import os
import time
import glob
import json
import string
import platform
import unicodedata
from selenium import webdriver
from json.decoder import JSONDecodeError
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from constants import (
    SECRETS,
    TIMEOUT,
    ENCODING,
    TARGET_FILE_TYPE,
    LOG_FILE_LOCATION,
    DOWNLOAD_DIRECTORY,
    NORMALIZATION_FORM,
    EXPLICIT_WAIT_TIME,
    TRACKER_FILE_LOCATION,
    SHOULD_CHECK_LOCAL_FILES,
    PARTIALLY_DOWNLOADED_FILE_EXT,
)


ordinal = lambda n: "%d%s" % (
    n,
    "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
)

# Scroll down N times to load (N * 15) files
def scrollNTimes(driver, scroll_count=1, n_scroll=35, timeout=TIMEOUT):
    time_elapsed = 0

    for _ in range(n_scroll):
        end_time = 0
        new_height = 0
        start_time = time.time()
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        while (last_height >= new_height) and (end_time <= timeout):
            waitNSeconds(3)  # Otherwise your account will surely get blocked
            new_height = driver.execute_script("return document.body.scrollHeight")

            end_time = time.time() - start_time

        time_elapsed += end_time
        updateLog(
            "{} scroll took {}s".format(ordinal(scroll_count), round(end_time, 2))
        )

        scroll_count += 1

        if end_time > timeout:
            updateLog("\nTIMEOUT: May be it's the end of the list!")
            break

    updateLog("\nTotal loading time {}s".format(round(time_elapsed, 2)))

    return scroll_count


def waitNSeconds(sleep_time=1):
    """
    WARNING
    -------
    Sleep is essential because if we run it too quickly, Facebook will detect the Bot and block this account.

    """
    time.sleep(sleep_time)


def initializeWebDriver():
    """
    Options
    -------
    1. Set the browser's default download location
    2. Ignores all alerts from the webpage
    3. Set automatically download multiple files option to True

    """
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOAD_DIRECTORY,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)

    # Tested on Windows & Linux
    if platform.system() == "Windows":
        service = Service(SECRETS[2])
        driver = webdriver.Chrome(service=service, options=options)
    elif platform.system() == "Linux":
        driver = webdriver.Chrome("chromedriver", options=options)

    # Explicit Waits: Wait until the element is ready
    web_driver_wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)

    return driver, web_driver_wait


def login(driver, web_driver_wait):
    driver.get("http://www.facebook.com")

    # Target credential's input field
    username = web_driver_wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']"))
    )
    password = web_driver_wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']"))
    )

    # Enter username and password
    username.clear()
    username.send_keys(SECRETS[0])
    password.clear()
    password.send_keys(SECRETS[1])

    # Target submit button
    SubmitButton = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )

    SubmitButton.click()


def initializeWebpage(driver, url):
    waitNSeconds(2)
    driver.get(url)

    """
    As you scroll through the webpage the content will no longer appear sorted
    so there is no merit in sorting the files by name/date/type or whatever
    
    If you still want to try this then you can use the code below

    Code
    ----
    sortButtons_xpath = "//div[@class='l9j0dhe7 du4w35lb j83agx80 pfnyh3mw taijpn5t bp9cbjyn owycx6da btwxx1t3 kt9q3ron ak7q8e6j isp2s0ed ri5dt5u2 rt8b4zig n8ej3o3l agehan2d sk4xxmp2 rq0escxv d1544ag0 tw6a2znq tdjehn4e tv7at329']" # find 3 per-scroll

    sortButtons = web_driver_wait.until(
        EC.presence_of_all_elements_located((By.XPATH, sortButtons_xpath))
    )

    # [1]: Sort by file_type (PDF at the top in my case)
    driver.execute_script("arguments[0].click();", sortButtons[1])

    """


def normalizeData(data):
    return unicodedata.normalize(NORMALIZATION_FORM, data)


def getExistingFilesInfo():
    with open(TRACKER_FILE_LOCATION, "r", encoding=ENCODING) as f:
        registered_file_list = []

        try:
            infos = json.load(f)["files"]

            for info in infos:
                """
                Normalizing here because the data is now coming from a UTF-8 encoded file

                Note
                ----
                Only combining post_id and name because you can only attach one pdf file with a post

                """
                registered_file_list.append(
                    transformData(
                        [
                            info["post_id"],
                            normalizeData(info["name"]),
                        ]
                    )
                )

            registered_file_list.sort()  # To perform binarySearch later

        except JSONDecodeError:
            pass

    # Already downloaded file's name in the download directory
    if SHOULD_CHECK_LOCAL_FILES:
        downloaded_file_list = sorted(
            transformData([os.path.basename(f)])  # Must pass a list as a parameter
            for f in glob.glob(DOWNLOAD_DIRECTORY + "*." + TARGET_FILE_TYPE)
        )
    else:
        downloaded_file_list = []

    return downloaded_file_list, registered_file_list


def appendFilesInfo(res):
    """
    We can make this function more efficient by not copying the entire file every time,
    but rather just adding the information at the end of the file (with less prettier mode and doing minimization)

    """
    with open(TRACKER_FILE_LOCATION, "r+", encoding=ENCODING) as f:
        try:
            data = json.load(f)
            data["files"].append(res)

            # Sets pointer's current position at the begining of the file
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)

            data.clear()
        except JSONDecodeError:
            # As initially the file is empty
            data = {"files": [res]}
            json.dump(data, f, indent=4, ensure_ascii=False)


def updateLog(text):
    print(text)  # Unnecessary but why not 😉
    with open(LOG_FILE_LOCATION, "a", encoding=ENCODING) as f:
        f.write(text + "\n")


def transformData(dataList):  # The parameter has to be a LIST
    res = ""

    for data in dataList:
        res += str(data)

    """
    Note
    ----
    1. Removing whitespace from the string before comparing because when the file is saved on the machine
    It appears to add whitespaces after '-', and there may be other things like this.

    2. Normalizing here because this function have to accept normalized/scattered data

    """
    # remove = string.punctuation + string.whitespace
    remove = string.whitespace
    mapping = {ord(c): None for c in remove}

    res = res.translate(mapping)

    return normalizeData(res)


def binarySearch(match_item, itemList):
    """
    match_item and itemList's data should always be on their normalized form

    """
    left = 0
    right = len(itemList) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if itemList[mid] == match_item:
            return mid

        # For these kind of comparison we need to normalize the data beforehand
        elif itemList[mid] > match_item:
            right = mid - 1
        else:
            left = mid + 1

    return -1


def checkDownloadStatus(_post_id, _name, downloaded_file_list, registered_file_list):
    """
    Check If the requested file has already been downloaded or not

    Return Value
    ------------
    First -> Should it download the requested file or not
    Second -> Should it update information in the traker file or not


    Scenarios
    ---------
    1. If either tracker file or download directory is empty then there was no previous attempt to download these files in this case all files
    should be downloaded
    -> return False, True

    2. If the file is not present in the tracker file (registered files.json), it means that the file that was requested to download was not
    downloaded previously.
    -> return False, True

    3. If the file is not in the download directory but has already been added to the tracker file (registered files.json), it was not downloaded
    properly previously.
    -> return False, False

    4. If the file exist both in tracker file (registered_files.json) & in the download directory then the file has been downloaded succesfully
    -> return True, False

    5. File is present in the download directory but there is no log for that file in registered_files.json
    -> return True, True (Didn't handle because you can't tell if the downloaded file is the requested one just by looking at the file name)

    Note
    ----
    1. Once all files have been checked, this should no longer be checked because there may be multiple files with the same name (on the website)
    that should all be downloaded. Removing the discovered file so that a file with the same name can be downloaded later

    2. If the file is found in the tracker file and you want to check if it really exists in the download directory, you cannot delete the data from
    this list because if two files have the same name, deleting the first one prevents the second one with '(1)' at the end from being checked and
    downloaded. And, yes, we miss the duplicate uploaded files this way, but we have to make some choices here. At the very least, the Bot downloads
    non-duplicate files that were not previously downloaded. So you can't do this ->

    downloaded_file_list.pop(downloaded_file_index)

    """

    # Scenarios: 1
    if not registered_file_list or (
        not downloaded_file_list and SHOULD_CHECK_LOCAL_FILES
    ):
        return False, True

    registered_file_index = binarySearch(
        transformData([_post_id, _name]),
        registered_file_list,
    )

    # Scenarios: 2
    # if not registered_file_index: # because index can be 0
    if registered_file_index == -1:
        return False, True

    # Scenarios: 3
    if SHOULD_CHECK_LOCAL_FILES:
        downloaded_file_index = binarySearch(
            transformData([_name]), downloaded_file_list
        )

        if registered_file_index and downloaded_file_index == -1:
            updateLog(
                "\n*** The information is in the tracker-file, but the file is not in the download directory. Downloading... ***"
            )
            return False, False

    registered_file_list.pop(registered_file_index)

    # Scenarios: 4
    return True, False


def downloadFile(driver, web_driver_wait, xpath, files_count):
    download_button = web_driver_wait.until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )

    """
    We can't afford to have the page of a loaded file redirected, so it is here  in order to be extra cautious

    """
    driver.execute_script("arguments[0].target='_blank';", download_button)

    waitNSeconds(1)

    driver.execute_script("arguments[0].click();", download_button)

    return files_count + 1  # Keeping track of the downloaded files


def insertFoundFiles(driver, files_to_load, identifier):
    for idx in range(len(files_to_load)):
        files_to_load[idx].extend(
            [
                element
                for element in driver.find_elements(By.XPATH, identifier[idx])
                if element not in files_to_load[idx]
            ]
        )

    return files_to_load


def waitToFinishDownload(directory, nfiles=None, timeout=TIMEOUT):
    """
    Args
    ----
    directory: str
        The path to the folder where the files will be downloaded.
    timeout: int
        How many time_elapsed until it stops waiting.
    nfiles: int, defaults to None
        If provided, also wait for the expected number of files.

    """

    dl_wait = True
    time_elapsed = 0

    while dl_wait and time_elapsed <= timeout:
        start_time = time.time()
        waitNSeconds(0.5)  # check every 0.5s

        dl_wait = False
        files = os.listdir(directory)

        if nfiles and len(files) != nfiles:
            dl_wait = True

        # Checking for any partially donwloaded file
        if not dl_wait:
            for fname in files:
                if fname.endswith(PARTIALLY_DOWNLOADED_FILE_EXT):
                    dl_wait = True
                    break

        time_elapsed += time.time() - start_time

    if time_elapsed >= timeout:
        time_elapsed = -1
        updateLog(
            "\nYour connection is either too slow or you are not connected at all! Please try again later. I'm going to disconnect..."
        )
    else:
        updateLog(
            "\nSuccessfully downloaded. Continuing after {}s... 🥳".format(
                round(time_elapsed, 2)
            )
        )

    return time_elapsed
