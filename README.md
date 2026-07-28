
# GA4HPC: Green Algorithms for High Performance Computing
![Version: v1.0](https://img.shields.io/badge/version-v1.0-blue) 
[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/purple?icon=github)](https://github.com/Naereen/badges/)

> :point_right: There are many different flavours of HPC setups, so no doubt you'll find some bugs...Please let us know what you find so that we can make it work for more people! 

GA4HPC is a user-facing, terminal-based tool that generates an energy usage and carbon footprint report for your computational workloads. It implements the [Green Algorithms Methodology](https://onlinelibrary.wiley.com/doi/abs/10.1002/advs.202100707) directly on High Performing Computing (HPC) clusters. **The tool currently supports SLURM clusters only**, with an aim to expand it for other workload managers in the future. 

It works by pulling usage statistics directly from the logs recorded by the workload manager and estimating the user's carbon footprint based on this usage.
It reports a range of statistics such as energy usage, carbon footprints, compute use, memory efficiency, impact of failed jobs etc.

By default, the output gets displayed in the terminal (example below). `--output='html'` can be used to get the output as an html report instead.
![example file](https://github.com/GreenAlgorithms/GreenAlgorithms4HPC/blob/main/example_files/Screenshot%20HPC%202024-08-20.png)

### Who is it for?
This tool is intended for individual HPC users who want to generate carbon footprint and energy usage reports for their own computational workloads.

> [!NOTE]
> Looking for automated, ongoing reporting across teams or departments?
> Check out the [Green Algorithms Dashboard](https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-HPCdashboard). It automatically track aggregated usage and carbon emissions via an interactive Grafana interface. Unlike GA4HPC, which any user can run directly, the Dashboard requires setup and maintenance by a system administrator.
 
---

### Contents
* [Quick start](#quick-start)
* [Limitations to keep in mind](#limitations-to-keep-in-mind)
* [Full list of options](#full-list-of-options)
* [Installation guide](#installation-guide)
  * [Requirements](#requirements)
  * [Step-by-step](#step-by-step)
  * [Updating an existing installation](#updating-an-existing-installation)
* [Contributing](#contributing)
* [FAQ](#faq)
  * [Can it work with other workload managers?](#can-it-work-with-other-workload-managers)
* [Getting help](#getting-help)
* [About us](#about-us)
* [Licence](#licence)

## Quick start

> [!NOTE]
> GA4HPC only needs to be installed once per cluster, preferably in a shared directory so that all users can access it without installing it themselves.

:warning: Even when installed in a shared directory, each user will only ever see their own usage. However, if the HTML output is used without a custom output directory, the report itself will be saved on the shared drive (see [`--outputDir`](#full-list-of-options) below to change this).

### Is GA4HPC already installed on your cluster?

Check with your HPC team first, if it's already installed, you can run it straight away to get your own carbon footprint. No need to reinstall it.
 
Assuming it's installed under `shared_directory`, run the following on the SLURM cluster to get your carbon footprint between two dates:
 
```bash
shared_directory/myCarbonFootprint.sh --startDay 2024-01-10 --endDay 2024-08-15
```
 
If it isn't installed yet, see the [Installation guide](#installation-guide) below.

### Common options
 
The full list of options is documented [below](#full-list-of-options), but the ones you'll use most often are:
 
- `-S, --startDay` / `-E, --endDay`: restrict the logs considered, formatted as `YYYY-MM-DD`.
- `-o, --output`: `terminal` for terminal output (default) or `html` for an HTML report. When using the HTML report, a subdirectory is created for it — by default under `GreenAlgorithms4HPC/outputs/`, though this can be changed.
- `--outputDir`: path to export any output to.

## Limitations to keep in mind
 
- The workload manager doesn't always log exact CPU usage time; when this information is missing, we assume all cores are used at 100%.
- GPUs are currently assumed to be used at 100%, as the information needed for more accurate measurement isn't available.
  (Both of these assumptions may lead to slightly overestimated carbon footprints, although the order of magnitude should still be correct.)
- Conversely, wasted energy due to memory over-allocation may be largely underestimated, as the information needed for this isn't always logged.


## Full list of options
 
```
usage: __init__.py [-h] [-S STARTDAY] [-E ENDDAY] [-o OUTPUT] [--outputDir OUTPUTDIR] [--filterCWD] [--filterJobIDs FILTERJOBIDS] [--filterAccount FILTERACCOUNT] [--customSuccessStates CUSTOMSUCCESSSTATES] [--useCustomLogs USECUSTOMLOGS]
 
Calculate your carbon footprint on the server.
 
optional arguments:
  -h, --help            show this help message and exit
  -S STARTDAY, --startDay STARTDAY
                        The first day to take into account, as YYYY-MM-DD (default: <current-year>-01-01)
  -E ENDDAY, --endDay ENDDAY
                        The last day to take into account, as YYYY-MM-DD (default: today)
  -o OUTPUT, --output OUTPUT
                        How to display the results, one of 'terminal' or 'html' (default: terminal)
  --outputDir OUTPUTDIR
                        Export path for the output (default: under `outputs/`). Only used with `--output html`
  --filterCWD           Only report on jobs launched from the current location.
  --filterJobIDs FILTERJOBIDS
                        Comma separated list of Job IDs you want to filter on. (default: "all")
  --filterAccount FILTERACCOUNT
                        Only consider jobs charged under this account
  --customSuccessStates CUSTOMSUCCESSSTATES
                        Comma-separated list of job states. By default, only jobs that exit with status CD or COMPLETED are considered successful (PENDING, RUNNING and REQUEUED are ignored). Jobs with states listed here will
                        be considered successful as well (best to list both the 2-letter and full-length codes). Full list of job states: https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
  --useCustomLogs USECUSTOMLOGS
                        Bypasses the workload manager and lets you input a custom log file of your jobs. This is mostly meant for debugging, but can be useful in some situations. An example of the expected file
                        can be found at `example_files/example_sacctOutput_raw.txt`.
```

## Installation guide
 
:point_right: This only needs to be installed once per cluster — check first that someone else hasn't already installed it!
 
### Requirements
 
- Python 3.8+

### Step-by-step
 
1. Clone this repository into a shared directory on your cluster:
```bash
    $ cd shared_directory
    $ git clone https://github.com/Llannelongue/GreenAlgorithms4HPC.git
```
 
2. Open `myCarbonFootprint.sh` and find the line that creates the virtual environment; it's marked with the comment `# EDIT ME: this line needs updating to load python on your server`:
```bash
    /usr/bin/python3.8 -m venv GA_env
```
Replace it with whatever loads Python 3.8+ on your server, for example:
```bash
    module load python/3.11.7
    python -m venv GA_env
```
 
3. Make the bash script executable:
```bash
    $ chmod +x shared_directory/GreenAlgorithms4HPC/myCarbonFootprint.sh
```
 
4. Edit [`data/cluster_info.yaml`](data/cluster_info.yaml) to plug in the values corresponding to your cluster's hardware specs (this is the trickiest step). Ask your HPC team, and check the Green Algorithms GitHub for useful reference values: https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-data

5. Run the script once to set things up. This checks that the correct version of Python is available and creates the virtual environment with the required packages, based on `requirements.txt`:
```bash
    $ shared_directory/GreenAlgorithms4HPC/myCarbonFootprint.sh
```

### Updating an existing installation
 
_More elegant solutions welcome! [Discussion here](https://github.com/Cambridge-Sustainable-Computing-Lab/GreenAlgorithms4HPC/discussions/31)._
 
> [!IMPORTANT] 
> Before updating, make sure you've saved a copy of your custom `cluster_info.yaml` and noted how you loaded Python 3.8+ during the initial install.
 
1. `git reset --hard` — removes local changes to files (hence the need for a backup above!)
2. `git pull`
3. Re-apply your `cluster_info.yaml` and `myCarbonFootprint.sh` edits as described in [Step-by-step](#step-by-step).
4. `chmod +x myCarbonFootprint.sh` to make it executable again.
5. Test `myCarbonFootprint.sh`.

## Contributing

1. **Fork** the repository and clone your fork locally.
2. Create a new branch off `main` for your change:
````bash
git checkout main
git checkout -b feature/<your-feature-name>-<your-username>
````
3. Make your changes, then run `pytest .` to make sure nothing's broken.
4. Commit your changes with a clear message, push to your fork, and open a **Pull Request against `main`**.

> [!IMPORTANT]
> Please open an issue for larger changes.

## FAQ

### Can it work other other workload managers?

Yes it can! the tool uses [Green-Algorithms-core](https://github.com/Cambridge-Sustainable-Computing-Lab/Green-Algorithms-core) to pull logs from workload managers like SLURM. Please [create an issue](https://github.com/Cambridge-Sustainable-Computing-Lab/GreenAlgorithms4HPC/issues) so that our team can help you implement it for your workload manager.

---
## Getting help
If you have questions, run into issues, or want to share feedback, please open a thread in [GitHub Discussions](https://github.com/Cambridge-Sustainable-Computing-Lab/GreenAlgorithms4HPC/discussions). This is the best place to get support from the development team and the wider community.

---
## About us

This tool is built and maintained by the [Cambridge Sustainable Computing Lab](https://cam-sustainablecomputing.org) at the University of Cambridge, UK. 

---
## Licence

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

This work is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0).

