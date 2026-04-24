# onyx-analysis-helper

This repository contains helper functions that can be used to format
analyses ready for submission to onyx.

## Installation as standalone code

Clone repo and create environment:
`git clone git@github.com:ukhsa-collaboration/onyx-analysis-helper.git`

`conda env create -n mscape_analysis`

`conda activate mscape_analysis`

Installation for users:
`cd onyx-analysis-helper`
`pip install .`

Installation for developers (installs code in editable mode):
`cd mscape-template`
`pip install --editable '.[dev]'`

Alternatively, install directly into a suitable environment using pip without cloning first:
`pip install git+ssh://git@github.com/ukhsa-collaboration/gpha-mscape-onyx-analysis-helper.git`

## Installation in another project

To install the codebase as part of another project, add this to your pyproject.toml
under [project] dependencies:
```python
[project]
dependencies = ["climb-onyx-client", "onyx-analysis-helper@git+https://github.com/ukhsa-collaboration/onyx-analysis-helper.git"]
```

## Usage

Functionality from the repo can be imported into other code after
installation:
```python
from onyx_analysis_helper import onyx_analysis_helper_functions as oa
```

Example usage to instantiate an OnyxAnalysis object, add required information, and
check all fields are present and correct:
```python
# Instantiate the class
onyx_analysis = oa.OnyxAnalysis()

# Add details on the analysis
onyx_analysis.add_analysis_details(
    analysis_name="example-analysis",
    analysis_description="""This is an analysis to generate example statistics for samples"""
    )

# Add package metadata - takes from package name if code base is pip installed
onyx_analysis.add_package_metadata(package_name = "package-name-here")

# Add methods information. You must run add_methods first. The onyx_analysis.methods attribute holds
# a dictionary. First an onyx query gets predefined versions from the database and populates the
# "versions" key in the methods dictionary. Any additional 'tool_versions' given are also
# added to this.
methods_fail = onyx_analysis.add_methods(
    sample_id = "ID_123456",
    server_name = "scape",
    tool_versions = {'my_dependency_version': pkg.__version__})  # this is optional

        # What does that now look like?
        {"methods": {
            "versions": [
                {"name": "database_from_onyx", "version": "1.0.0"},
                {"name": "my_pkg_dependency", "version": "0.0.0"}
            ]
            }
        }

# Once versions have been populated, add a hash calculated from methods["versions"].
# This writes methods["versions_hash"] and overwrites it if called again.
versions_hash_fail = onyx_analysis.add_versions_hash_to_methods()

        # The methods dict will now also include:
        {"methods": {
            "versions_hash": "<some_long_hash>"
            }
        }

# Any additional methods can now be added to the method attribute. You must provide the methods_dict
# as a dict. With the example below, thresholds will then be added to the methods dict like this:

other_methods_fail = onyx_analysis.add_other_methods(
    methods_dict={
        "thresholds": {"limit": 10, "filter": 5}
    }
)

        # Waht does this now look like?
        {"methods": {
            "versions": [
                {"name": "database_from_onyx", "version": "1.0.0"},
                {"name": "my_pkg_dependency", "version": "0.0.0"}
            ],
            "thresholds": {"limit": 10, "filter": 5}
            }
        }

# Note that if you provide 'versions' as the key in your methods_dict argument to the method, it
# will not overwrite the versions already there, but append to that dict. You must provide "name"
# and "version" in the methods_dict arg, like this:
other_methods_fail = onyx_analysis.add_other_methods(
    methods_dict={
        "versions": {"name": "my_tool", "version": "1.0.0"}
    }
)

# Add results information e.g. QC results. Must be in dictionary format. More detailed
# results to be added in output files/report.
results_fail = onyx_analysis.add_results(top_result = headline_result, results_dict = example_results)

# Add climb ID - field is either mscape_records or synthscape_records
onyx_analysis.add_server_records(sample_id = record_id, server_name = "synthscape")

# Add location of output files. Add report field if single file provided, add outputs field
# if results directory is provided
output_fail = onyx_analysis.add_output_location(result_file)

# Check all required fields are present and that there are no invalid fields.
# Select publish_analysis = True if you are checking an analysis object ready for
# publication, publish_analysis = False if you are checking an analysis object that will
# not be published yet and so will be missing the outputs/report field
required_field_fail, attribute_fail = onyx_analysis.check_analysis_object(publish_analysis = True)

# Fail statuses can be checked and actioned as appropriate with e.g. logging, raising an
# error etc using something like:
if any([methods_fail, versions_hash_fail, other_methods_fail, results_fail, output_fail, required_field_fail, attribute_fail]):
    logging.error("Incorrect attribute in analysis object, check logs for details")
    exitcode = 1
else:
    logging.info("Correct attributes in analysis object")
    exitcode = 0
```

Example submissions of data to onyx after creating a valid onyx analysis object:
```python
# Attempt to add analysis to onyx but don't publish - if successful returns analysis id and exitcode of 0
analysis_id, exitcode = onyx_analysis.write_analysis_to_onyx(server = "synthscape",
                                                             dryrun = True,
                                                             publish_analysis = False)

# Attempt to update an existing analysis (e.g. add report or outputs field) and then publish results
analysis_id, exitcode = onyx_analysis.update_onyx_analysis(server = "synthscape",
                                                           analysis_id = "A-123",
                                                           dryrun = True,
                                                           publish_analysis = True)
```
Note the use of dryrun = True in these examples to do a test upload/update. This option
should always be used unless code is in production.
