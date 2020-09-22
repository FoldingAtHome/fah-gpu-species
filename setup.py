from setuptools import setup, find_packages

setup(
    name="fah_log_parser",
    version="0.1",
    packages=find_packages(),
    install_requires=["fire>=0.3", "pandas>=1.1", "parsy>=1.3", "pydantic>=1.6", "rich>=7.0"],
    entry_points={"console_scripts": ["parse_fah_log = fah_log_parser.app:main"]},
    author="Matt Wittmann",
    author_email="matt.wittmann@choderalab.org",
    description="Parser for extracting structured data from core22 log files",
    keywords="foldingathome",
    url="https://github.com/FoldingAtHome/fah-gpu-species",
)
