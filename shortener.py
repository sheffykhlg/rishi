import logging
import aiohttp

# Set up logging
logger = logging.getLogger(__name__)

async def shorten_link(domain: str, api_key: str, long_url: str) -> str | None:
    """
    Shortens a given URL using the specified shortener service by parsing its JSON response.
    """
    if not domain or not api_key:
        logger.warning("Shortener domain or API key is not configured.")
        return None

    # Construct the API URL for the shortener service
    api_url = f"https://{domain}/api"
    
    # The parameters might differ based on your shortener service
    params = {
        'api': api_key,
        'url': long_url,
    }

    try:
        # Make an asynchronous GET request to the shortener API
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    try:
                        # Parse the JSON response from the API
                        data = await response.json()
                        
                        # Check if the API call was successful and extract the URL from the 'shortenedUrl' key
                        if data.get("status") == "success" and data.get("shortenedUrl"):
                            short_url = data["shortenedUrl"]
                            logger.info(f"Successfully shortened URL: {long_url} -> {short_url}")
                            return short_url
                        else:
                            # Log the error message from the API if available
                            error_message = data.get('message', 'Unknown API error')
                            logger.error(f"Shortener API returned an error: {error_message}")
                            return None
                            
                    except aiohttp.ContentTypeError:
                        # This error happens if the response is not valid JSON
                        logger.error("Failed to parse JSON from shortener API response.")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to shorten link. HTTP Status: {response.status}, Response: {error_text}"
                    )
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"An error occurred during the API request to the shortener: {e}")
        return None
