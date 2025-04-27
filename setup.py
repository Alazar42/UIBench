from setuptools import setup, find_packages

setup(
    name="UIBench",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # Core UI analysis & automation
        "playwright==1.42.0",
        "beautifulsoup4==4.13.3",
        "cssutils==2.9.0",
        "pylint==3.0.3",
        "spacy==3.7.4",
        "textblob==0.17.1",
        "textstat==0.7.3",
        "axe-playwright-python==0.1.4",
        "zaproxy==0.4.0",
        
       
        "lighthouse-python-plus==1.2.0",
        "lighthousedataextract==1.0.9",
        
        # Backend
        "fastapi==0.115.12",
        "uvicorn==0.34.0",
        "motor==3.7.0",
        "pymongo==4.11.3",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "python-multipart==0.0.9",
        
        # Utilities
        "python-dotenv==1.1.0",
        "requests==2.32.3",
        "aiohttp==3.9.3",
        "aiocache==0.12.2"
    ],
    python_requires=">=3.8",
    author="Mikiyas Tesfaye, Yared Kiros",
    author_email="your.email@example.com",
    description="A comprehensive UI evaluation and analysis tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Alazar42/UIBench.git",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 