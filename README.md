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
under [project] dependencies - you should pin a version you have built and tested with:
```python
[project]
dependencies = ["climb-onyx-client", "onyx-analysis-helper@git+https://github.com/ukhsa-collaboration/onyx-analysis-helper.git@1.0.0"]
```

## Usage
- [I want to use the decorator for my Onyx query](##Onyx-Query-Decorator)
- [I want to use a default query function](##Query-onyx-using-provided-function)
- [I want to create analysis tables](##Create-analysis-tables)


## Onyx Query Decorator
The onyx query decorator is a simple function decorator that can be added to functions that query onyx.

The decorator will:
- automatically run 3 retries if connection cannot be established, with 5 second pauses between tries.
- write neat logging messages to the logger with name 'onyx_analysis_helper'.
- silence exceptions by default, and return the record or response and an exitcode.

### Use

To use the onyx query decorator, first import the library (possibly just the wrapper):
```python
from onyx_analysis_helper.onyx_analysis_helper_functions import call_to_onyx
```

Then wrap your function using the decorator notation:
```python
@call_to_onyx
def this_is_my_query_function(id, server):
    record = onyx_client.get(id=id, server=server)
    return record, exitcode
```

Note that the decorator returns two things - the record/data that the client method returns, and an exitcode, which is an integer where 0 is success and 1 is fail. __Your function must return both.__

### I don't want to silence exceptions...

Your function can take `silence` as a keyword argument. The decorator by default sets this to True,
but an argument can overwrite this. Then any exceptions will be raised. An exitcode code will still be returned if no exceptions are raised.

For example:

```python
@call_to_onyx
def this_is_my_query_function(id, server, silence=False):
    exitcode = 0
    record = onyx_client.get(id=id, server=server)
    return record, exitcode
```
When the function is called like so:
```
this_is_my_query_function("id=123", "myserver")
```
then any exceptions will be raised by the wrapper.

## Query onyx using provided function
There are some onyx query functions already written in the onyx analysis helper functions. These already use the decorator as above.

To use these, import onyx analysis helper functions from the library, then use the function as below.


```python
from onyx_analysis_helper.onyx_analysis_helper.functions import (
    query_onyx,
    get_data_and_versions_from_onyx,
    get_analysis_records
)
```

| function   | arguments                          | what it does |
|------------|------------------------------------|--------------|
| query_onyx | sample_id: str, server: str, silence: bool = True | Query onyx using OnyxClient.get for single sample and specified server. |
| get_data_and_versions_from_onyx | sample_id: str, server: str, fields: list or None, silence: bool = True | Query onyx for specific climb id and server, then handle versions from Onyx and return just fields of interest if supplied.  |
| get_analysis_records | sample_id: str, server: str, fields: list, silence: bool = True | Query onyx to get all analysis tables associated with a given sample ID on a given server. |

## Create analysis tables

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

# Add methods information. The onyx_analysis.methods attribute holds
# a dictionary and is populated with two distinct methods. If you want to add commands, thresholds
# or any other information, use add_methods and supply a dictionary of items to add:
methods_fail = onyx_analysis.add_methods(
    methods_dict={
        "thresholds": {"limit": 10, "filter": 5},
        "command": "my_command.sh --args"
    }
)

        # What will 'methods' now look like in the analysis table?
            {"methods": {
                "thresholds": {"limit": 10, "filter": 5},
                "command": "my_command.sh --args"
                }
            }

# If you want to add any versions of anything, you must use the "add_versions_to_methods" method.
# This can be used without using add_methods beforehand. In this example, the above code runs first,
# then this runs:
methods_versions_fail = onyx_analysis.add_versions_to_methods(
    tool_versions = {"my_dependency_version": pkg.__version__, "other_tool": "2.0.0"},
    # This is optional and defaults to False:
    include_versions_hash = True)

        # What will methods now look like?
        {"methods": {
            "thresholds": {"limit": 10, "filter": 5},
            "command": "my_command.sh --args"
            "versions": [
                {"name": "my_dependency_version", "version": "1.0.0"},
                {"name": "other_tool", "version": "2.0.0"}
            ],
            "versions_hash": "<some_other_long_hash>"
            }
        }

# If you want to include versions that are stored in Onyx, you must have retrieved the versions when
# you first queried onyx for the data being analysed. (There is a function in the onyx analysis
# helper that will do this.)

# When adding the onyx versions to the method attribue, a hash is created and stored in the methods
# dict with the key 'onyx_versions_hash'.

# Setting 'include_versions_hash' to True will add an additional hash of all the versions supplied
# and subsequently stored in 'versions'.

# This method can be used many times or done in one method call, as in this example:

# Query the data using the onyx analysis helper function:
onyx_record, onyx_versions, exitcode = get_data_and_versions_from_onyx(sample_id="ID-123456", server="server")
# In this case, the onyx_versions is a list of dicts that looks like this:
[
    {"name": "database_from_onyx", "version": "1.0.0"},
    {"name": "tool_version_from_onyx", "version": "1.0.0"}
]

methods_versions_fail = onyx_analysis.add_versions_to_methods(
        onyx_versions = onyx_versions,
        # this is optional:
        tool_versions = {"my_dependency_version": pkg.__version__, "other_tool": "2.0.0"},
        # this is optional and defaults to False:
        include_versions_hash = True
   )

        # What does this now look like?
        {"methods": {
            "thresholds": {"limit": 10, "filter": 5},
            "command": "my_command.sh --args"
            "versions": [
                {"name": "my_dependency_version", "version": "1.0.0"},
                {"name": "other_tool", "version": "2.0.0"}
                {"name": "database_from_onyx", "version": "1.0.0"},
                {"name": "tool_version_from_onyx", "version": "1.0.0"}
            ],
            "onyx_versions_hash": "<some_long_hash>"
            "versions_hash": "<some_other_long_hash>"
            }
        }
# NOTE: the onyx_versions_hash ONLY pertains to the onyx versions, in this case:
# [{"name": "database_from_onyx", "version": "1.0.0"}, {"name": "tool_version_from_onyx", "version": "1.0.0"}]


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
if any([methods_fail, methods_versions_fail, versions_hash_fail, results_fail, output_fail, required_field_fail, attribute_fail]):
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

__IMPORTANT__

The `publish_analysis` argument here sets the `is_published` field in the analysis record, which is
a field that Onyx uses as a toggle for visibility of the record in Onyx. In other words, when
`is_published` is set to false, the record is not visibile in Onyx. This allows initial pushing of
analysis record to Onyx to allocate the analysis ID, and then allows the record to be changed, added
to etc. before making it available in Onyx.

It is important to note that any attributes (which correspond to fields in the onyx analysis record)
set in the onyx_analysis helper when running onyx_analysis.update_onyx_analysis will overwrite any
fields that might already by in onyx for the given analysis_id.

Note also that the `is_published` attribute is only set by the `update_onyx_analysis` and
`write_analysis_to_onyx` methods. I the attribute is set any other way before running these methods,
these methods will overwrite that attribute.
