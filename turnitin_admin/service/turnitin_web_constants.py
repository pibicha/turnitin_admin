# turnitin_web_constants.py
class TurnitinWebConstants:
    # URLs
    LOGIN_URL = "https://www.turnitin.com/login_page.asp?lang=en_us"
    HOMEPAGE = "https://www.turnitin.com/t_home.asp"
    SUBMIT_URL = "https://www.turnitin.com/t_submit.asp"
    CONFIRM_URL = "https://www.turnitin.com/submit_confirm.asp"
    METADATA_URL = "https://www.turnitin.com/panda/get_submission_metadata.asp"
    INBOX_URL_TEMPLATE = "https://www.turnitin.com/assignment/type/paper/inbox/%s?lang=en_us"
    DOWNLOAD_URL = "https://ev.turnitin.com/app/carta/en_us/?ro=103&lang=en_us&s=1&u=1176178090&o="
    SET_FILTER_URL = "https://ev.turnitin.com/paper/%s/similarity/options?lang=en_us&cv=1&output=json&tl=0"
    
    # Headers
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
    ACCEPT_HTML = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    ACCEPT_JSON = "application/json, text/javascript, */*; q=0.01"
    ACCEPT_TEXT = 'text/plain'
    CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
    ACQUIRE_DOWNLOAD_URL_LINK = "https://ev.turnitin.com/paper/%s/queue_pdf?lang=en_us&cv=1&output=json"

    # Cookie related
    LEGACY_SESSION_ID = "legacy-session-id"
    SESSION_ID = "session-id"
    COOKIE_SEPARATOR = "; "

    # Form fields
    DEFAULT_USER_ID = "1176483583"
    AUTHOR_FIRST = "No Repository"
    AUTHOR_LAST = "Check"
    LANG_EN_US = "en_us"

    # Patterns
    UUID_PATTERN = r'"uuid":"([^"]+)"'

    # Other
    MAX_RETRIES = 180
    RETRY_DELAY_MS = 2000