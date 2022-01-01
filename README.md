[![Shield](https://img.shields.io/docker/pulls/stacscan/stacs-ci?style=flat-square)](https://hub.docker.com/r/stacscan/stacs-ci)
[![Shield](https://img.shields.io/docker/image-size/stacscan/stacs-ci?style=flat-square)](https://hub.docker.com/r/stacscan/stacs-ci/tags?page=1&ordering=last_updated)
[![Shield](https://img.shields.io/twitter/follow/stacscan?style=flat-square)](https://twitter.com/stacscan)
<p align="center">
    <br /><br />
    <img src="./docs/images/STACS-Logo-RGB.small.png?raw=true">
</p>
<p align="center">
    <br />
    <b>Static Token And Credential Scanner</b>
    <br />
    <i>CI</i>
    <br />
</p>

## What is it?

This repository contains a set of modules to enable integration of STACS with commonly
used CI / CD systems. Currently, this repository supports:

* Github Actions
  * Fails the build on findings.
  * Automatically annotates pull-requests with findings

* Generic CI Systems
  * Fails the build on findings.
  * Outputs findings to the console in formatted plain-text.

STACS is a [YARA](https://virustotal.github.io/yara/) powered static credential scanner
which suports source code, binary file formats, analysis of nested archives, composable
rulesets and ignore lists, and SARIF reporting.

### Github Actions

This repository contains a Github action which enables running STACS as a Github
action. This can be used to identify credentials committed to both committed to Git, or
even credentials accidentally compiled into binary artifacts - such as Android APKs,
Docker images, RPM packages, ZIP files, [and more](https://github.com/stacscan/stacs/blob/main/README.md#what-does-stacs-support)!

This action automatically annotates a pull-request with findings to allow simplified
review integrated with existing code-review processes. As this integration does not use
the Github security events framework, no additional subscription to Github is required,
even for private repositories!

Additionally, this action can 'fail the build' if any static tokens and credentials are
detected.

#### Inputs

##### `scan-directory`

An optional subdirectory to scan. This allows scanning to be limited to a specific
directory under the repository root.

Defaults to the repository root.

##### `fail-build`

Defines whether this action should 'fail the build' if any static token or credentials
are detected. This will take any suppressed / ignore listed entries into account,
allowing consumers to ignore known false positives - such as test fixtures.

Defaults to `true`

#### Example Usage

The following example scans the currently checked out commit and uploads the findings
as security events to Github (see "Permissions" section below).

```yaml
uses: actions/stacscan@v1
```

The following example scans a sub-directory in the repository. In this example the 
`binaries/` sub-directory contains binary objects, compiled for release by another step
of a Github actions pipeline.

```yaml
uses: actions/stacscan@v1
with:
    scan-directory: 'binaries/'
```

The following example disables 'failing the build' if there are findings which have not
been ignored / suppressed.

```yaml
uses: actions/stacscan@v1
with:
    fail-build: false
```

#### Permissions

Please be aware that in order to annotate pull-requests with comments, the action must
also be granted `write` permissions to `pull-requests`. This can be done by adding the
following to the respective `job` in your Github actions pipeline.

```yaml
permissions:
    contents: read         # Required to read the repository contents (checkout).
    pull-requests: write   # Required to annotate pull requests with comments.
```
