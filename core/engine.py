import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class UIBench(BeautifulSoup):
    def __init__(self, url, features="html.parser", **kwargs):
        """
        Initializes the UIBench instance by fetching HTML content from the provided URL.
        
        :param url: The URL to fetch HTML from.
        :param features: The parser to use (default is "html.parser").
        :param kwargs: Additional arguments for the BeautifulSoup constructor.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses
            # Initialize the parent class (BeautifulSoup) with the fetched HTML content
            super().__init__(response.text, features, **kwargs)
            self.base_url = url
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {e}")
            raise

    def get_subroutes(self):
        """
        Extracts all internal links (subroutes) from the HTML of the given URL.
        
        :return: A set of unique internal subroutes.
        """
        subroutes = set()
        if self:
            for link in self.find_all("a", href=True):
                full_url = urljoin(self.base_url, link.get("href"))
                parsed_base = urlparse(self.base_url)
                parsed_link = urlparse(full_url)

                # Check if the link is internal (same domain as the base URL)
                if parsed_base.netloc == parsed_link.netloc:
                    subroutes.add(parsed_link.path)  # Add the path only
        return subroutes

# Example usage
if __name__ == "__main__":
    url = "https://google.com"  # Replace with your target URL
    uibench_instance = UIBench(url)

    # Accessing BeautifulSoup methods and properties
    print("Title:", uibench_instance.title.string if uibench_instance.title else "No title found")
    print("Body:", uibench_instance.body.text.strip() if uibench_instance.body else "No body content")
    
    print("\nLinks:")
    for link in uibench_instance.find_all("a"):
        print("Link:", link.get("href"))
    
    print("\nSubroutes:")
    subroutes = uibench_instance.get_subroutes()
    for route in sorted(subroutes):
        print(route)
