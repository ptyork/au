# `au` CLI Installation

The `au` command line interface (CLI) has the following tool dependencies:

 - python (>= 3.12)
 - pipx or pip (python package managers)
 - git (Git command line interface)
 - gh (GitHub command line interface)

If you already have these installed and configured, then you can skip directly
to the [Install `au-tools` section](#install-au-tools).

## Install Dependencies

If you don't already have Python version 3.12 or higher installed, then you will
need to do so. This process differs significantly between platforms, so will be
beyond the scope of this guide.

Likewise, Python's `pip` package installer is required, but its installation can
differ significantly between platforms. Just be sure that `python --version`
(substitute `python3` if appropriate on your platform) and `python -m pip
--version` show a python version of 3.12 or greater.

### Install `git` and `gh` CLI tools

The `au` commandline tool makes extensive "behind the scenes" use of both the
`git` and `gh` command line tools. As such, you should insure that these tools
are installed in your environment of choice. For example:

=== "Windows 11"
    Using the `winget` from the terminal:
    ``` cmd
    winget install Git.Git
    winget install GitHub.cli
    ```
=== "MacOS"
    Using [Homebrew](https://brew.sh) from the terminal:
    ``` ksh
    brew install git
    brew install gh
    ```
=== "Ubuntu/Debian"
    Using `apt` from the terminal:
    ``` bash
    sudo apt update
    sudo apt install git
    sudo apt install gh
    ```

### Additional System Dependencies for Database Support

If you plan to use the SQL database features (MySQL/MariaDB, PostgreSQL, or
Microsoft SQL Server), you'll need to install additional system-level packages:

=== "Ubuntu/Debian"
    
    If you are having compilation issues you may need to install libpq-dev:
    
    ``` bash
    sudo apt update
    sudo apt install libpq-dev
    ```

    **Note:** Microsoft SQL Server support (`mssql-python`) may require additional system dependencies on some Linux distributions. If you encounter installation issues, please refer to the [official mssql-python installation guide](https://github.com/microsoft/mssql-python#installation).

=== "MacOS"
    Using [Homebrew](https://brew.sh):
    ``` bash
    # For PostgreSQL support (optional, only if having compilation issues)
    brew install postgresql
    ```

    **Note:** Microsoft SQL Server support (`mssql-python`) may require additional system dependencies. If you encounter installation issues, please refer to the [official mssql-python installation guide](https://github.com/microsoft/mssql-python#installation).

=== "Windows 11"
    Windows typically doesn't require additional system packages for PostgreSQL or Microsoft SQL Server support.

    **Note:** If you encounter installation issues with `mssql-python`, please refer to the [official mssql-python installation guide](https://github.com/microsoft/mssql-python#installation).

### Configure `git`

If you've never configured the `git` CLI tool, now is the time. You must
minimally identify yourself when committing to a repository, so configure your
identity as follows:

``` bash
git config --global user.name "John Doe"
git config --global user.email johndoe@example.com
```

You should verify you configured things correctly by listing your global
configuration:

``` bash
git config --list --global
```

### Authenticate using `gh`

In the past, managing authentication with GitHub using the `git` CLI was
somewhat painful. Fortunately, the GitHub's CLI makes this process mostly
transparent now. The process is outlined in detail in the [GitHub
documentation](https://docs.github.com/en/get-started/git-basics/caching-your-github-credentials-in-git?utm_source=Blog).
However, in short you simply need to do the following.

 1. From the terminal, run:
    ``` bash
    gh auth login
    ```
 2. Select "GitHub.com" as the account to login to
 3. Choose HTTPS as the preferred protocol
 4. Select Y to authenticate Git with your GitHub credentials
 5. Choose to "Login with a web browser"
    - copy the one-time code
    - open the browser (note that if a default web browser cannot be opened  you
      simply need to open a browser window to
      [https://github.com/login/device](https://github.com/login/device))
    - login to GitHub if needed
    - Paste in your one-time code
    - Click the "Authorize github" button
      (_If using a Passkey you may be required to use it at this point_)
 6. The process is now complete, and the gh command in the terminal should now
    show you as logged in.

To test your configuration, you can run `git clone [PRIVATE_REPO_URL]` and
ensure that you are not prompted for a user id or password. If not, then you
have successfully authenticated both `git` and `gh` and you can continue to
install and use `au`.

## Install `au-tools`

Currently the `au` CLI is only installable using Python's `pip` installer or the
`pipx` package manager. `pipx` automatically uses virtual environments to
isolate the `au` CLI from the rest of your local Python environment, so this is
the recommended approach.

### Installation via `pipx`

First you must install `pipx`. You can consult the [full `pipx`
documentation](https://pipx.pypa.io/stable/installation/). But in short, you
should run something similar to the following to install `pipx`.

=== "Most Platforms"
    Assuming `pip` is installed (substitute `pip3` if appropriate):
    ``` bash
    pip install pipx
    pipx ensurepath```
    ```
=== "Ubuntu (>= 23.04)"
    ``` bash
    sudo apt update
    sudo apt install pipx
    pipx ensurepath
    ```

Once installed, `pipx` usage is quite similar to most other package managers.
To install the `au` CLI, you can now simply `pipx install` it in the terminal:

``` bash
pipx install au-tools
```

### Installation via `pip` (_not recommended_)

Though slightly simpler, this method is not recommended as it installs the `au`
CLI and all of its dependencies as global- or user-level Python packages. This
tends to "pollute" your core Python environment and can cause issues with
package interdependency and version conflicts. In fact, the latest releases of
most Linux distributions simply disallow installing packages via pip unless you
are doing so inside of a virtual environment.

However, if you do wish to proceed with this option and/or you have manually
configured a Python virtual environment, then simply `pip install` it from the
terminal:

``` bash
pip install au-tools
```

## Upgrading `au`

Upgrades to the `au` cli will be published regularly to the PyPI.org repository. Thus, upgrading your installation requires simply telling your package manager to check for and install upgrades.

=== "pipx"
    ``` bash
    pipx upgrade au-tools
    ```
=== "pip"
    ```bash
    pip install --upgrade au-tools
    ```

## Other Recommended Tools

### VisiData

[VisiData](https://www.visidata.org) is an amazing terminal-based tool for
analyzing data. Although total overkill, it's lightning fast to start up and a
great way to view CSV files (like course rosters and grades).

Install is also quite simple. And I again recommend `pipx`, though `pip` works
just fine, as well.

=== "pipx"
    ``` bash
    pipx install visidata
    ```
=== "pip"
    ```bash
    pip install visidata
    ```
