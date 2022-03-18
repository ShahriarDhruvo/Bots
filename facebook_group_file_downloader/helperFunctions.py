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
    sort_by,
    secrets,
    timeout,
    encoding,
    target_file_type,
    log_file_location,
    normalization_form,
    explicit_wait_time,
    tracker_file_location,
    partially_downloaded_file_ext,
)


def waitNSeconds(sleep_time=1):
    """
    WARNING
    -------
    Sleep is essential because if we run it too quickly, Facebook will detect the Bot and block this account.

    """
    time.sleep(sleep_time)


def initializeWebDriver():
    # Keep the focus on the main window: Ignores all alerts from the webpage
    options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)

    # Tested on Windows & Linux
    if platform.system() == "Windows":
        service = Service(secrets[3])
        driver = webdriver.Chrome(service=service, options=options)
    elif platform.system() == "Linux":
        driver = webdriver.Chrome("chromedriver", options=options)

    # Explicit Waits: Wait until the element is ready
    web_driver_wait = WebDriverWait(driver, explicit_wait_time)

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
    username.send_keys(secrets[0])
    password.clear()
    password.send_keys(secrets[1])

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
    return unicodedata.normalize(normalization_form, data)


def getExistingFilesInfo():
    with open(tracker_file_location, "r", encoding=encoding) as f:
        registered_file_list = []

        try:
            infos = json.load(f)["files"]

            for info in infos:
                registered_file_list.append(
                    {
                        "post_id": normalizeData(info["post_id"]),
                        "name": normalizeData(info["name"]),
                        "uploaded_date": normalizeData(info["uploaded_date"]),
                    }
                )

            registered_file_list = sorted(
                registered_file_list, key=lambda x: x[sort_by]
            )

        except JSONDecodeError:
            pass

    # Already downloaded file's name in the download directory
    downloaded_file_list = sorted(
        normalizeData(os.path.basename(f))
        for f in glob.glob(secrets[2] + "/*." + target_file_type)
    )

    return downloaded_file_list, registered_file_list


def appendFilesInfo(res):
    """
    We can make this function more efficient by not copying the entire file every time,
    but rather just adding the information at the end of the file (with less prettier mode and doing minimization)

    """
    with open(tracker_file_location, "r+", encoding=encoding) as f:
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
    with open(log_file_location, "a", encoding=encoding) as f:
        f.write(text + "\n")


def compareData(s1, s2):
    """
    Note
    ----
    1. You do not need to normalize the string here because it should be normalized before passing to this function or else it will produce
    unexpected results when strings are compared(>, <) in the searchFile() and it will also help with performance because you will not need to
    normalize in every check.

    2. Removing whitespace from the string before comparing because when the file is saved on the machine
    It appears to add whitespaces after '-', and there may be other things like this.

    """
    # remove = string.punctuation + string.whitespace
    remove = string.whitespace
    mapping = {ord(c): None for c in remove}

    return s1.translate(mapping) == s2.translate(mapping)


def lowerBound(match_item, itemList, key):
    left = 0
    right = len(itemList) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if itemList[mid][key] >= match_item[key]:
            right = mid - 1
        else:
            left = mid + 1

    return left


def upperBound(match_item, itemList, key):
    left = 0
    right = len(itemList) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if itemList[mid][key] > match_item[key]:
            right = mid - 1
        else:
            left = mid + 1

    return left


def searchFile(match_item, itemList, multipleCheck=False):
    if multipleCheck:
        # Finding left and right most position of the matched item by binary search
        left = lowerBound(match_item, itemList, sort_by)
        right = upperBound(match_item, itemList, sort_by)

        if left == right:
            return -1

        # Linear Search between the left and right most position of the matched item
        for idx in range(left, right):
            c1 = match_item["post_id"] == itemList[idx]["post_id"]
            c2 = compareData(match_item["name"], itemList[idx]["name"])
            c3 = compareData(
                match_item["uploaded_date"], itemList[idx]["uploaded_date"]
            )
            if c1 and c2 and c3:
                return idx

    else:
        # Binary Search
        left = 0
        right = len(itemList) - 1

        while left <= right:
            mid = left + (right - left) // 2

            if compareData(itemList[mid], match_item):
                return mid

            # For these kind of comparison we need to normalize the data beforehand
            elif itemList[mid] > match_item:
                right = mid - 1
            else:
                left = mid + 1

    return -1


def checkDownloadStatus(
    _post_id, _name, _date, downloaded_file_list, registered_file_list
):
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
    if not registered_file_list or not downloaded_file_list:
        return False, True

    registered_file_index = searchFile(
        {"post_id": _post_id, "name": _name, "uploaded_date": _date},
        registered_file_list,
        True,
    )

    # Scenarios: 2
    # if not registered_file_index: # because index can be 0
    if registered_file_index == -1:
        return False, True

    downloaded_file_index = searchFile(_name, downloaded_file_list)

    # Scenarios: 3
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

    # Prevent it from opening into a new tab
    driver.execute_script("arguments[0].target='_self';", download_button)

    waitNSeconds(0.5)

    driver.execute_script("arguments[0].click();", download_button)

    return files_count + 1  # Keeping track of the downloaded files


def loadMoreFiles(driver, files_to_load, identifier, timeout=timeout, n_scroll=1):
    """
    Scroll down to load more files
    -> do this operation(scroll to load) for n times

    """
    for _ in range(n_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time_elapsed = 0
        current_len = len(files_to_load[0])

        """
        1. If the first one is loaded then all others will surely get loaded so you don't have to check the whole length of 'files_to_load' array but
           if you want you can do something like this ->
            
           current_len = sum(len(i) for i in files_to_load)

        
        2. Wait 'timeout=30 minutes' before determining that there is no more files to load

        3. Computation here gets much more expensive as more and more data loads so it is not viable to do this check every second hence 5s interval
        
        """
        while time_elapsed < timeout:
            start_time = time.time()
            waitNSeconds(5)

            # By doing this we don't need to check if every single data is loaded or not everytime hence saving computational power
            first_data = driver.find_elements(By.XPATH, identifier[0])

            if current_len < len(first_data):
                files_to_load[0].extend(
                    [
                        element
                        for element in first_data
                        if element not in files_to_load[0]
                    ]
                )

                for idx in range(1, len(files_to_load)):
                    files_to_load[idx].extend(
                        [
                            element
                            for element in driver.find_elements(
                                By.XPATH, identifier[idx]
                            )
                            if element not in files_to_load[idx]
                        ]
                    )

                break

            time_elapsed += time.time() - start_time

    return files_to_load


def waitToFinishDownload(directory, nfiles=None, timeout=timeout):
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

    while dl_wait and time_elapsed < timeout:
        start_time = time.time()
        waitNSeconds(0.5)  # check every 0.5s

        dl_wait = False
        files = os.listdir(directory)

        if nfiles and len(files) != nfiles:
            dl_wait = True

        # Checking for any partially donwloaded file
        if not dl_wait:
            for fname in files:
                if fname.endswith(partially_downloaded_file_ext):
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
            "\nThe download was successful. Continuing after {}s... 🥳".format(
                time_elapsed
            )
        )

    return time_elapsed
