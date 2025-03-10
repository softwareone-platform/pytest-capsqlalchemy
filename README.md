# pytest-capsqlalchemy


[![Release](https://img.shields.io/github/v/release/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/v/release/softwareone-platform/pytest-capsqlalchemy)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-capsqlalchemy)](https://img.shields.io/pypi/pyversions/pytest-capsqlalchemy)
[![Build status](https://img.shields.io/github/actions/workflow/status/softwareone-platform/pytest-capsqlalchemy/main.yml?branch=main)](https://github.com/softwareone-platform/pytest-capsqlalchemy/actions/workflows/main.yml?query=branch%3Amain)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_pytest-capsqlalchemy&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_pytest-capsqlalchemy)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_pytest-capsqlalchemy&metric=coverage)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_pytest-capsqlalchemy)
[![Commit activity](https://img.shields.io/github/commit-activity/m/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/commit-activity/m/softwareone-platform/pytest-capsqlalchemy)
[![License](https://img.shields.io/github/license/softwareone-platform/pytest-capsqlalchemy)](https://img.shields.io/github/license/softwareone-platform/pytest-capsqlalchemy)

Pytest plugin to allow capturing SQLAlchemy queries.

- **Github repository**: <https://github.com/softwareone-platform/pytest-capsqlalchemy/>
- **Documentation** <https://softwareone-platform.github.io/pytest-capsqlalchemy/>

## Getting Started

### 1. Clone the repository

First, clone the repository from GitHub:

```bash
git clone https://github.com/softwareone-platform/pytest-capsqlalchemy
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```
### 4. Run the tests

The tests require a Postgres database to be running. If you prefer to use a local database you need to edit the `.env` file with
the connection options for it. Alternatively, you can use the provided `docker-compose.yaml` to run it within docker -- all you
need to do is run:

```bash
docker compose up test_postgres -d
```

And after that to run the tests:

```bash
make test
```

### 5. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
