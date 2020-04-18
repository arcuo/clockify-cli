# Clockify-Cli
A command line interface for the time tracker app [Clockify](https://clockify.me/). 

Updated from [t5](https://github.com/t5/clockify-cli) to work with current API (April 2020).
Added extra methods and removed password and email environment variables as these are not necessary.

## Usage 
```
Usage: clockify [OPTIONS] COMMAND [ARGS]...

  Clockify terminal app

Options:
  --verbose  Enable verbose output
  --help     Show this message and exit.
Commands:
  start          Start a new time entry
  finish         Finish an on-going time entry
  entry          Add entry with duration
  entries        Show previous 10 time entries
  projects       Show all projects
  workspaces     Show all workspaces
  set_workspace  Set the default workspace
  set_project    Set the default project
  user           Get user information
  remove_entry   Remove entry
  in-progress    Get timer in progress
```
To access the usage help for the various subcommands:
```
> clockify start --help
Usage: clockify start [OPTIONS] WORKSPACE DESCRIPTION

Options:
  --billable          Set if entry is billable
  -p, --project TEXT  Project ID
  -g, --tag TEXT      Multiple tags permitted
  --help              Show this message and exit.
```
## Installation
Move to the main directory that contains setup.py
```
pip install -e .
```
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
