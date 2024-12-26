import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class UIBench(BeautifulSoup):
    def __init__(self, markup, features=None, builder=None, parse_only=None, from_encoding=None, exclude_encodings=None, element_classes=None):
        # Initialize the parent class with the necessary arguments
        super().__init__(markup, features, builder, parse_only, from_encoding, exclude_encodings, element_classes)

    @classmethod
    def from_url(cls, url, features="html.parser"):
        """
        Fetches HTML content from the provided URL and initializes a UIBench instance.
        
        :param url: The URL to fetch HTML from.
        :param features: The parser to use (default is "html.parser").
        :return: An instance of UIBench.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return cls(response.text, features)
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch URL: {e}")
            return None

    def get_subroutes(self, base_url):
        """
        Extracts all internal links (subroutes) from the HTML of the given URL.
        
        :param base_url: The base URL to filter internal links.
        :return: A set of unique internal subroutes.
        """
        subroutes = set()
        if self:
            for link in self.find_all("a", href=True):
                full_url = urljoin(base_url, link.get("href"))
                parsed_base = urlparse(base_url)
                parsed_link = urlparse(full_url)

                # Check if the link is internal (same domain as the base URL)
                if parsed_base.netloc == parsed_link.netloc:
                    subroutes.add(parsed_link.path)  # Add the path only
        return subroutes

# Example usage
if __name__ == "__main__":
    url = "https://google.com"  # Replace with your target URL
    uibench_instance = UIBench.from_url(url)

    if uibench_instance:
        # Accessing BeautifulSoup methods and properties
        print("Title:", uibench_instance.title.string if uibench_instance.title else "No title found")
        print("Body:", uibench_instance.body.text.strip() if uibench_instance.body else "No body content")
        print("\nLinks:")
        for link in uibench_instance.find_all("a"):
            print("Link:", link.get("href"))
        
        print("\nSubroutes:")
        subroutes = uibench_instance.get_subroutes(url)
        for route in sorted(subroutes):
            print(route)
