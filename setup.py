from setuptools import find_packages, setup

setup(
    name="zyte-spider-templates",
    version="0.6.1",
    description="Spider templates for automatic crawlers.",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author="Zyte Group Ltd",
    author_email="info@zyte.com",
    url="https://github.com/zytedata/zyte-spider-templates",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pydantic>=2",
        "scrapy>=2.11.0",
        "scrapy-poet>=0.20.1",
        "scrapy-spider-metadata>=0.1.2",
        "scrapy-zyte-api[provider]>=0.15.0",
        "zyte-common-items>=0.13.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
