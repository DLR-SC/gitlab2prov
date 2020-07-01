import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="gitlab2prov",
    version="0.1",
    author="Claas de Boer, Andreas Schreiber",
    author_email="claas.deboer@dlr.de, andreas.schreiber@dlr.de",
    description="Extract provenance information (W3C PROV) from GitLab projects.",
    keywords=[
        "prov",
        "gitlab",
        "neo4j",
        "provenance",
        "prov generation",
        "software analytics",
        "w3c prov"
    ],
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/dlr-sc/gitlab2prov",
    packages=find_packages(),
    install_requires=[
        "prov==1.5.3",
        "pydot",
        "aiohttp",
        "prov-db-connector",
        "yarl",
        "py2neo==5.0b1"
    ],
    entry_points={"console_scripts":["gitlab2prov=gitlab2prov.cli:main"]},
    license="MIT",
    classifiers=["License :: OSI Approved :: MIT License"],
    include_package_data=True,
)
