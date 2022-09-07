<h1 align="center">Welcome to <code>gitlab2prov</code>! 👋</h1>
<p align="center">
  <a href="https://github.com/dlr-sc/gitlab2prov/blob/master/LICENSE">
    <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-yellow.svg" target="_blank" />
  </a>
  <a href="https://img.shields.io/badge/Made%20with-Python-1f425f.svg">
    <img src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg" alt="Badge: Made with Python"/>
  </a>
  <a href="https://pypi.org/project/gitlab2prov/">
    <img src="https://img.shields.io/pypi/v/gitlab2prov" alt="Badge: PyPi Version">
  </a>
  <a href="https://pypistats.org/packages/gitlab2prov">
    <img src="https://img.shields.io/pypi/dm/gitlab2prov" alt="Badge: PyPi Downloads Monthly">
  </a>
  <a href="https://twitter.com/dlr_software">
    <img alt="Twitter: DLR Software" src="https://img.shields.io/twitter/follow/dlr_software.svg?style=social" target="_blank" />
  </a>
  <a href="https://open.vscode.dev/DLR-SC/gitlab2prov">
    <img alt="Badge: Open in VSCode" src="https://img.shields.io/static/v1?logo=visualstudiocode&label=&message=open%20in%20visual%20studio%20code&labelColor=2c2c32&color=007acc&logoColor=007acc" target="_blank" />
  </a>
  <a href="https://zenodo.org/badge/latestdoi/215042878">
    <img alt="Badge: DOI" src="https://zenodo.org/badge/215042878.svg" target="_blank" />
  </a>
  <a href="https://www.w3.org/TR/prov-overview/">
    <img alt="Badge: W3C PROV" src="https://img.shields.io/static/v1?logo=w3c&label=&message=PROV&labelColor=2c2c32&color=007acc&logoColor=007acc?logoWidth=200" target="_blank" />
  </a>
  <a href="https://citation-file-format.github.io/">
    <img alt="Badge: Citation File Format Inside" src="https://img.shields.io/badge/-citable%20software-green" target="_blank" />
  </a>
</p>


> `gitlab2prov` is a Python library and command line tool that extracts provenance information from GitLab projects.

---

