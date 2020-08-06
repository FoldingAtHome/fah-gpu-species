from setuptools import setup, find_packages

setup(
    name="fah_log_parser",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fire>=0.3",
        "parsy>=1.3",
        "dataclasses-json>=0.5",
    ],
    entry_points={"console_scripts": ["parse_fah_log = fah_log_parser:cli",],},
    author="Matt Wittmann",
    author_email="matt.wittmann@choderalab.org",
    description="Parser for extracting structured data from core22 log files",
    keywords="foldingathome",
    url="https://github.com/FoldingAtHome/fah-gpu-species",
)
