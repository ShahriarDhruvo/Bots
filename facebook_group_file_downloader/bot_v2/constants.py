timeout = 1800  # 30 minutes
encoding = "utf-8"
explicit_wait_time = 10
target_file_type = "pdf"
normalization_form = "NFC"
log_file_location = "bot.log"
download_directory = "D:\\Download\\Molat-PDF-Files\\"

# Turned of because it downloads already downloaded files!
should_check_local_files = False


"""
For chromium based browsers this is '.crdownload'

"""
partially_downloaded_file_ext = ".crdownload"

# This file keeps track of every downloaded file
tracker_file_location = "registered_files.json"


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
with open("registered_files.json", "a+") as f:
    f.close()


# For obvious reason 😉
with open(".secret", encoding=encoding) as f:
    info = """
    0 -> username,
    1 -> password,
    2 -> chromewebdriver location (windows)

    """
    try:
        secrets = [secret.strip() for secret in f.readlines()]
    except Exception as e:
        print("Put your stuffs in the .secret file!!!", info)