The `gitlab2prov` data model has been designed according to [W3C PROV](https://www.w3.org/TR/prov-overview/) specification.
The model documentation can be found [here](https://github.com/DLR-SC/gitlab2prov/tree/master/docs).


## ️🏗️ ️Installation

Clone the project and install using `pip`:
```bash
pip install .
```

Or install the latest release from [PyPi](https://pypi.org/project/gitlab2prov/):
```bash
pip install gitlab2prov
```

To install `gitlab2prov` with all extra dependencies require the `[dev]` extras while proceeding as before:
```bash
pip install .[dev] # clone and invoke pip locally
pip install gitlab2prov[dev] # install from PyPi
```

## 🚀‍ Usage

To extract provenance from a gitlab project, follow these steps:
| Instructions                                                                                                                                                      | Config Option    |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| 1. Obtain an API Token for the GitLab API ([Token Guide](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#creating-a-personal-access-token)) | `--token`        |
| 2. Set the URL[s] for the GitLab Project[s]                                                                                                                             | `--project_urls` |
| 3. Choose a PROV serialization format                                                                                                                             | `--format`       |


`gitlab2prov` can be configured either by command line flags or by using a config file.

### 📋 Config File Example

An example of a configuration file can be found in `/config/example.ini`.

```ini
# This is an example of a configuration file as used by gitlab2prov.
# The configuration options match the command line flags in function.

[GITLAB]
# Gitlab project urls as a comma seperated list.
project_urls = project_a_url, project_b_url

# Gitlab personal access token.
# More about tokens and how to create them:
# https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token
token = token

[OUTPUT]
# Provenance serialization format.
# Supported formats: json, rdf, xml, provn, dot
format = json, rdf, xml

# File location to write provenance output to.
# Each specified format will result in a seperate file.
# For example:
#     format = json, xml
#     outfile = out/example
# Creates the files:
#     out/example.json
#     out/example.xml
outfile = provout/example

[MISC]
# Enables/Disables profiling using the cprofile lib.
# The runtime profile is written to a file called gitlab2prov-run-$TIMESTAMP.profile
# where $TIMESTAMP is the current time in 'YYYY-MM-DD-hh-mm-ss' format.
# The profile can be visualized using tools such as snakeviz.
profile = False

# Enables/Disables verbose output (DEBUG mode logging to stdout)
verbose = False

# Path to double agent mapping to unify duplicated agents.
double_agents = path/to/alias/mapping

# Enables/Disables agent pseudonymization by enumeration.
pseudonymous = False
```

### 🖥️ Command Line Usage ☝ Single Format Serialization

```
  usage: gitlab2prov [-h] -p PROJECT_URLS [PROJECT_URLS ...] -t TOKEN [-c CONFIG_FILE] [-f {json,rdf,xml,provn,dot}] [-v] [--double-agents DOUBLE_AGENTS] [--pseudonymous] [--profile] {multi-format} ...

Extract provenance information from GitLab projects.

positional arguments:
  {multi-format}
    multi-format        serialize output in multiple formats

options:
  -h, --help            show this help message and exit
  -p PROJECT_URLS [PROJECT_URLS ...], --project-urls PROJECT_URLS [PROJECT_URLS ...]
                        gitlab project urls
  -t TOKEN, --token TOKEN
                        gitlab api access token
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        config file path
  -f {json,rdf,xml,provn,dot}, --format {json,rdf,xml,provn,dot}
                        provenance serialization format
  -v, --verbose         write log to stderr, set log level to DEBUG
  --double-agents DOUBLE_AGENTS
                        agent mapping file path
  --pseudonymous        pseudonymize user names by enumeration
  --profile             enable deterministic profiling, write profile to 'gitlab2prov-run-$TIMESTAMP.profile' where $TIMESTAMP is the current timestamp in 'YYYY-MM-DD-hh-mm-ss' format
```
### 🖥️ Command Line Usage 🖐 Multi Format Serialization
To serialize the extracted provenance information into multiple formats in one go, use the provided `multi-format` mode.

```
usage: gitlab2prov multi-format [-h] [-f {json,rdf,xml,provn,dot} [{json,rdf,xml,provn,dot} ...]] -o OUTFILE

options:
  -h, --help            show this help message and exit
  -f {json,rdf,xml,provn,dot} [{json,rdf,xml,provn,dot} ...], --format {json,rdf,xml,provn,dot} [{json,rdf,xml,provn,dot} ...]
                        provenance serialization formats
  -o OUTFILE, --outfile OUTFILE
                        serialize to {outfile}.{format} for each specified format
```

### 🎨 Provenance Output Formats

`gitlab2prov` supports output formats that the [`prov`](https://github.com/trungdong/prov) library provides:
* [PROV-N](http://www.w3.org/TR/prov-n/)
* [PROV-O](http://www.w3.org/TR/prov-o/) (RDF)
* [PROV-XML](http://www.w3.org/TR/prov-xml/)
* [PROV-JSON](http://www.w3.org/Submission/prov-json/)
* [Graphviz](https://graphviz.org/) (DOT)

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## How to cite

If you use GitLab2PROV in a scientific publication, we would appreciate citations to the following paper:

* Schreiber, A., de Boer, C. and von Kurnatowski, L. (2021). [GitLab2PROV—Provenance of Software Projects hosted on GitLab](https://www.usenix.org/conference/tapp2021/presentation/schreiber). 13th International Workshop on Theory and Practice of Provenance (TaPP 2021), USENIX Association

Bibtex entry:

```BibTeX
@InProceedings{SchreiberBoerKurnatowski2021,
  author    = {Andreas Schreiber and Claas de~Boer and Lynn von~Kurnatowski},
  booktitle = {13th International Workshop on Theory and Practice of Provenance (TaPP 2021)},
  title     = {{GitLab2PROV}{\textemdash}Provenance of Software Projects hosted on GitLab},
  year      = {2021},
  month     = jul,
  publisher = {{USENIX} Association},
  url       = {https://www.usenix.org/conference/tapp2021/presentation/schreiber},
}
```

You can also cite specific releases published on Zenodo: [![DOI](https://zenodo.org/badge/215042878.svg)](https://zenodo.org/badge/latestdoi/215042878)

## References

**Influencial Software for `gitlab2prov`**
* Martin Stoffers: "Gitlab2Graph", v1.0.0, October 13. 2019, [GitHub Link](https://github.com/DLR-SC/Gitlab2Graph), DOI 10.5281/zenodo.3469385

* Quentin Pradet: "How do you rate limit calls with aiohttp?", [GitHub Gist](https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741), MIT LICENSE

**Influencial Papers for `gitlab2prov`**:

* De Nies, T., Magliacane, S., Verborgh, R., Coppens, S., Groth, P., Mannens, E., and Van de Walle, R. (2013). [Git2PROV: Exposing Version Control System Content as W3C PROV](https://dl.acm.org/doi/abs/10.5555/2874399.2874431). In *Poster and Demo Proceedings of the 12th International Semantic Web Conference* (Vol. 1035, pp. 125–128).

* Packer, H. S., Chapman, A., and Carr, L. (2019). [GitHub2PROV: provenance for supporting software project management](https://dl.acm.org/doi/10.5555/3359032.3359039). In *11th International Workshop on Theory and Practice of Provenance (TaPP 2019)*.

**Papers that refer to `gitlab2prov`**:

* Andreas Schreiber, Claas de Boer (2020). [Modelling Knowledge about Software Processes using Provenance Graphs and its Application to Git-based VersionControl Systems](https://dl.acm.org/doi/10.1145/3387940.3392220). In *ICSEW'20: Proceedings of the IEEE/ACM 42nd Conference on Software Engineering Workshops* (pp. 358–359).

* Tim Sonnekalb, Thomas S. Heinze, Lynn von Kurnatowski, Andreas Schreiber, Jesus M. Gonzalez-Barahona, and Heather Packer (2020). [Towards automated, provenance-driven security audit for git-based repositories: applied to germany's corona-warn-app: vision paper](https://doi.org/10.1145/3416507.3423190). In *Proceedings of the 3rd ACM SIGSOFT International Workshop on Software Security from Design to Deployment* (pp. 15–18).

* Andreas Schreiber (2020). [Visualization of contributions to open-source projects](https://doi.org/10.1145/3430036.3430057). In *Proceedings of the 13th International Symposium on Visual Information Communication and Interaction*. ACM, USA.