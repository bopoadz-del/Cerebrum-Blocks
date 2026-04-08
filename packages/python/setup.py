"""Setup for Cerebrum SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cerebrum-sdk",
    version="1.0.0",
    author="Cerebrum Team",
    author_email="team@cerebrumblocks.com",
    description="Build AI Like Lego - Official Python SDK for Cerebrum Blocks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bopoadz-del/cerebrum-blocks",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "black>=22.0",
            "mypy>=1.0",
        ],
    },
    keywords="ai, llm, chatgpt, openai, claude, blocks, sdk, api",
    project_urls={
        "Bug Reports": "https://github.com/bopoadz-del/cerebrum-blocks/issues",
        "Source": "https://github.com/bopoadz-del/cerebrum-blocks",
        "Documentation": "https://docs.cerebrumblocks.com",
    },
)
