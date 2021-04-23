# :seedling: `gitlab2prov`: Extract Provenance from GitLab Projects 

[![License: MIT](https://img.shields.io/github/license/dlr-sc/gitlab2prov?label=License)](https://opensource.org/licenses/MIT) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![PyPI version fury.io](https://badge.fury.io/py/gitlab2prov.svg)](https://pypi.python.org/pypi/gitlab2prov/) [![DOI](https://zenodo.org/badge/215042878.svg)](https://zenodo.org/badge/latestdoi/215042878) 

`gitlab2prov` is a Python library and command line tool for extracting provenance information from GitLab projects.  

The data model employed by `gitlab2prov` has been modelled according to [W3C PROV](https://www.w3.org/TR/prov-overview/) specification.  
A representation of the model can be found in `\docs`.

**Note: Work in progress. Expect breaking changes until v1.0**.

## Installation :wrench:

Clone the project and use the provided `setup.py` to install `gitlab2prov`.

```bash
python setup.py install --user
```

## Usage :computer:

`gitlab2prov` can be used either as a command line script or as a Python lib.

To extract provenance from a project, follow these steps:
| Instructions                                                                                                                                                      | Config Option    |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| 1. Obtain an API Token for the GitLab API ([Token Guide](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#creating-a-personal-access-token)) | `--token`        |
| 2. Set the URL for the GitLab Project                                                                                                                             | `--project_urls` |
| 3. Set a rate limit for API requests                                                                                                                              | `--rate_limit`   |
| 4. Choose a PROV serialization format                                                                                                                             | `--format`       |
| 5. Choose whether to print to stdout or not                                                                                                                       | `--quiet`        |

### As a Command Line Script

`gitlab2prov` can be configured either by command line flags or by using a config file.


##### Config File :clipboard:

An example of a configuration file can be found in `config\examples`.

```ini
[GITLAB2PROV]
token = token
quiet = False
format = json
rate_limit = 10

[PROJECTS]
project_a = project_a_url
project_b = project_b_url
```

##### Command Line Flags :flags:

```
usage: GitLab2PROV [-h] [-p <string> [<string> ...]] [-t <string>] [-r <int>] [-c <string>]
                   [-f {provn,json,rdf,xml,dot}] [-q] [--aliases <string>] [--pseudonymize]

Extract provenance information from GitLab projects.

optional arguments:
  -h, --help            show this help message and exit
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
  --aliases <string>    path to agent alias mapping json file
  --pseudonymize        pseudonymize agents
```

### Provenance Output Formats

`gitlab2prov` supports output formats that the `[prov](https://github.com/trungdong/prov)` library provides:
* [PROV-N](http://www.w3.org/TR/prov-n/)
* [PROV-O](http://www.w3.org/TR/prov-o/) (RDF)
* [PROV-XML](http://www.w3.org/TR/prov-xml/)
* [PROV-JSON](http://www.w3.org/Submission/prov-json/)
* [Graphviz](https://graphviz.org/) (DOT)


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## References

**Influencial Software for `gitlab2prov`**
* Martin Stoffers: "Gitlab2Graph", v1.0.0, October 13. 2019, [GitHub Link](https://github.com/DLR-SC/Gitlab2Graph), DOI 10.5281/zenodo.3469385  

* Quentin Pradet: "How do you rate limit calls with aiohttp?", [GitHub Gist](https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741), MIT LICENSE

**Influencial Papers for `gitlab2prov`**:

* De Nies, T., Magliacane, S., Verborgh, R., Coppens, S., Groth, P., Mannens, E., & Van de Walle, R. (2013). [Git2PROV: Exposing Version Control System Content as W3C PROV](https://dl.acm.org/doi/abs/10.5555/2874399.2874431). In *Poster and Demo Proceedings of the 12th International Semantic Web Conference* (Vol. 1035, pp. 125–128).

* Packer, H. S., Chapman, A., & Carr, L. (2019). [GitHub2PROV: provenance for supporting software project management](https://dl.acm.org/doi/10.5555/3359032.3359039). In *11th International Workshop on Theory and Practice of Provenance (TaPP 2019)*.

**Papers that refer to `gitlab2prov`**:
* Andreas Schreiber, Claas de Boer (2020). [Modelling Knowledge about Software Processes using Provenance Graphs and its Application to Git-based VersionControl Systems](https://dl.acm.org/doi/10.1145/3387940.3392220). In *ICSEW'20: Proceedings of the IEEE/ACM 42nd Conference on Software Engineering Workshops* (pp. 358-359).

* Tim Sonnekalb, Thomas S. Heinze, Lynn von Kurnatowski, Andreas Schreiber, Jesus M. Gonzalez-Barahona, and Heather Packer (2020). [Towards automated, provenance-driven security audit for git-based repositories: applied to germany's corona-warn-app: vision paper](https://doi.org/10.1145/3416507.3423190). In *Proceedings of the 3rd ACM SIGSOFT International Workshop on Software Security from Design to Deployment* (pp. 15–18).

* Andreas Schreiber (2020). [Visualization of contributions to open-source projects](https://doi.org/10.1145/3430036.3430057). In *Proceedings of the 13th International Symposium on Visual Information Communication and Interaction*. ACM, USA. 
