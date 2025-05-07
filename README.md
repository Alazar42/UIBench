# UIBench Core Engine

UIBench is a Python-based core engine designed to automate the evaluation of web design aesthetics and accessibility. The engine fetches a website’s HTML content, parses it, and provides insights into its structure, internal links (subroutes), and key content. The primary focus of UIBench is to streamline the process of evaluating websites for design and accessibility without a web interface.

## Features

- **Web Page Analysis**: Fetches HTML content from a given URL and parses it.
- **Internal Link Extraction**: Automatically retrieves all internal links (subroutes) from the website.
- **Title and Body Content Extraction**: Extracts the title and body content of the webpage for further analysis.
- **HTML Parsing**: Built on `BeautifulSoup`, UIBench uses a flexible and efficient way to parse and navigate the HTML structure of the page.

## How It Works

1. **Submit URL**: Provide the URL of the website you want to analyze.
2. **Fetch HTML Content**: UIBench fetches the HTML content of the provided URL.
3. **Parse and Extract Information**: The engine parses the HTML to extract key information like the title, body content, and internal links.
4. **Analysis**: The engine performs internal link extraction and can be expanded for more advanced design and accessibility checks.

### UIBench Class

The `UIBench` class extends `BeautifulSoup` to provide additional functionality, such as fetching content from a URL and extracting internal links.

#### Key Methods

- `from_url(cls, url, features="html.parser")`: Fetches HTML from the provided URL and initializes a `UIBench` instance.
- `get_subroutes(self, base_url)`: Extracts all internal links (subroutes) from the HTML content.

#### Example Usage

```python
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
```

## Installation

To use the UIBench core engine locally, follow these steps:

### Prerequisites

- Python 3.11+
- Git

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/uibench.git
   cd uibench
   ```

2. Create and activate a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package:

   You have several installation options depending on your needs:

   ```bash
   pip install -e .          # Install everything (recommended for most users)
   pip install -e .[core]    # Install only core analysis functionality
   pip install -e .[backend] # Install only backend server functionality
   pip install -e .[dev]     # Install development tools and testing dependencies
   ```

   The different installation options provide:
   - `core`: Core analysis functionality including web scraping, NLP, and testing
   - `backend`: Server functionality including FastAPI and database utilities
   - `dev`: Development tools like black, flake8, mypy, and pytest extensions

## Contributing

We welcome contributions to the UIBench core engine! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes and commit them (`git commit -am 'Add feature'`).
4. Push to your branch (`git push origin feature-name`).
5. Open a pull request.

## Acknowledgments

- BeautifulSoup: For the efficient parsing and navigation of HTML content.
