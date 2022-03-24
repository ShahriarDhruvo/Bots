TIMEOUT = 1800  # 30 minutes
ENCODING = "utf-8"
EXPLICIT_WAIT_TIME = 10
TARGET_FILE_TYPE = "pdf"
NORMALIZATION_FORM = "NFC"
LOG_FILE_LOCATION = "bot.log"
DOWNLOAD_DIRECTORY = "/mnt/762C61C32C617F4D/Download/Bangla-Books-Direct-Link"
FACEBOOK_GROUP_URL = "https://www.facebook.com/groups/blbookdl/files/"
# FACEBOOK_GROUP_URL = "https://www.facebook.com/groups/201623576939858/files/"

# Turn it off if you find it is causing duplicate files
SHOULD_CHECK_LOCAL_FILES = False

# This file keeps track of every downloaded file
TRACKER_FILE_LOCATION = "registered_files2.json"

# For chromium based browsers this is '.crdownload'
PARTIALLY_DOWNLOADED_FILE_EXT = ".crdownload"


"""
Targets identifiers
-------------------
option_button_xpath = ('...' 3 dot) button -> finds 15 per-scroll
download_button_xpath = Download that appears after clicking the option button -> finds 1 per-click
post_permalink_xpath = Permanent link of the post that posted this file -> finds 15 per-scroll

name_xpath = Name of the file -> finds 15 per-scroll
type_date_xpath = Type(pdf/docx) and uploaded date of the file -> finds 30 per-scroll

WARNING
-------
name_xpath, type_date_xpath -> this identifiers will change continuously so update it according to your needs 

"""
OPTION_BUTTON_XPATH = "//div[@aria-label='File options']"
DOWNLOAD_BUTTON_XPATH = "//a[contains(@href, 'https://www.facebook.com/download/')]"
POST_PERMALINK_XPATH = (
    "//a[contains(@href, 'https://www.facebook.com/groups/201623576939858/permalink/')]"
)

NAME_XPATH = "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d3f4x2em iv3no6db jq4qci2q a3bd9o3v lrazzd5p oo9gr5id hzawbc8m']"
TYPE_DATE_XPATH = "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d9wwppkn iv3no6db e9vueds3 j5wam9gi b1v8xokw oo9gr5id hzawbc8m']"


"""
Create necessary files

bot.log                  This will keep you updated on what's going on with this Bot
.secret                  Put all your secrets into this one -> username, password of FB, download location and driver location
registered_files.json    Keeps the track of downloaded files so that they don't get downloaded again if you start from the begining again!

"""
with open("bot.log", "a+") as f:
    f.close()
with open(".secret", "a+") as f:
    f.close()
with open("registered_files2.json", "a+") as f:
    f.close()


# For obvious reason 😉
with open(".secret", encoding=ENCODING) as f:
    info = """
    0 -> username,
    1 -> password,
    2 -> chromewebdriver location (windows)

    """
    try:
        SECRETS = [secret.strip() for secret in f.readlines()]
    except Exception as e:
        print("Put your stuffs in the .secret file!!!", info)
