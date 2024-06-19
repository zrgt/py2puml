<div align="center">
  <a href="https://www.python.org/psf-landing/" target="_blank">
    <img width="350px" alt="Python logo"
      src="https://www.python.org/static/community_logos/python-logo-generic.svg" />
  </a>
  <a href="https://plantuml.com/" target="_blank">
    <img width="116px" height="112px" alt="PlantUML logo" src="https://cdn-0.plantuml.com/logoc.png" style="margin-bottom: 40px" vspace="40px" />
  </a>
  <h1>Python AAS Meta to PlantUML</h1>
</div>

Generate PlantUML class diagrams to document your Python application.

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lucsorel/py2puml/main.svg)](https://results.pre-commit.ci/latest/github/lucsorel/py2puml/main)


`pyaas2puml` uses [pre-commit hooks](https://pre-commit.com/) and [pre-commit.ci Continuous Integration](https://pre-commit.ci/) to enforce commit messages, code formatting and linting for quality and consistency sake.
See the [code conventions](#code-conventions) section if you would like to contribute to the project.


# How it works

`pyaas2puml` produces a class diagram [PlantUML script](https://plantuml.com/en/class-diagram) representing classes properties (static and instance attributes) and their relations (composition and inheritance relationships).

`pyaas2puml` internally uses code [inspection](https://docs.python.org/3/library/inspect.html) (also called *reflexion* in other programming languages) and [abstract tree parsing](https://docs.python.org/3/library/ast.html) to retrieve relevant information.

## Minimum Python versions to run py2puml

`pyaas2puml` uses some code-parsing features that are available only since **Python 3.8** (like [ast.get_source_segment](https://docs.python.org/3/library/ast.html#ast.get_source_segment)).
If your codebase uses the `int | float` syntax to define optional types, then you should use Python 3.10 to run `pyaas2puml`.

To sum it up, use at least Python 3.8 to run pyaas2puml, or a higher version if you use syntax features available only in higher versions.

The [.python-version](.python-version) file indicates the Python version used to develop the library.
It is a file used by [pyenv](https://github.com/pyenv/pyenv/) to define the binary used by the project.

## Features

From a given path corresponding to a folder containing Python code, `py2puml` processes each Python module and generates a [PlantUML script](https://plantuml.com/en/class-diagram) from the definitions of various data structures using:

* **[inspection](https://docs.python.org/3/library/inspect.html)** and [type annotations](https://docs.python.org/3/library/typing.html) to detect:
  * static class attributes and [dataclass](https://docs.python.org/3/library/dataclasses.html) fields
  * fields of [namedtuples](https://docs.python.org/3/library/collections.html#collections.namedtuple)
  * members of [enumerations](https://docs.python.org/3/library/enum.html)
  * composition and inheritance relationships (between your domain classes only, for documentation sake).
The detection of composition relationships relies on type annotations only, assigned values or expressions are never evaluated to prevent unwanted side-effects

* parsing **[abstract syntax trees](https://docs.python.org/3/library/ast.html#ast.NodeVisitor)** to detect the instance attributes defined in `__init__` constructors

`pyaas2puml` outputs diagrams in PlantUML syntax, which can be:
* versioned along your code with a unit-test ensuring its consistency (see the [test_py2puml.py's test_py2puml_model_on_py2uml_domain](tests/py2puml/test_py2puml.py) example)
* generated and hosted along other code documentation (better option: generated documentation should not be versioned with the codebase)

To generate image files, use the PlantUML runtime, a docker image of the runtime (see [think/plantuml](https://hub.docker.com/r/think/plantuml)) or of a server (see the CLI documentation below)

If you like tools related with PlantUML, you may also be interested in this [lucsorel/plantuml-file-loader](https://github.com/lucsorel/plantuml-file-loader) project:
a webpack loader which converts PlantUML files into images during the webpack processing (useful to [include PlantUML diagrams in your slides](https://github.com/lucsorel/markdown-image-loader/blob/master/README.md#web-based-slideshows) with RevealJS or RemarkJS).

# Install

Install from [PyPI](https://pypi.org/project/py2puml/):

* with `pip`:

```sh
pip install git+https://github.com/zrgt/pyaas2puml.git
```

# Usage

## CLI

Once `pyaas2puml` is installed at the system level, an eponymous command is available in your environment shell.

For example, to create the diagram of the classes used by `pyaas2puml`, run:

```sh
pyaas2puml pyaas2puml/domain pyaas2puml.domain
```

This outputs the following PlantUML content:

```plantuml
@startuml
skinparam classAttributeIconSize 0
hide methods

class umlclass.UmlAttribute {
}
class umlclass.UmlClass {
}
class umlitem.UmlItem {
}
class umlenum.Member {
}
class umlenum.UmlEnum {
}
enum umlrelation.RelType <<enumeration>> {
  *--
  -->
  ..>
  <|--
}
class umlrelation.UmlRelation {
}
umlclass.UmlClass ..> umlclass.UmlAttribute
umlitem.UmlItem <|-- umlclass.UmlClass
umlenum.UmlEnum ..> umlenum.Member
umlitem.UmlItem <|-- umlenum.UmlEnum
umlrelation.UmlRelation ..> umlrelation.RelType
@enduml
```

Using PlantUML, this content is rendered as in this diagram:

![py2puml domain UML Diagram](http://www.plantuml.com/plantuml/png/TP0_QiKm3CPtdK9pmQO72E6Lqk4DNLxR0pY98AQs4snbw9_UlR89XJZk8Wlzf4_-T4bi8c_UGNgtOJNHU1oTIUc1ETfXOxgEItYnduJtCDk9q1FFovG0IXlAQ4dqctT_C_W5Fmt-c9CZiqm-ewkyHq9Xy_gP_42n0MJaITv2SY63ICwmNOA-aNlzM0cxBYEAfThtqenufvH4fNg9MkVOVKjfrp_8o8xRdfSzPoiYq3u0rDRoalCjeBOZWfNtjb8r1_zzM_HQbu4BXKdglm00)

For a full overview of the CLI, run:

```sh
pyaas2puml --help
```

The CLI can also be launched as a python module:

```sh
python -m pyaas2puml pyaas2puml/domain pyaas2puml.domain
```

## Python API

See an example in the [main.py](main.py).


# Tests

```sh
# directly with poetry
poetry run pytest -v

# in a virtual environment
python3 -m pytest -v
```

Code coverage (with [missed branch statements](https://pytest-cov.readthedocs.io/en/latest/config.html?highlight=--cov-branch)):

```sh
poetry run pytest -v --cov=pyaas2puml --cov-branch --cov-report term-missing --cov-fail-under 93
```

# Licence

Unless stated otherwise all works are licensed under the [MIT license](http://spdx.org/licenses/MIT.html), a copy of which is included [here](LICENSE).

# Contributions

* [Luc Sorel-Giffo](https://github.com/lucsorel)
* [Doyou Jung](https://github.com/doyou89)
* [Julien Jerphanion](https://github.com/jjerphan)
* [Luis Fernando Villanueva Pérez](https://github.com/jonykalavera)
* [Konstantin Zangerle](https://github.com/justkiddingcode)
* [Igor Garmaev](https://github.com/zrgt)

## Pull requests

Pull-requests are welcome and will be processed on a best-effort basis.

Pull requests must follow the guidelines enforced by the `pre-commit` hooks:

- commit messages must follow the Angular conventions enforced by the `commitlint` hook
- code formatting must follow the conventions enforced by the `isort` and `ruff-format` hooks
- code linting should not detect code smells in your contributions, this is checked by the `ruff` hook

Please also follow the [contributing guide](CONTRIBUTING.md) to ease your contribution.

## Code conventions

The code conventions are described and enforced by [pre-commit hooks](https://pre-commit.com/hooks.html) to maintain consistency across the code base.
The hooks are declared in the [.pre-commit-config.yaml](.pre-commit-config.yaml) file.

Set the git hooks (pre-commit and commit-msg types):

```sh
poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

Before committing, you can check your changes with:

```sh
# put all your changes in the git staging area
git add -A

# all hooks
poetry run pre-commit run --all-files

# a specific hook
poetry run pre-commit run ruff --all-files
```

### Commit messages

Please, follow the [conventions of the Angular team](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#-commit-message-format) for commit messages.
When merging your pull-request, the new version of the project will be derived from the messages.

### Code formatting

This project uses `isort` and `ruff-format` to format the code.
The guidelines are expressed in their respective sections in the [pyproject.toml](pyproject.toml) file.

### Best practices

This project uses the `ruff` linter, which is configured in its section in the [pyproject.toml](pyproject.toml) file.

# Current limitations

* regarding **inspection**

  * type hinting is optional when writing Python code and discarded when it is executed, as mentionned in the [typing official documentation](https://docs.python.org/3/library/typing.html). The quality of the diagram output depends on the reliability with which the type annotations were written

  > The Python runtime does not enforce function and variable type annotations. They can be used by third party tools such as type checkers, IDEs, linters, etc.

* regarding the detection of instance attributes with **AST parsing**:
  * only constructors are visited, attributes assigned in other functions won't be documented
  * attribute types are inferred from type annotations:
    * of the attribute itself
    * of the variable assigned to the attribute: a signature parameter or a locale variable
    * to avoid side-effects, no code is executed nor interpreted
