#!/usr/bin/env python3

"""
Module containing OnyxAnalysis class object and associated functions
to support submission and reading of onyx analyses.
"""

# Imports - ordered (can use ruff to do this automatically)
import datetime
import importlib.metadata as metadata
import json
import logging
import os
import time
from functools import wraps
from pathlib import Path

from onyx import OnyxClient, OnyxConfig, OnyxEnv
from onyx.exceptions import OnyxClientError, OnyxConfigError, OnyxConnectionError, OnyxHTTPError

# Set up e.g. config settings
# Set up onyx config
CONFIG = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)


# Onyx query decorator
def call_to_onyx(func):
    """Decorator that provides error handling and submission attempt
    functionality for any calls to Onyx.
    """

    @wraps(func)
    def call_to_onyx_wrapper(*args, **kwargs):
        connection_attempts = 1
        success = False

        while success is False:
            try:
                logging.debug(
                    "Attempting connection to Onyx. Attempt number %s", connection_attempts
                )
                result, exitcode = func(*args, **kwargs)
                success = True
                logging.debug("Successful connection to onyx")

                return result, exitcode

            except OnyxConnectionError as exc:
                if connection_attempts < 3:
                    connection_attempts += 1
                    logging.debug("OnyxConnectionError: %s. Retrying connection in 5 seconds", exc)
                    time.sleep(5)

                else:
                    logging.error(
                        """OnyxConnectionError: %s. Connection to Onyx failed %s times,
                              exiting program""",
                        exc,
                        connection_attempts,
                    )
                    result = None
                    exitcode = 1
                    return result, exitcode

            except OnyxConfigError as exc:
                logging.error(
                    """OnyxConfigError: %s. Check credentials and details in OnyxConfig
                          are correct. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details.""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

            except OnyxClientError as exc:
                logging.error(
                    """OnyxClientError: %s. Check calls to OnyxClient are correct
                          and required arguments e.g. climb_id are present. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

            except OnyxHTTPError as exc:
                logging.error(
                    """OnyxHTTPError: %s. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc.response.json(),
                )
                result = None
                exitcode = 1
                return result, exitcode

            except Exception as exc:
                logging.error(
                    """Unhandled error: %s. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

    return call_to_onyx_wrapper


# Functions
@call_to_onyx
def _get_versions_from_onyx(sample_id: str, server: str) -> tuple[list[dict[str, str | None]], int]:
    """
    Get the various database and tool versions from Onyx.

    # TODO:
    Remove if statement.
    There is an if statement to check if all versions are in one Onyx field. Note the 'else' is then
    only required if this does not exist in Onyx, so cnce it does, this 'else' statement is
    superfluous.

    Arguments:
            sample_id -- valid climb id.
            server_name -- name of server to query.
        Returns:
            versions_dicts -- list of dicts, where the dict contains "name" and "version".
                e.g. [{"name": "tool", "version": "1.2.3"}, {"name": "db", "version": "2.3.4"}]
            exitcode -- 1 if fail 0 if pass
    """
    exitcode = 0

    with OnyxClient(CONFIG) as client:
        record: dict = client.get(project=server, climb_id=sample_id)

        versions_dicts: list[dict[str, str | None]] = []

        # Add a little check that the versions column in the db is as expected:
        if (
            (new_versions_dicts := record.get("versions"))
            and isinstance(new_versions_dicts, list)
            and isinstance(new_versions_dicts[0], dict)
        ):
            versions_dicts.extend(new_versions_dicts)
            return versions_dicts, exitcode

        # If 'versions' field not available in onyx, then define our own versions to get from onyx:
        versions_to_get = [
            "classifier_version",
            "classifier_db_date",
            "ncbi_taxonomy_date",
            "scylla_version",
            "sylph_db_version",
            "alignment_db_version",
        ]
        for ver in versions_to_get:
            versions_dicts.append({"name": ver, "version": record.get(ver)})

        return versions_dicts, exitcode


class OnyxAnalysis:
    def __init__(self):
        self.analysis_date: datetime.datetime
        self.name: str
        self.description: str
        self.pipeline_name: str
        self.pipeline_url: str
        self.pipeline_version: str
        self.pipeline_command: str | None
        self.methods: dict[str, list[dict[str, str | None]]]
        self.result: str
        self.result_metrics: dict
        self.report: Path | None
        self.outputs: Path | None
        self.upstream_analyses: str | None
        self.downstream_analyses: str | None
        self.identifiers: list[str] = []

    def add_analysis_details(self, analysis_name: str, analysis_description: str) -> None:
        """Adds analysis details to onyx analysis object. Sets analysis date
        if not already specified.
        """
        self.name = analysis_name
        self.description = analysis_description
        self._set_analysis_date()

    def add_package_metadata(self, package_name: str) -> None:
        "Adds package metadata to onyx analysis object"
        package_metadata = dict(metadata.metadata(package_name))
        self.pipeline_name = package_metadata["Name"]
        self.pipeline_version = package_metadata["Version"]
        self.pipeline_url = package_metadata["Project-URL"].split(", ")[
            1
        ]  # Get url from toml - add to template

    def add_methods(
        self,
        sample_id: str,
        server_name: str,
        tool_versions: dict | None = None,
    ) -> bool:
        """
        Queries Onyx for various predefined tool and database versions, and populates the methods
        dict. Also added in any additional tool_versions supplied.

        Arguments:
            sample_id -- valid climb id.
            server_name -- name of server to query.
            tool_versions -- optional; dict of other versions to put into the versions dict in the
                methods. Must be in format {'tool_name': 'version'}
        Returns:
            methods_fail -- bool, False if successful, True if fail
        """
        methods_fail = False

        # First prepopulate the methods dict.
        versions_dicts, exitcode = _get_versions_from_onyx(sample_id=sample_id, server=server_name)

        if exitcode != 0:
            logging.error(
                "Error: Onyx cannot query sample-ID for versions to pre-populate the methods dict."
            )
            methods_fail = True
            return methods_fail

        # Add any additional tool or database versions that need to go into the analysis table.
        if tool_versions:
            for tool, version in tool_versions.items():
                versions_dicts.append({"name": tool, "version": version})

        self.methods: dict[str, dict] = {"versions": versions_dicts}
        # methods did not fail
        return methods_fail

    def add_other_methods(self, methods_dict: dict) -> bool:
        """
        CANNOT USE BEFORE SETTING METHOD ATTRIBUTE WITH add_methods().

        Attempts to add methods to existing onyx analysis object. If methods are invalid, returns
        methods_fail.

        Arguments:
            method_dicts: dict containing methods to add. Recommended to be nested.
                e.g.: {"thresholds": {"cutoff": 1, "limit": 2}}.
                If the first key is 'versions', this will append to the exisiting 'versions' dict
                in the methods attribute. The inner dict must then look like this:
                e.g.: {"versions": {"name": "thing_to_version", "version": "1.2.3"}}
        Returns:
            methods_fail: true if fail, check logging message.
        """
        methods_fail = False
        # methods attribute has to be available.
        if not hasattr(self, "methods"):
            logging.error("Error: instance has no 'methods' attribute. Use add_methods() first.")
            methods_fail = True
            return methods_fail

        if not isinstance(methods_dict, dict):
            logging.error("Error: Methods must be in dict format.")
            methods_fail = True
            return methods_fail

        for method_name, method_params in methods_dict.items():
            if method_name == "versions":  # avoid overwriting 'versions'
                if "name" not in method_params or "version" not in method_params:
                    methods_fail = True
                    logging.error(
                        "Error: Trying to append versions in method attribute, but "
                        "provided methods_dict does not contain 'name' and 'versions'."
                    )
                    return methods_fail
                self.methods["versions"].append(method_params)
                return methods_fail

            self.methods[method_name] = method_params
        return methods_fail

    def add_results(self, top_result: str, results_dict: dict) -> bool:
        """Attempts to add results to analysis object. If results are
        invalid, returns results_fail.
        """
        if isinstance(results_dict, dict):
            self.result = top_result
            self.result_metrics: dict = results_dict
            results_fail = False
        else:
            logging.error("Error: result_metrics must be in dict format")
            results_fail = True

        return results_fail

    def add_server_records(self, sample_id: str, server_name: str) -> None:
        """Creates records field for appropriate server e.g. "mscape_records"
        and adds sample_id to this field.
        """
        server_records = f"{server_name}_records"
        setattr(self, server_records, [sample_id])

    def add_output_location(self, result_path: Path) -> bool:
        """Adds result location to analysis object. If results are in a
        file, adds a report field. If results are in a folder, adds
        an outputs field.
        """
        outputs_fail = False
        if Path(result_path).is_dir():
            self.outputs = result_path
        elif Path(result_path).is_file():
            self.report = result_path
        else:
            outputs_fail = True

        return outputs_fail

    # Private methods for creating new analysis object
    def _set_analysis_date(self) -> None:
        "Checks if analysis date is present and sets today's date if it isn't"
        if not hasattr(self, "analysis_date"):
            self.analysis_date = datetime.datetime.now().date().isoformat()

    # Add in function to set s3 output path, other optional fields
    # Create analysis in Onyx
    @call_to_onyx
    def write_analysis_to_onyx(
        self, server: str, dryrun: bool, publish_analysis: bool
    ) -> tuple[str, int]:
        """Attempts to add onyx analysis to object.
        Arguments:
            server -- Server submitting data to
            dryrun -- Specify if test or real upload to onyx
            publish -- Specify if analysis should be published. Set to true is all fields complete, false if additional fields e.g. outputs needs adding before publication of analysis
        Returns:
            result -- Analysis ID if valid submission, {} if test upload,
                      None if upload fails
            exitcode -- 0 if successful, 1 if fail
        """
        self.is_published = publish_analysis

        with OnyxClient(CONFIG) as client:
            result = client.create_analysis(project=server, fields=vars(self), test=dryrun)
        exitcode = 0

        return result, exitcode

    # Write analysis object to json
    def write_analysis_to_json(self, result_file: Path) -> Path | None:
        "Writes onyx analysis object to json"
        fields_dict = vars(self)
        # make sure all attributes are json strings:
        fields_dict["methods"] = json.dumps(self.methods)
        fields_dict["result_metrics"] = json.dumps(self.result_metrics)

        with Path(result_file).open("w") as file:
            json.dump(fields_dict, file)

        return result_file

    # Check fields and attributes are valid
    def check_analysis_object(self, publish_analysis: bool) -> list[str]:
        """Performs checks on an analysis object to ensure required fields
        are present and that there are no invalid attributes. Runs additional
        check on the outputs being present if analysis is to be published.
        """
        # Set up list to store fail statuses
        status_list = []

        # Check all required fields are present and add status to list
        required_field_fail = self._check_required_fields()
        status_list.append(required_field_fail)

        # Check attributes are present and add status to list
        attribute_fail = self._check_analysis_attributes()
        status_list.append(attribute_fail)

        # If analysis is to be published, check outputs or report field present
        if publish_analysis:
            output_field_fail = self._check_required_outputs()
            status_list.append(output_field_fail)

        return status_list

    def _check_required_fields(self) -> bool:
        "Checks all required fields are present, returns True if fields missing"
        fields_dict = vars(self)
        missing_field = False
        required_fields = [
            "analysis_date",
            "name",
            "pipeline_name",
            "pipeline_version",
            "result",
            "identifiers",
        ]
        if not all(field in fields_dict for field in required_fields):
            missing_fields = [field for field in required_fields if field not in fields_dict]
            logging.error("Missing required fields: %s", missing_fields)
            missing_field = True

        return missing_field

    def _check_required_outputs(self) -> bool:
        "Checks output field is present, returns True if missing"
        fields_dict = vars(self)
        missing_output = False
        output_fields = ["report", "outputs"]

        if not any(field in output_fields for field in fields_dict):
            logging.error("Fields dict must contain one of: %s", output_fields)
            missing_output = True

        return missing_output

    def _check_analysis_attributes(self) -> bool:
        "Checks all attributes are valid onyx fields, return True if invalid fields present"

        analysis_dict = vars(self)
        attribute_fail = False

        valid_attributes = [
            "published_date",
            "site",
            "analysis_id",
            "analysis_date",
            "name",
            "description",
            "pipeline_name",
            "pipeline_url",
            "pipeline_version",
            "pipeline_command",
            "methods",
            "result",
            "result_metrics",
            "report",
            "outputs",
            "upstream_analyses",
            "downstream_analyses",
            "identifiers",
            "synthscape_records",
            "mscape_records",
            "is_published",
        ]

        invalid_attributes = list(analysis_dict.keys() - set(valid_attributes))

        if invalid_attributes != []:
            logging.error("Invalid attribute in onyx analysis: %s", invalid_attributes)
            attribute_fail = True

        return attribute_fail

    # Read in analysis information from json
    def read_analysis_from_json(self, analysis_json: Path) -> None:
        "Reads analysis object from json and sets class attributes"
        with Path(analysis_json).open("r") as file:
            data = json.load(file)

        self._set_analysis_attributes(data)

    # Read in existing analysis from onyx
    def read_analysis_from_onyx(self, analysis_id: str, server: str) -> tuple[dict, int]:
        """Method to retrieve an analysis from Onyx and set class attributes from this.

        Arguments:
        analysis_id -- Name of analysis to be returned
        server -- Name of server to retrieve analysis from

        """
        analysis_dict, exitcode = self._get_analysis_from_onyx(analysis_id, server)
        if exitcode != 0:
            return analysis_dict, exitcode
        self._set_analysis_attributes(analysis_dict)

        return analysis_dict, exitcode

    @staticmethod
    @call_to_onyx
    def _get_analysis_from_onyx(analysis_id: str, server: str) -> tuple[dict, int]:
        "Retrieves analysis from Onyx"
        with OnyxClient(CONFIG) as client:
            analysis_dict = client.get_analysis(server, analysis_id)
        exitcode = 0

        return analysis_dict, exitcode

    def _set_analysis_attributes(self, analysis_dict: dict) -> None:
        "Sets class attributes from input dictionary"
        for key, value in analysis_dict.items():
            if key == "result_metrics" or key == "methods":
                value = json.loads(value)  # these need loading into dict type.
            setattr(self, key, value)

    @call_to_onyx
    def update_onyx_analysis(
        self, server: str, analysis_id: str, dryrun: bool, publish_analysis: bool
    ) -> tuple[str, int]:
        """Attempts to update an existing onyx analysis with fields in an
        OnyxAnalysis object.
        Arguments:
            server -- Server submitting data to
            analysis_id -- ID of analysis to be updated
            dryrun -- Specify if test or real upload to onyx
            publish -- Specify if analysis should be published. Set to true if all
            fields complete, false if additional fields e.g. outputs needs adding
            before publication of analysis
        Returns:
            result -- Analysis ID if valid submission, {} if test upload,
                      None if upload fails
            exitcode -- 0 if successful, 1 if fail
        """
        self.is_published = publish_analysis

        with OnyxClient(CONFIG) as client:
            result = client.update_analysis(
                project=server, analysis_id=analysis_id, fields=vars(self), test=dryrun
            )

        exitcode = 0

        return result, exitcode
