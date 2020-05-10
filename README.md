# GitLab2PROV - Extract Provenance Information from GitLab Repositories

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![DOI](https://zenodo.org/badge/215042878.svg)](https://zenodo.org/badge/latestdoi/215042878) ![Python application](https://github.com/DLR-SC/gitlab2prov/workflows/Python%20application/badge.svg?branch=master) ![mypy-check](https://github.com/DLR-SC/gitlab2prov/workflows/mypy-check/badge.svg) ![Deploy to Amazon ECS](https://github.com/DLR-SC/gitlab2prov/workflows/Deploy%20to%20Amazon%20ECS/badge.svg)

## Data Model

GitLab2PROV uses a data model according to [W3C PROV](https://www.w3.org/TR/prov-overview/) specification.

## Setup and Usage:rocket:

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
### Configuration

#### Obtain Private Access Token for GitLab

Go to `https://YOUR-GITLAB/profile/personal_access_tokens` and claim a personal access token.
The necessary scopes are `api` and `read_user`. A guide on how to create an API access token can be found [here](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#creating-a-personal-access-token).


#### Configure `gitlab2prov`

All available configuration options can be set by providing command line arguments/flags.
To get a list of available options, simply run `python gitlab2prov.py -h` or refer to the **Usage** section of this README.
To ease the configuration of consecutive runs, `gitlab2prov` is able to use a configuration file.
The default path for the config file is set to `config/config.ini` and can be changed by using the `-c` or likewise the `--config-file` flag.

An example of a configuration file can be found at `config/example.ini`.

Excerpt from `config/example.ini`
```ini
[GITLAB2PROV]
token = token
quiet = False
format = json
rate_limit = 10

neo4j = False
neo4j_user = username
neo4j_host = localhost
neo4j_boltport = 7687
neo4j_password = password

[PROJECTS]
foo = project_foo_url
bar = project_bar_url
```
**Note:** Command line flags will take precedence over values provided by the config file.

### Usage
```
❯ python gitlab2prov.py -h
usage: GitLab2PROV [-h] [-p <string> [<string> ...]] [-t <string>] [-r <int>]
                   [-c <string>] [-f {provn,json,rdf,xml,dot}] [-q] [--neo4j]
                   [--neo4j-user <string>] [--neo4j-password <string>]
                   [--neo4j-host <string>] [--neo4j-boltport <string>]

Extract provenance information from GitLab projects.

optional arguments:
  -h, --help            show this help message and exit

BASIC CONFIG:
  -p <string> [<string> ...], --project-urls <string> [<string> ...]
                        gitlab project urls
  -t <string>, --token <string>
                        gitlab api access token
  -r <int>, --rate-limit <int>
                        api client rate limit (in req/s)
  -c <string>, --config-file <string>
                        config file path
  -f {provn,json,rdf,xml,dot}, --format {provn,json,rdf,xml,dot}
                        provenance output format
  -q, --quiet           suppress output to stdout

NEO4J CONFIG:
  --neo4j               enable neo4j storage
  --neo4j-user <string>
                        neo4j username
  --neo4j-password <string>
                        neo4j password
  --neo4j-host <string>
                        neo4j host
  --neo4j-boltport <string>
                        neo4j bolt protocol port

Consider visiting GitLab2PROV on GitHub: https://github.com/DLR-SC/gitlab2prov
```

## Example

### Cypher Query

```cypher
MATCH (user:Agent)-[:wasAttributedTo]-(fileVersion:Entity), (fileVersion:Entity)-[:specializationOf]->(file:Entity)
WHERE 
  fileVersion.`prov:type` = "file_version" AND file.`prov:type` = "file"
RETURN 
  user.name, COUNT(DISTINCT file) AS file_count
ORDER BY file_count DESC
```

## Credits
**Software that has provided the foundations for GitLab2PROV**  
* Martin Stoffers: "Gitlab2Graph", v1.0.0, October 13. 2019, [GitHub Link](https://github.com/DLR-SC/Gitlab2Graph), DOI 10.5281/zenodo.3469385  

* Quentin Pradet: "How do you rate limit calls with aiohttp?", [GitHub Gist](https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741), MIT LICENSE


**Papers that GitLab2PROV is based on**:

* De Nies, T., Magliacane, S., Verborgh, R., Coppens, S., Groth, P., Mannens, E., & Van de Walle, R. (2013). [Git2PROV: Exposing Version Control System Content as W3C PROV](https://dl.acm.org/doi/abs/10.5555/2874399.2874431). In *Poster and Demo Proceedings of the 12th International Semantic Web Conference* (Vol. 1035, pp. 125–128).

* Packer, H. S., Chapman, A., & Carr, L. (2019). [GitHub2PROV: provenance for supporting software project management](https://dl.acm.org/doi/10.5555/3359032.3359039). In *11th International Workshop on Theory and Practice of Provenance (TaPP 2019)*.
