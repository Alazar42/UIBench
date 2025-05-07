from setuptools import setup, find_packages

# Core dependencies - Used for core analysis functionality
core_requirements = [
    # Browser automation and testing
    "playwright>=1.40.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    
    # Web scraping and parsing
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "cssselect>=1.2.0",
    "requests>=2.31.0",
    "aiohttp>=3.9.0",  # For async HTTP requests
    "html5lib>=1.1",  # Better HTML parsing
    
    # NLP and text analysis
    "nltk>=3.8.1",
    "textblob>=0.17.1",
    "textstat>=0.7.3",
    "spacy>=3.7.0",
    
    # Data handling and validation
    "pydantic>=2.5.0",
    "pyyaml>=6.0.1",
    "jsonschema>=4.40.0",
    "python-dotenv>=1.0.0",  # For environment variables
    
    # CSS and HTML parsing
    "tinycss2>=1.2.1",
    "cssselect>=1.2.0",
    "pyquery>=2.0.0",  # jQuery-like HTML parsing
    
    # Security and authentication
    "passlib>=1.7.4",  # For password hashing
    "python-jose[cryptography]>=3.3.0",  # For JWT
    "bcrypt>=4.0.1",  # For password hashing
    
    # Utilities
    "tqdm>=4.66.0",  # Progress bars
    "colorama>=0.4.6",  # Colored terminal output
    "rich>=13.6.0",  # Rich text and formatting
    "typing-extensions>=4.0.0",
    "packaging>=22.0",
    "click>=8.0.0",  # CLI tools
]

setup(
    name="uibench",
    version="0.1.0",
    packages=find_packages(),
    install_requires=core_requirements,
    extras_require={
        "dev": [
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.5.0",
            "pytest-xdist>=3.5.0",
            "pytest-timeout>=2.2.0"
        ],
        "nlp": [
            "spacy>=3.7.0",
            "nltk>=3.8.1",
            "textblob>=0.17.1",
            "textstat>=0.7.3"
        ]
    },
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "uibench=core.cli:main",
        ],
    },
    package_data={
        "core": [
            "data/*.json",
            "data/*.yaml",
            "templates/*.html",
            "static/*.css",
            "static/*.js"
        ]
    },
    include_package_data=True,
) 