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

Please note that this tool requires Git to be installed on your machine.

Clone the project and install using `pip`:
```bash
pip install .
```

Or install the latest release from [PyPi](https://pypi.org/project/gitlab2prov/):
```bash
pip install gitlab2prov
```

To install `gitlab2prov` with all extra dependencies require the `[dev]` extras:
```bash
pip install .[dev]            # clone repo, install with extras
pip install gitlab2prov[dev]  # PyPi, install with extras
```

## ⚡ Getting started

`gitlab2prov` needs a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) to clone git repositories and to authenticate with the GitLab API.
Follow [this guide](./docs/guides/tokens.md) to create an access token with the required [scopes](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#personal-access-token-scopes).


## 🚀‍ Usage

`gitlab2prov` can be configured using the command line interface or by providing a configuration file in `.yaml` format.

###  Command Line Usage
The command line interface consists of commands that can be chained together like a unix pipeline.

```
Usage: gitlab2prov [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Extract provenance information from GitLab projects.

Options:
  --version        Show the version and exit.
  --verbose        Enable logging to 'gitlab2prov.log'.
  --config FILE    Read config from file.
  --validate FILE  Validate config file and exit.
  --help           Show this message and exit.

Commands:
  combine                  Combine multiple graphs into one.
  extract                  Extract provenance information for one or more...
  load                     Load provenance files.
  merge-duplicated-agents  Merge duplicated agents based on a name to...
  pseudonymize             Pseudonymize a provenance graph.
  save                     Save provenance information to a file.
  stats                    Print statistics such as node counts and...
```

### Configuration Files
`gitlab2prov` supports configuration files in `.yaml` format that are functionally equivalent to command line invocations. 

To read configuration details from a file instead of specifying on the command line, use the `--config` option:
```ini
# initiate a run using a config file
gitlab2prov --config config/example.yaml
```
You can validate your config file using the provided JSON-Schema `gitlab2prov/config/schema.json` that comes packaged with every installation:
```ini
# check config file for syntactical errors
gitlab2prov --validate config/example.yaml
```

Config file example:

```yaml
- extract:
        url: ["https://gitlab.com/example/foo"]
        token: tokenA
- extract:
        url: ["https://gitlab.com/example/bar"]
        token: tokenB
- load:
        input: [example.rdf]
- pseudonymize:
- combine:
- save:
        output: combined
        format: [json, rdf, xml, dot]
- stats:
        fine: true
        explain: true
        formatter: table
```

The config file example is functionally equivalent to this command line invocation:

```
gitlab2prov extract -u https://gitlab.com/example/foo -t tokenFoo \
            extract -u https://gitlab.com/example/bar -t tokenBar \
            load -i example.rdf                                   \
            pseudonymize                                          \
            combine                                               \
            save -o combined -f json -f rdf -f xml -f dot         \
            stats --fine --explain --formatter table
```

### 🎨 Provenance Output Formats

`gitlab2prov` supports output formats that the [`prov`](https://github.com/trungdong/prov) library provides:
* [PROV-N](http://www.w3.org/TR/prov-n/)
* [PROV-O](http://www.w3.org/TR/prov-o/) (RDF)
* [PROV-XML](http://www.w3.org/TR/prov-xml/)
* [PROV-JSON](http://www.w3.org/Submission/prov-json/)
* [Graphviz](https://graphviz.org/) (DOT)

## 🤝 Contributing

Contributions and pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

## ✨ How to cite

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

## ✏️ References

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

## 📜 Dependencies 
`gitlab2prov` depends on several open source packages that are made freely available under their respective licenses.

| Package                                                         | License                                                                                                                   |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| [GitPython](https://github.com/gitpython-developers/GitPython)  | [![License](https://img.shields.io/badge/License-BSD_3--Clause-orange.svg)](https://opensource.org/licenses/BSD-3-Clause) |
| [click](https://github.com/pallets/click)                       | [![License](https://img.shields.io/badge/License-BSD_3--Clause-orange.svg)](https://opensource.org/licenses/BSD-3-Clause) |
| [python-gitlab](https://github.com/python-gitlab/python-gitlab) | [![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)       |
| [prov](https://pypi.org/project/prov/)                          | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)               |
| [jsonschema](https://github.com/python-jsonschema/jsonschema)   | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)               |
| [ruamel.yaml](https://pypi.org/project/ruamel.yaml/)            | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)               |
| [pydot](https://github.com/pydot/pydot)                         | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)               |

## 📝 License
This project is [MIT](https://github.com/dlr-sc/gitlab2prov/blob/master/LICENSE) licensed.  
Copyright © 2019 German Aerospace Center (DLR) and individual contributors.
