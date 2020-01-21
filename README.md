# GitLab2PROV

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> GitLab2PROV is a tool to extract provenance information (W3C PROV) from GitLab repositories.

### Usage
```
usage: gitlab2prov.py [-h] [--provn PROVN] [--neo4j]

Extract provenance information from a GitLab repository.

optional arguments:
  -h, --help     show this help message and exit
  --provn PROVN  output file
  --neo4j        save to neo4j
```

### Configuration
`gitlab2prov` is configured by its config file at `config/config.ini`.

Excerpt from `config/config.ini.example`

```ini
[GITLAB]
token = YourTokenHere
project = RepositoryURL
rate = RateLimitOfGitLabClient

[NEO4J]
host = Neo4jURL
user = YourUsername
password = YourPassword
boltport = BOLTPort
```

## Setup :rocket:
### Installation
```
# Clone repository via SSH (recommended)
git clone git@github.com:DLR-SC/gitlab2prov.git

# Change into directory
cd gitlab2prov

# Create a virtual environment (recommended)
python -m venv env

# Activate the environment
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```
## Credits
**Software that has provided the foundations for GitLab2PROV**  
> Martin Stoffers: "Gitlab2Graph", v1.0.0, October 13. 2019, [GitHub Link](https://github.com/DLR-SC/Gitlab2Graph), DOI 10.5281/zenodo.3469385  

> Quentin Pradet: "How do you rate limit calls with aiohttp?", [GitHub Gist](https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741), MIT LICENSE


**Papers that GitLab2PROV is based on**:
> GitHub2PROV: Provenance for Supporting Software Project Management 

> Git2PROV: Exposing Version Control System Content as W3C PROV
