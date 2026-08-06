"""
Module containing OnyxAnalysis class object and associated functions
to support submission and reading of onyx analyses.
"""

import datetime
import hashlib
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
def _calculate_versions_hash(versions: list[dict[str, str | None]]) -> str:
    """
    Create a stable SHA-256 hash from version records.

    Version record order and dict key order do not affect the hash.
    A new entry in the versions list will change the hash, as will a new field in the version dicts, or a change in any of the values.
    """
    stable_versions = sorted(
        versions,
        key=lambda version: json.dumps(version, sort_keys=True, separators=(",", ":")),
    )
    versions_json = json.dumps(stable_versions, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(versions_json.encode()).hexdigest()


@call_to_onyx
def query_onyx(
    sample_id: str,
    server: str,
) -> tuple[dict, int]:
    """
    Query to onyx using OnyxClient.get for single sample and specified server.

    Returns record first as dict and exitcode as int. Uses decorator so can only return record
    and exitcode.

    Arguments:
            sample_id -- valid climb id.
            server -- name of server to query.

        Returns:
            record -- dict, the entire Onyx record, or just the fields requested in 'fields'
                argument.
            versions_dicts -- list of dicts, where the dict contains "name" and "version".
                e.g. [{"name": "tool", "version": "1.2.3"}, {"name": "db", "version": "2.3.4"}]
            exitcode -- 1 if fail 0 if pass

    """
    exitcode = 0

    with OnyxClient(CONFIG) as client:
        record: dict = client.get(project=server, climb_id=sample_id)

    return record, exitcode


def get_data_and_versions_from_onyx(
    sample_id: str, server: str, fields: list | None = None
) -> tuple[dict, list[dict], int]:
    """
    Query to onyx for specific climb id and server, then handle versions from Onyx and return
    just fields of interest if supplied.

    Returns record first, specific versions dict and exitcode.

    Arguments:
        sample_id -- valid climb id.
        server -- name of server to query.
        fields -- optional, list of valid onyx fields to return in the record.
    Returns:
        record -- dict, the entire Onyx record, or just the fields requested in 'fields'
            argument.
        versions_dicts -- list of dicts, where the dict contains "name" and "version".
            e.g. [{"name": "tool", "version": "1.2.3"}, {"name": "db", "version": "2.3.4"}]
        exitcode -- 1 if fail 0 if pass

    """
    exitcode = 0
    record: dict
    record, exitcode = query_onyx(sample_id=sample_id, server=server)

    versions_dicts: list[dict[str, str | None]] = []

    if exitcode != 0:
        logging.error(
            "Error: Onyx query failed for sample ID %s and server %s." % (sample_id, server)  # noqa: UP031
        )
        # if onyx call did not work, return an empty record, empty versions and exitcode 1.
        return {}, [], 1

    # Add a little check that the versions column in the record is as expected:
    if (
        (new_versions_dicts := record.get("versions"))
        and isinstance(new_versions_dicts, list)
        and isinstance(new_versions_dicts[0], dict)
    ):
        versions_dicts.extend(new_versions_dicts)
    else:
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

    if fields:
        record: dict = {field: record[field] for field in fields}

    return record, versions_dicts, exitcode


# Query analysis tables
@call_to_onyx
def get_analysis_records(sample_id: str, server: str, fields: list = []) -> tuple[dict, int]:  # noqa: B006
    """
    Query onyx to get all analysis tables associated with a given sample ID on a given server.

    Arguments:
        sample_id -- valid climb id.
        server -- name of server to query.
        fields -- optional, list of valid onyx fields to return in the record.
    Returns:
        analysis_recs -- a dictionary where key is the analysis ID, and value is the record.
        exitcode -- 1 if fail 0 if pass
    """
    exitcode = 0
    if fields:
        fields.append("analysis_id")

    analysis_recs: dict = {}

    with OnyxClient(CONFIG) as client:
        analyses: dict = client.analyses(project=server, climb_id=sample_id)

        analysis_ids = [analysis["analysis_id"] for analysis in analyses]

        if not analysis_ids:
            logging.info("No analysis tables found for sample %s on server %s.", sample_id, server)
            return {}, exitcode

        for aid in analysis_ids:
            analysis_rec = client.get_analysis(project=server, analysis_id=aid, include=fields)

            analysis_recs[analysis_rec.pop("analysis_id")] = analysis_rec

    return analysis_recs, exitcode


def truncate_version(version: str, use_version: str = "PATCH"):
    """
    Truncate semver version to 'use_version'.

    Arguments
        version -- str, the version to be truncated, i.e. '1.2.3' - can be longer, will strip off
            letters.
        use_version -- str, must be one of MAJOR, MINOR or PATCH.
    Returns:
        new version -- version truncated at the point given by use_version.
    """
    semver = ["MAJOR", "MINOR", "PATCH"]
    use_version = use_version.upper()
    if use_version and use_version in semver:
        v = version.split("-")[0] if "-" in version else version
        v = v.split(".")[0 : (semver.index(use_version) + 1)]
    else:
        raise ValueError('use_version must be one of "MAJOR", "MINOR", "PATCH"')
    return ".".join(v)


class OnyxAnalysis:
    def __init__(self):
        self.analysis_date: datetime.datetime
        self.name: str
        self.description: str
        self.pipeline_name: str
        self.pipeline_url: str
        self.pipeline_version: str
        self.pipeline_command: str | None
        self.methods: dict
        self.result: str
        self.result_metrics: dict = {}
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
        package_metadata = dict(metadata.metadata(package_name))  # ty:ignore[no-matching-overload]
        self.pipeline_name = package_metadata["Name"]
        self.pipeline_version = (
            package_metadata["Version"]
            if package_metadata["Version"].startswith("v")
            else "v" + package_metadata["Version"]
        )
        self.pipeline_url = package_metadata["Project-URL"].split(", ")[
            1
        ]  # Get url from toml - add to template

    def add_versions_to_methods(
        self,
        tool_versions: dict | None = None,
        onyx_versions: list[dict] | None = None,
        include_versions_hash: bool = False,
    ) -> bool:
        """
        Method to add versions to the methods field in the analysis table.

        Give tool versions to record as a dict:
            {'tool_name': '1.0.0'}

        Give onyx__versions as a list of dicts - must be the output from
        get_data_and_versions_from_onyx or in format list of dicts:
        [{'name':'tool', 'version':'1.0.0'}]

        Arguments:
            tool_versions -- Optional; dict of other versions to put into the versions dict in the
                methods. Must be in format {'tool_name': 'version'}
            onyx_versions
            include_versions_hash -- default is False, set to True to calculate and add
                versions_hash to the methods dict after versions are added.
        Returns:
            methods_fail -- bool, False if successful, True if fail - check logs.
        """
        methods_fail = False

        # If attribute not yet set, set as empty dict.
        if not hasattr(self, "methods"):
            self.methods = {}

        # There is a chance this function does nothing, so bail early:
        if not onyx_versions and not tool_versions:
            logging.warning("Warning: No suitable arguments provided, this method does nothing.")
            return methods_fail

        versions_dicts: list = []

        # Add onyx versions if there are any. Must be list.
        if onyx_versions:
            # If not list, bail early
            if not isinstance(onyx_versions, list):
                logging.error(
                    "Error: Onyx versions must be given as list in format: "
                    "[{'name': 'tool', 'version': '1.0.0'}]. Use outputs from "
                    "get_data_and_versions_from_onyx."
                )
                methods_fail = True
                return methods_fail

            # Append those onyx versions
            versions_dicts.extend(onyx_versions)

            # Add onyx_versions_hash to the methods:
            onyx_versions_hash = _calculate_versions_hash(onyx_versions)
            self.methods["onyx_versions_hash"] = onyx_versions_hash

        # Add any additional versions that need to go into the analysis table. Must be dict.
        if tool_versions:
            # if not dict, bail early
            if not isinstance(tool_versions, dict):
                logging.error("Error: tool_versions must be in dict format: e.g. {'tool': '1.0.0'}")
                methods_fail = True
                return methods_fail
            # Reformat the versions and add to the dict.
            for tool, version in tool_versions.items():
                versions_dicts.append({"name": tool, "version": version})

        # Add versions_dicts to the analysis table but don't overwrite
        if existing_versions := self.methods.get("versions"):
            existing_versions.extend(versions_dicts)
        else:
            self.methods["versions"] = versions_dicts

        if include_versions_hash:
            methods_fail = self.add_versions_hash_to_methods()

        # methods did not fail
        return methods_fail

    def add_versions_hash_to_methods(self) -> bool:
        """
        Calculate and add versions_hash to the methods field.

        This can be called after versions have been added to methods. It always
        overwrites any existing versions_hash with a hash calculated from the
        current methods["versions"] list.

        Returns:
            methods_fail: true if fail, check logging message.
        """
        methods_fail = False

        if "versions" not in self.methods:
            logging.error(
                "Error: versions must be present in methods before calculating versions_hash"
            )
            methods_fail = True
            return methods_fail

        if not isinstance(self.methods["versions"], list):
            logging.error("Error: versions must be a list before calculating versions_hash")
            methods_fail = True
            return methods_fail

        self.methods["versions_hash"] = _calculate_versions_hash(self.methods["versions"])
        return methods_fail

    def add_methods(self, methods_dict: dict) -> bool:
        """
        Attempts to add methods to onyx analysis object. If methods are invalid, returns
        methods_fail.

        DO NOT provide 'versions' with this method, use add_versions_to_methods instead.

        Arguments:
            method_dicts: dict containing methods to add. Recommended to be nested but doesn't have
            to be.
                e.g.: {"thresholds": {"cutoff": 1, "limit": 2}} or {"command": "tool --defaults"}
                or a combination of both.

        Returns:
            methods_fail: true if fail, check logging message.
        """
        methods_fail = False

        if not isinstance(methods_dict, dict):
            logging.error("Error: Methods must be in dict format.")
            methods_fail = True
            return methods_fail

        # If attribute not yet set, set as empty dict.
        if not hasattr(self, "methods"):
            self.methods = {}

        for method_name, method_params in methods_dict.items():
            if method_name == "version" or method_name == "versions":
                logging.error(
                    (  # noqa: UP031
                        "Error: Cannot add '%s' to the methods field with add_methods. "
                        "Use add_versions_to_methods to add versions."
                    )
                    % (method_name)
                )
                methods_fail = True
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

    def _get_fields(self) -> dict:
        """
        Get all the fields in the analysis table. If methods and results_metrics set, convert dicts
        to json string.
        """
        fields_dict: dict[str, str | dict | Path | list | None] = vars(self).copy()
        for field, value in fields_dict.items():
            if isinstance(value, dict):
                fields_dict[field] = json.dumps(value)

        return fields_dict

    def _get_onyx_payload(self, publish: bool):
        """
        Return the payload that will be updated in Onyx. The payload contains a dict of the
        fields that will be updated in Onyx. If the record is to be published, set publish=True.

        NB: The 'is_published' field is a toggle for visibility in onyx.

        arguments:
            publish (bool): True if the record should be visible in Onyx, False if hidden (used
            if the record is incomplete).

        Returns:
            payload (dict): The payload is a python dict that stores values as json strings
            (Onyx will only accept json strings).
        """
        # set the is_published field to true/false as per arg
        self.is_published = publish
        # convert any python dicts to json
        payload: dict = self._get_fields()

        return payload

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
            publish_analysis -- Specify if analysis should be published. Set to true is all fields
            complete, false if additional fields e.g. outputs needs adding before publication of
            analysis
        Returns:
            result -- Analysis ID if valid submission, {} if test upload,
                      None if upload fails
            exitcode -- 0 if successful, 1 if fail
        """
        payload = self._get_onyx_payload(publish_analysis)

        with OnyxClient(CONFIG) as client:
            result = client.create_analysis(project=server, fields=payload, test=dryrun)
        exitcode = 0

        return result, exitcode

    # Write analysis object to json
    def write_analysis_to_json(self, result_file: Path) -> Path | None:
        "Writes onyx analysis object to json"
        fields_dict = self._get_fields()

        with Path(result_file).open("w") as file:
            json.dump(fields_dict, file)

        return result_file

    # Check fields and attributes are valid
    def check_analysis_object(self, publish_analysis: bool) -> list[bool | str]:
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
        fields_dict = self._get_fields()
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
        fields_dict = self._get_fields()
        missing_output = False
        output_fields = ["report", "outputs"]

        if not any(field in output_fields for field in fields_dict):
            logging.error("Fields dict must contain one of: %s", output_fields)
            missing_output = True

        return missing_output

    def _check_analysis_attributes(self) -> bool:
        "Checks all attributes are valid onyx fields, return True if invalid fields present"

        analysis_dict = self._get_fields()
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
        """Sets class attributes from input dictionary. Attributes that are dicts are parsed from
        json as dicts into the instance."""
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
            publish_analysis -- Specify if analysis should be published. Set to
            true if all fields complete, false if additional fields e.g.
            outputs needs adding before publication of analysis
        Returns:
            result -- Analysis ID if valid submission, {} if test upload,
                      None if upload fails.
            exitcode -- 0 if successful, 1 if fail
        """
        payload = self._get_onyx_payload(publish_analysis)

        with OnyxClient(CONFIG) as client:
            result = client.update_analysis(
                project=server, analysis_id=analysis_id, fields=payload, test=dryrun
            )

        exitcode = 0

        return result, exitcode
