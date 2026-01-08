import random
import requests
import uuid
from typing import Optional, Dict, Any

# Each tuple: (user_agent, sec_ch_ua, mobile, platform)
HEADER_PROFILES = [
    # Windows Desktop - Chrome
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        '"Google Chrome";v="131", "Chromium";v="131", "Not?A_Brand";v="24"',
        "?0",
        '"Windows"',
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        '"Chromium";v="130", "Not?A_Brand";v="99", "Google Chrome";v="130"',
        "?0",
        '"Windows"',
    ),
    # Windows Desktop - Firefox (no sec-ch-ua)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "",
        "",
        "",
    ),
    # Android Mobile - Chrome
    (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        '"Google Chrome";v="131", "Chromium";v="131", "Not?A_Brand";v="24"',
        "?1",
        '"Android"',
    ),
    (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        '"Chromium";v="130", "Not?A_Brand";v="99", "Google Chrome";v="130"',
        "?1",
        '"Android"',
    ),
    # iOS Mobile - Safari (no sec-ch-ua)
    (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "",
        "",
        "",
    ),
]

ACCEPT_LANGUAGES = [
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,fr;q=0.8",
    "fr-FR,fr;q=0.6",
]


def get_random_cookies() -> Dict[str, str]:
    """Generate realistic 8a.nu cookies to mimic normal user session."""
    categories = ["sportclimbing", "bouldering"]
    color_themes = ["system", "light", "dark"]
    periods = ["3", "6", "12", "24"]

    # Generate realistic Stripe mid (UUID-like format with timestamp)
    stripe_mid = str(uuid.uuid4())

    return {
        "color-value": random.choice(color_themes),
        "ranking-sub-navigation__recent-category": random.choice(categories),
        "user-ascent-statistics__recent-period-bouldering": random.choice(
            periods
        ),
        "__stripe_mid": stripe_mid,
    }


def get_random_headers(referer: Optional[str] = None) -> Dict[str, str]:
    """Generate realistic browser headers with consistent platform/mobile/UA combinations."""
    user_agent, sec_ch_ua, mobile, platform = random.choice(HEADER_PROFILES)

    headers = {
        "accept": "*/*",
        "accept-language": random.choice(ACCEPT_LANGUAGES),
        "user-agent": user_agent,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }

    # Only add Client Hints headers for Chromium-based browsers
    if sec_ch_ua:
        headers["sec-ch-ua"] = sec_ch_ua
        headers["sec-ch-ua-mobile"] = mobile
        headers["sec-ch-ua-platform"] = platform
        headers["sec-gpc"] = "1"

    if referer:
        headers["referer"] = referer

    return headers

def get_static_cookies() -> Dict[str, str]:
    """Generate static cookies for requests."""
    return {
        "color-value": "system",
        "ranking-sub-navigation__recent-category": "sportclimbing",
        "user-ascent-statistics__recent-period-bouldering": "12",
        "__stripe_mid": "018d25f0-6232-4a73-84a2-48793809c41697b668",
    }

def get_static_headers() -> Dict[str, str]:
    """Generate static browser headers for requests."""
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-ch-ua": '"Chromium";v="130", "Not?A_Brand";v="99", "Google Chrome";v="130"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-gpc": "1",
    }
    return headers


def fetch(
    url: str,
    random_headers: bool = True,
    referer: Optional[str] = None,
    timeout: int = 30,
    authentication_cookie: str = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON data from API endpoint with realistic browser headers and cookies.

    Args:
        url: API endpoint URL
        referer: Optional referer URL
        timeout: Request timeout in seconds
        session: Optional requests.Session for persistent cookies

    Returns:
        JSON response as dict, or None on failure
    """
    if random_headers:
        request_headers = get_random_headers(referer=referer)
        cookies = get_random_cookies()
    else:
        request_headers = get_static_headers()
        cookies = get_static_cookies()

    if authentication_cookie:
        cookies["nu8a_session"] = authentication_cookie
    
    response = requests.get(
        url, headers=request_headers, cookies=cookies, timeout=timeout
    )

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")
        raise error
