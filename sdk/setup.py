"""Setup for Cerebrum Blocks Python SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cerebrum-blocks",
    version="1.0.0",
    author="Cerebrum Team",
    author_email="team@cerebrumblocks.com",
    description="Build AI like Lego. One API. 13 blocks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bopoadz-del/cerebrum-blocks",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
        ],
    },
    keywords="ai, llm, openai, anthropic, vector-search, chromadb, api, sdk",
    project_urls={
        "Bug Reports": "https://github.com/bopoadz-del/cerebrum-blocks/issues",
        "Source": "https://github.com/bopoadz-del/cerebrum-blocks",
        "Documentation": "https://docs.cerebrumblocks.com",
    },
)
