timeout = 1800  # 30 minutes
encoding = "utf-8"
sort_by = "post_id"
explicit_wait_time = 10
target_file_type = "pdf"
normalization_form = "NFC"
log_file_location = "bot.log"

"""
For chromium based browsers this is '.crdownload'

"""
partially_downloaded_file_ext = ".crdownload"

# This file keeps track of every downloaded file
tracker_file_location = "registered_files.json"

# For obvious reason 😉
with open(".secret", encoding=encoding) as f:
    """
    0 -> username,
    1 -> password,
    2 -> download directory (for checking)
    3 -> chromewebdriver location (windows)

    """
    secrets = [secret.strip() for secret in f.readlines()]
