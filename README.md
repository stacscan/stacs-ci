[![Shield](https://img.shields.io/github/workflow/status/stacscan/stacs-ci/Check?label=Tests&style=flat-square)](https://github.com/stacscan/stacs-ci/actions?workflow=Check)
[![Shield](https://img.shields.io/github/workflow/status/stacscan/stacs-ci/Publish?label=Deploy&style=flat-square)](https://github.com/stacscan/stacs-ci/actions?workflow=Publish)
[![Shield](https://img.shields.io/docker/pulls/stacscan/stacs-ci?style=flat-square)](https://hub.docker.com/r/stacscan/stacs-ci)
[![Shield](https://img.shields.io/docker/image-size/stacscan/stacs-ci?style=flat-square)](https://hub.docker.com/r/stacscan/stacs-ci/tags?page=1&ordering=last_updated)
![Shield](https://img.shields.io/github/license/stacscan/stacs-ci?style=flat-square)
[![Shield](https://img.shields.io/twitter/follow/stacscan?style=flat-square)](https://twitter.com/stacscan)
<p align="center">
    <br /><br />
    <img src="https://raw.githubusercontent.com/stacscan/stacs-ci/main/docs/images/STACS-Logo-RGB.small.png?raw=true">
</p>
<p align="center">
    <br />
    <b>Static Token And Credential Scanner</b>
    <br />
    <i>CI Integrations</i>
    <br />
</p>

## What is it?

STACS is a [YARA](https://virustotal.github.io/yara/) powered static credential scanner
which supports source code, binary file formats, analysis of nested archives, composable
rule-sets and ignore lists, and SARIF reporting.

This repository contains a set of modules to enable integration of STACS with commonly
used CI / CD systems. Currently, supported is:

* Github Actions
  * Fails the build on unsuppressed findings.
  * Automatically annotates pull requests with findings.
  * Automatically loads suppressions from a `stacs.ignore.json` in the root of the repository.

* Generic CI Systems
  * Fails the build on unsuppressed findings.
  * Outputs findings to the console in formatted plain-text.
  * Automatically loads suppressions from a `stacs.ignore.json` in the scan directory.

### Github Actions

This Github action enables running STACS as a Github action. This can be used to
identify credentials committed in both source code, or even credentials accidentally
compiled into binary artifacts - such as Android APKs, Docker images, RPM packages, ZIP
files, [and more](https://github.com/stacscan/stacs/blob/main/README.md#what-does-stacs-support)!

If run as part of a pull request, this action automatically annotates a pull request
with findings to allow simplified review integrated with existing code-review processes.
As this integration does not use the Github security events framework, no additional
subscription to Github is required, even for private repositories!

This action can also be used as part of a `release` event. Allowing scanning of binaries
before publishing to catch credentials which may have been accidentally generated or
included as part of the build process.

Additionally, this action can 'fail the build' if any static tokens and credentials are
detected.

#### Appearance

If STACS detects a static credential during a pull request, a review comment will be
added to the line containing the static credential:

<img src="https://raw.githubusercontent.com/stacscan/stacs-ci/main/docs/images/github_comment.png?raw=true" width="500px" alt="Github Comment of finding" />

The STACS Github integration will even check the pull request to see whether there is
an existing comment for this finding, preventing multiple comments being added to the
same pull request on subsequent commits.

If the credential is found inside of an archive, in a part of a file not modified by the
pull request, then a regular comment will be added to the triggering pull request.

#### Inputs

##### `scan-directory`

An optional sub-directory to scan, relative to the repository root. This allows scanning
to be limited to a specific directory under the repository root.

Defaults to the repository root.

##### `fail-build`

Defines whether this action should 'fail the build' if any static token or credentials
are detected. This will take any suppressed / ignore listed entries into account,
allowing consumers to ignore known false positives - such as test fixtures.

Defaults to `true`

#### Example Usage

The following example scans the currently checked out commit and adds review comments
for findings to an associated pull-request (see "Permissions" section below). If the
trigger was not a pull-request, findings will instead be printed to the console and
STACS CI will exit with a non-zero status (`100`) if unsupressed findings were present.

```yaml
uses: stacscan/stacs-ci@0.1.5
```

The following example scans a sub-directory in the repository. In this example the 
`binaries/` sub-directory contains binary objects, compiled for release by another step
of a Github actions pipeline.

```yaml
uses: stacscan/stacs-ci@0.1.5
with:
    scan-directory: 'binaries/'
```

The following example disables 'failing the build' if there are findings which have not
been ignored / suppressed.

```yaml
uses: stacscan/stacs-ci@0.1.5
with:
    fail-build: false
```

#### Permissions

Please be aware that in order to annotate pull requests with comments, the action must
also be granted `write` permissions to `pull-requests`. This can be done by adding the
following to the respective `job` in your Github actions pipeline.

```yaml
permissions:
    contents: read         # Required to read the repository contents (checkout).
    pull-requests: write   # Required to annotate pull requests with comments.
```

This is only required if running in response to `pull-request` triggers.

### Generic CI

This repository can be integrated with a number of common CI systems using the provided
Docker image, or Python module.

The pre-built Docker image greatly simplifies this process and provides a mechanism to
quickly execute a STACS scan against a given directory, print the results in an
actionable manner, and signal to the CI system that the build should fail on findings.

#### Appearance

If STACS detects a static credential, a results block will be printed to the console
with information required to identify its location:

<img src="https://raw.githubusercontent.com/stacscan/stacs-ci/main/docs/images/generic_tui.png?raw=true" width="500px" alt="Terminal output of findings" />

If the credential is found within an archive, STACS will print a file tree to allow
quick identification of exactly where the credential is.

#### Basic

The simplest form of executing the Generic CI integration can be performed using the
following Docker command from the directory to be scanned. Using this default
configuration Docker will complete with a non-zero exit code if any unsuppressed findings
are found:

```bash
docker run -it -v $(pwd):/mnt/stacs/input stacscan/stacs-ci:latest
```

To prevent a non-zero exit code on unsuppressed findings, such as for initial 'dry run'
style operation, the following command can be run:

```bash
docker run -it -e FAIL_BUILD=false -v $(pwd):/mnt/stacs/input stacscan/stacs-ci:latest
```

#### Jenkins

_To be added._

#### Circle CI

_To be added._
