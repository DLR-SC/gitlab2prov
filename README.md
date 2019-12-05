# GitLab2PROV
> GitLab2PROV is a tool to extract provenance information (W3C PROV) from GitLab repositories.

## Setup :rocket:
### Installation
```bash
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
Excerpt from `config/example.ini`
```ini
[GITLAB]
token= YourTokenHere
url = GitLabInstanceURL
project = RepositoryURL
```
## Basic Usage
Keep in mind, the project status is very much **WIP** - this section will change! :wrench: 

At the moment, PROV generation is only viable for **small repositories** (50 commits or less). 
This will hopefully change in the near future.
```
python gitlab2prov.py :repositoryurl:
```
Will generate a `.dot` file containing a diagram of the generated PROV records.
Use the following command to generate a PDF.
```
dot -Tdpf prov.dot -o prov.pdf
```
**NOTE**: This can take a while - especially for bigger diagrams - as `dot` will spend some time computing the layout.

## About GitLab2PROV
GitLab2PROV is based on GitLab2Graph by Martin Stoffers:
Martin Stoffers: "Gitlab2Graph", v1.0.0, October 13. 2019, [GitHub Link](https://github.com/DLR-SC/Gitlab2Graph), DOI 10.5281/zenodo.3469385

The PROV model used in GitLab2PROV is based on the following papers:
- GitHub2PROV: Provenance for Supporting Software Project Management
- Git2PROV: Exposing Version Control System Content as W3C PROV
