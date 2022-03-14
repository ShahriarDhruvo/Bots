encoding = "utf-8"
target_file_type = "pdf"
log_file_location = "bot.log"

# This file keeps track of every downloaded file
tracker_file_location = "files_info.json"

explicit_wait_time = 10
network_failure_timeout = 600

# For obvious reason 😉
with open(".secret", encoding=encoding) as f:
    """
    0 -> username,
    1 -> password,
    2 -> download directory (for checking)
    3 -> chromewebdriver location (windows)

    """
    secrets = [secret.strip() for secret in f.readlines()]
