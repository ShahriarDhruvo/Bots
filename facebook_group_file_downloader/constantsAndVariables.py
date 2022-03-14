encoding = "utf-8"
target_file_type = "pdf"
log_file_location = "bot.log"

# This file keeps track of every downloaded file
tracker_file_location = "files_info.json"

explicit_wait_time = 10
network_failure_timeout = 600

# this value will ensure how many downloads will happen concurrently
download_thread_count = 3

"""
 targets identifiers -> this identifiers will change continuously so update it according to your needs 

"""
download_button_cssSelector = "a[href*='https://www.facebook.com/download/']"
fileOption_xpath = "//div[@aria-label='File options']"  # by default finds 15 per-scroll

# Target identifiers
# They change too often so they have to be present here
fileName_xpath = "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d3f4x2em iv3no6db jq4qci2q a3bd9o3v lrazzd5p oo9gr5id hzawbc8m']"  # find 15 per-scroll
fileTypeDate_xpath = "//span[@class='d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j fe6kdd0r mau55g9w c8b282yb keod5gw0 nxhoafnm aigsh9s9 d9wwppkn iv3no6db e9vueds3 j5wam9gi b1v8xokw oo9gr5id hzawbc8m']"  # find 30 per-scroll


# For obvious reason 😉
with open(".secret", encoding=encoding) as f:
    """
    0 -> username,
    1 -> password,
    2 -> download directory (for checking)
    3 -> chromewebdriver location (windows)

    """
    secrets = [secret.strip() for secret in f.readlines()]
