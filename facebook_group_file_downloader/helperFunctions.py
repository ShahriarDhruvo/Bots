import os
import math
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


from constantsAndVariables import (
    secrets,
    encoding,
    target_file_type,
    log_file_location,
    explicit_wait_time,
    tracker_file_location,
    network_failure_timeout,
)

#########################################################
# sleep is important because if we scrape too fast then #
# facebook will detect the bot and block this account   #
#########################################################
def waitNSeconds(sleep_time=1):
    time.sleep(sleep_time)


def initializeWebDriver():
    # Ignore all alerts from the webpage
    options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)

    # Tested on Windows & Linux
    if platform.system() == "Windows":
        service = Service(secrets[3])
        driver = webdriver.Chrome(service=service, options=options)
    elif platform.system() == "Linux":
        driver = webdriver.Chrome("chromedriver", options=options)

    wait = WebDriverWait(
        driver, explicit_wait_time
    )  # to wait until the element is ready -> Explicit Waits

    return driver, wait


def login(driver, wait):
    # open the webpage
    driver.get("http://www.facebook.com")

    # target credentials
    username = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']"))
    )
    password = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass']"))
    )

    # enter username and password
    username.clear()
    username.send_keys(secrets[0])
    password.clear()
    password.send_keys(secrets[1])

    # target thesrc login button and click it
    SubmitButton = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )

    SubmitButton.click()

    """ After this you should be logged in! -> if you have 2fa then you have to authorize it manually and then run the remaining cells manually """


def initializeWebpage(driver, url):
    waitNSeconds(2)
    driver.get(url)

    ###########################################################
    # NOT NEEDED -> as it doesn't sort by file type reliably 😑
    ###########################################################
    # sortButtons_xpath = "//div[@class='l9j0dhe7 du4w35lb j83agx80 pfnyh3mw taijpn5t bp9cbjyn owycx6da btwxx1t3 kt9q3ron ak7q8e6j isp2s0ed ri5dt5u2 rt8b4zig n8ej3o3l agehan2d sk4xxmp2 rq0escxv d1544ag0 tw6a2znq tdjehn4e tv7at329']" # find 3 per-scroll

    # sortButtons = wait.until(
    #     EC.presence_of_all_elements_located((By.XPATH, sortButtons_xpath))
    # )

    # # sort by file_type (PDF at the top in my case)
    # driver.execute_script("arguments[0].click();", sortButtons[1])


def compareString(s1, s2):
    # To avoid comparison between different unicode char
    s1 = unicodedata.normalize("NFC", s1)
    s2 = unicodedata.normalize("NFC", s2)

    # Removing whitespace in the string before comparing
    # because when file saves in the machine it seems to add whitepsaces after '-'
    # remove = string.punctuation + string.whitespace
    remove = string.whitespace
    mapping = {ord(c): None for c in remove}

    return s1.translate(mapping) == s2.translate(mapping)


def getExistingFilesInfo():
    with open(tracker_file_location, "r", encoding=encoding) as f:
        try:
            files_info = json.load(f)["files"]
        except JSONDecodeError:
            files_info = []

    # already downloaded file's name in download directory
    downloaded_files = sorted(
        [os.path.basename(f) for f in glob.glob(secrets[2] + "/*." + target_file_type)]
    )

    # files that are registered in files_info.json
    tracked_files = sorted(
        [
            [
                info["post_permalink"] if "post_permalink" in info else False,
                info["uploaded_date"],
                info["name"],
            ]
            for info in files_info
        ]
    )

    return downloaded_files, tracked_files


def appendFilesInfo(res):
    with open(tracker_file_location, "r+", encoding=encoding) as f:
        try:
            data = json.load(f)
            data["files"].append(res)

            # Sets file's current position at offset.
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


