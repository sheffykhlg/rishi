import aiohttp
import logging

logger = logging.getLogger(__name__)

async def shorten_link(domain: str, api_key: str, long_url: str) -> str | None:
    """
    Diye gaye URL ko shortener API ka use karke shorten karta hai.
    NOTE: Yeh ek generic implementation hai. Aapko apne shortener service
    ke API documentation ke hisab se isko badalna pad sakta hai.
    """
    if not domain or not api_key:
        logger.warning("Shortener domain ya API key set nahi hai.")
        return None
        
    # Example API URL format, ise apne service ke hisab se badlein
    api_url = f"https://{domain}/api"
    params = {
        "api": api_key,
        "url": long_url
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    # Response format ko check karein (text, json, etc.)
                    data = await response.text() 
                    # Ho sakta hai aapko response.json() use karna pade
                    # Example: `result = await response.json()` and then `return result.get('shortenedUrl')`
                    logger.info(f"Link successfully shorten hua: {data}")
                    return data
                else:
                    logger.error(f"Shortener API se error aaya. Status: {response.status}, Response: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Link shorten karte waqt exception: {e}")
        return None
