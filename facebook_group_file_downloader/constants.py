encoding = "utf-8"
sort_by = "post_id"
target_file_type = "pdf"
normalization_form = "NFC"
log_file_location = "bot.log"

# This file keeps track of every downloaded file
tracker_file_location = "registered_file.json"

timeout = 600
explicit_wait_time = 10

# For obvious reason 😉
with open(".secret", encoding=encoding) as f:
    """
    0 -> username,
    1 -> password,
    2 -> download directory (for checking)
    3 -> chromewebdriver location (windows)

    """
    secrets = [secret.strip() for secret in f.readlines()]
