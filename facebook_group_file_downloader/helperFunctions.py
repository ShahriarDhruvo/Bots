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
)


def waitNSeconds(sleep_time=1):
    """
    WARNING
    -------
    Sleep is important because if we run it too fast then
    facebook will detect the Bot and block this account

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
    wait = WebDriverWait(driver, explicit_wait_time)

    return driver, wait


def login(driver, wait):
    driver.get("http://www.facebook.com")

    # Target credential's input field
    username = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']"))
    )
    password = wait.until(
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

    """
    You should be logged in by now!
    
    Note
    ----
    if you have 2fa on for this account then you have to authorize it and then run the remaining code manually
    
    """


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

    sortButtons = wait.until(
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

        except JSONDecodeError:
            pass

    registered_file_list = sorted(registered_file_list, key=lambda x: x[sort_by])

    # Already downloaded file's name in the download directory
    downloaded_file_list = sorted(
        normalizeData(os.path.basename(f))
        for f in glob.glob(secrets[2] + "/*." + target_file_type)
    )

    return downloaded_file_list, registered_file_list


def appendFilesInfo(res):
    """
    We can make this function more efficient by not copyting the whole file again and again everytime
    but just adding those info at the end of the file (with less prettier mode and doing minimization)

    """
    with open(tracker_file_location, "r+", encoding=encoding) as f:
        try:
            data = json.load(f)
            data["files"].append(res)

            # Sets file's current position at the begining.
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)

            data.clear()
        except JSONDecodeError:
            # If the file is empty initially
            data = {"files": [res]}
            json.dump(data, f, indent=4, ensure_ascii=False)


def updateLog(text):
    print(text)  # Unnecessary but why not :3
    with open(log_file_location, "a", encoding=encoding) as f:
        f.write(text + "\n")


def compareData(s1, s2):
    """
    Note
    ----
    1. You donot need to normalize the string here because it should be normalized before passing to this function
    or this will generate unexpected results when strings are compared(>, <) in the binarySearch()
    and it will help with the performance too as you don't need to normalize in every check

    2. Removing whitespace in the string before comparing because when file saves in the machine
    it seems to add whitepsaces after '-' and there can also be some other things like this

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

    Scenarios
    ---------
    1. If either tracker file or download directory is empty then there was no previous
    attempt to download these files in this case all files should be downloaded
    -> return False

    2. If the file is not present in the tracker file(registered_files.json) then the file that
    has been requested to download didn't get to download previously
    -> return False

    3. If the file is not present in the download directory but has already been
    added to tracker file(registered_files.json) then it was not downloaded properly
    -> return False

    4. If the file exist both in tracker file(registered_files.json) & in the download directory
    then the file has been downloaded
    -> return True

    5. File present in the download directory but there is no log for that file in registered_files.json
    -> this shouldn't happen in any situation

    6. All files has been checked once then this shouldn't be checked anymore because there can be
    multiple files with the same name(in the website) and they all should be downloaded
    remove the found file so that the file with same name can be downloaded later on


    Return Value
    ------------
    First -> Should it download the requested file or not
    Second -> Should it update traker file or not

    """

    if not registered_file_list or not downloaded_file_list:
        return False, True

    registered_file_index = searchFile(
        {"post_id": _post_id, "name": _name, "uploaded_date": _date},
        registered_file_list,
        True,
    )

    # if not registered_file_index: # because index can be 0
    if registered_file_index == -1:
        return False, True

    downloaded_file_index = searchFile(_name, downloaded_file_list)

    # Turned off for duplicate file download
    # if registered_file_index and downloaded_file_index == -1:
    #     updateLog(
    #         "\n*** Info does exist in the tracker-file but file doesn't exist in the download directory ***"
    #     )
    #     return False, False

    registered_file_list.pop(registered_file_index)
    downloaded_file_list.pop(downloaded_file_index)

    return True, True


def downloadFile(driver, wait, xpath, files_count):
    download_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    # Prevent it from opening into a new tab
    driver.execute_script("arguments[0].target='_self';", download_button)

    waitNSeconds(0.5)

    driver.execute_script("arguments[0].click();", download_button)

    return files_count + 1  # Keeping track of the downloaded files


def loadMoreFiles(driver, files_to_load, identifier, timeout=timeout, n_scroll=1):
    """
    Scroll down to load more files
    wait 'timeout=10 minutes' before determining that there is no more files to load

    """
    for _ in range(n_scroll):  # do this operation (scroll to load) n times
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time_elapsed = 0
        current_len = len(files_to_load[0])

        """
        If the first one is loaded then all others will surely get loaded
        so you don't have to check the whole length of 'files_to_load' array
        but if you want you can do something like this ->
        current_len = sum(len(i) for i in files_to_load)
        
        """
        while (current_len >= len(files_to_load[0])) and time_elapsed < timeout:
            waitNSeconds(1)

            # Iterate through all the files that are needed to be loaded
            for idx, _ in enumerate(files_to_load):
                files_to_load[idx].extend(
                    [
                        element
                        for element in driver.find_elements(By.XPATH, identifier[idx])
                        if element not in files_to_load[idx]
                    ]
                )

            time_elapsed += 1

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
        waitNSeconds(0.5)  # check every 0.5s

        dl_wait = False
        files = os.listdir(directory)

        if nfiles and len(files) != nfiles:
            dl_wait = True

        # As partial downloaded files will be of ".crdownload" extension for chromium based browsers
        if not dl_wait:
            for fname in files:
                if fname.endswith(".crdownload"):
                    dl_wait = True
                    break

        time_elapsed += 0.5

    if time_elapsed >= timeout:
        time_elapsed = -1
        updateLog(
            "\nYour connection is too slow or you are not connected! Try again later. Closing the connection..."
        )
    else:
        updateLog(
            "\nSuccessfully downloaded. Continuing after {}s... 🥳".format(time_elapsed)
        )

    return time_elapsed


################ DEPRICATED ###########################
# def binarySearch(item, itemList, multipleCheck=False):
#     left = 0
#     right = len(itemList) - 1

#     while left <= right:
#         mid = left + (right - left) // 2

#         if multipleCheck:
#             """
#             Sorted By: uploaded date

#             If permalink exist for the file then check:
#                 0 uploaded date
#                 1 permalink of the post
#                 2 file name
#             If not then check:
#                 0 uploaded date
#                 2 file name

#             """
#             if itemList[mid][1]:
#                 if (
#                     compareString(itemList[mid][0], item[0])
#                     and itemList[mid][1] == item[1]
#                     and compareString(itemList[mid][2], item[2])
#                 ):
#                     return mid
#                 elif itemList[mid][0] > item[0]:
#                     right = mid - 1
#                 else:
#                     left = mid + 1
#             else:
#                 if compareString(itemList[mid][0], item[0]) and compareString(
#                     itemList[mid][2], item[2]
#                 ):
#                     return mid
#                 elif itemList[mid][0] > item[0]:
#                     right = mid - 1
#                 else:
#                     left = mid + 1
#         else:
#             if compareString(itemList[mid], item):
#                 return mid
#             elif itemList[mid] > item:
#                 right = mid - 1
#             else:
#                 left = mid + 1

#     return -1