def binarySearch(item, itemList, multipleCheck=False):
    left = 0
    right = len(itemList) - 1

    while left <= right:
        mid = math.floor(left + (right - left) / 2)

        if multipleCheck:
            """
            If permalink exist for the file then check:
                permalink of the post
                uploaded date
                file name
            If not then check:
                uploaded date
                file name

            """
            if (
                itemList[mid][0]
                and (
                    itemList[mid][0] == item[0]
                    and compareString(itemList[mid][1], item[1])
                    and compareString(itemList[mid][2], item[2])
                )
                or (
                    compareString(itemList[mid][1], item[1])
                    and compareString(itemList[mid][2], item[2])
                )
            ):
                return mid
            elif itemList[mid][0] > item[0]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if compareString(itemList[mid], item):
                return mid
            elif itemList[mid] > item:
                right = mid - 1
            else:
                left = mid + 1

    return -1


def isDownloaded(fileName, uploadDate, post_permalink, downloaded_files, tracked_files):
    """
    Check If the requested file has already been downloaded or not

    Scenarios
    ---------
    1. If either tracker file or download directory is empty then there was no previous
    attempt to download these files in this case all files should be downloaded
    -> return False

    2. If the file is not present in the tracker file(files_info.json) then the file that
    has been requested to download didn't get to download previously
    -> return False

    3. If the file is not present in the download directory but has already been
    added to tracker file(files_info.json) then it was not downloaded properly
    -> return False

    4. If the file exist both in tracker file(files_info.json) & in the download directory
    then the file has been downloaded
    -> return True

    5. File present in the download directory but there is no log for that file in files_info.json
    -> this shouldn't happen in any situation

    6. All files has been checked once then this shouldn't be checked anymore because there can be
    multiple files with the same name(in the website) and they all should be downloaded
    remove the found file so that the file with same name can be downloaded later on


    Return Value
    ------------
    First -> Should it download the requested file
    Second -> If the file should download then should it update it into the tracker file

    """

    if not downloaded_files or not tracked_files:
        return False, True

    downloadedFileIndex = binarySearch(fileName, downloaded_files)
    trackedFileIndex = binarySearch(
        (post_permalink, uploadDate, fileName), tracked_files, True
    )

    # if not trackedFileIndex: # because index can be 0
    if trackedFileIndex == -1:
        return False, True

    if trackedFileIndex and downloadedFileIndex == -1:
        return True, False

    tracked_files.pop(trackedFileIndex)
    downloaded_files.pop(downloadedFileIndex)

    return True, True


def downloadFile(driver, wait, cssSelector, files_count):
    download_button = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, cssSelector))
    )

    driver.execute_script(
        "arguments[0].target='_self';", download_button
    )  # to prevent it from opening into a new tab

    waitNSeconds(0.5)

    driver.execute_script("arguments[0].click();", download_button)

    return files_count + 1  # Keeping track of the downloaded files


###################################################################
# scroll down to load more files                                  #
# wait 60s before determining that there is no more files to load #
###################################################################
def loadMoreFiles(driver, files_to_load, identifier, timeout=60, n_scroll=1):
    for _ in range(n_scroll):  # do this operation(scroll to load) for n times
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time_elapsed = 0
        current_len = len(files_to_load[0])

        ########################################################################
        # If the first one is loaded then all others will surely get loaded    #
        # so you don't have to check the whole length of 'files_to_load' array #
        # but if you want you can do something like this ->                    #
        # current_len = sum(len(i) for i in files_to_load)                     #
        ########################################################################
        while (current_len >= len(files_to_load[0])) and time_elapsed < timeout:
            waitNSeconds(1)

            # iterate through all the files that are needed to be loaded
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


def waitToFinishDownload(directory, nfiles=None, timeout=network_failure_timeout):
    """
    Wait for downloads to finish with a specified timeout.

    Args
    ----
    directory : str
        The path to the folder where the files will be downloaded.
    timeout : int
        How many time_elapsed until it stops waiting.
    nfiles : int, defaults to None
        If provided, also wait for the expected number of files.

    """

    time_elapsed = 0
    dl_wait = True

    while dl_wait and time_elapsed < timeout:
        waitNSeconds(0.5)  # check every 0.5s

        dl_wait = False
        files = os.listdir(directory)

        # if nfiles and len(files) != nfiles:
        #     # if nfiles and len(files) < nfiles:
        #     dl_wait = True

        if not dl_wait:
            for fname in files:
                # as partial downloaded files will be of ".crdownload" extension for chromium based browsers
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
