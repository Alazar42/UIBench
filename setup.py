from setuptools import setup, find_packages

setup(
    name="uibench",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Web scraping and parsing
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "cssselect>=1.2.0",
        "requests>=2.31.0",
        
        # Browser automation
        "playwright>=1.40.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        
        # Testing
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        
        # NLP and text analysis
        "nltk>=3.8.1",
        "textblob>=0.17.1",
        "textstat>=0.7.3",
        "spacy>=3.7.0",
        
        # Web and async
        "aiohttp>=3.9.0",
        "aiofiles>=23.2.1",
        
        # Data handling
        "pydantic>=2.5.0",
        "pyyaml>=6.0.1",
        "jsonschema>=4.20.0",
        
        # CSS parsing
        "tinycss2>=1.2.1",
        
        # System utilities
        "psutil>=5.9.0",
        
        # UI and formatting
        "colorama>=0.4.6",
        "tqdm>=4.66.0",
        "rich>=13.6.0",
        
        # Additional utilities
        "python-dotenv>=1.0.0",
        "click>=8.0.0",
        "typing-extensions>=4.0.0",
        "packaging>=22.0"
    ],
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