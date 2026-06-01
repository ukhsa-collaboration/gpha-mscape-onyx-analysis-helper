"""
Unit tests for the OnyxAnalysis class and associated functions. To save
generated test results in the repo, run the following command from the
top folder:
pytest tests/test_onyx_analysis_helper.py -rP --basetemp tests/test_outputs/

WARNING: Using --basetemp on an existing folder will overwrite all files.
"""

import datetime
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import regex as re

from onyx_analysis_helper import onyx_analysis_helper_functions as oa

REPO_PATH = Path(__file__).parents[1]


# Fixtures
@pytest.fixture
def example_methods():
    methods_dict = {"method1": "method example 1", "method2": "method example 2"}

    return methods_dict


@pytest.fixture
def expected_methods_json():
    methods_json = (
        '{"method1": "method example 1", "method2": "method example 2", '
        '"versions": ['
        '{"name": "a_great_tool", "version": "1.0.0"}, '
        '{"name": "another_great_tool", "version": "2000.0.0"}'
        "]}"
    )

    return methods_json


@pytest.fixture
def example_results():
    methods_dict = {"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}

    return methods_dict


@pytest.fixture
def expected_results():
    methods_dict = {"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}

    return methods_dict


@pytest.fixture
def onyx_json_file_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("onyx_analysis_tests") / "onyx_analysis.json"
    return str(tmp_dir)


@pytest.fixture
def complete_field_dict():
    field_dict = {
        "name": "test-analysis",
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "report": "",
        "outputs": "path/to/outputs",
        "methods": {
            "versions": [
                {"name": "a_great_tool", "version": "1.0.0"},
                {"name": "another_great_tool", "version": "2000.0.0"},
            ],
            "thresholds": {"limit": 10},
            "method2": "method example 2",
        },
        "result_metrics": {
            "Example result 1": 9,
            "Example result 2": "Fail",
            "Example result 3": 0.3,
        },
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


# Same as fixture 'complete_field_dict' BUT the result_metrics and methods are json strings also.
@pytest.fixture
def complete_field_dict_json():
    json_dict = {
        "name": "test-analysis",
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "report": "",
        "outputs": "path/to/outputs",
        "methods": '{"versions": [{"name": "a_great_tool", "version": "1.0.0"}, {"name": "another_great_tool", "version": "2000.0.0"}], "thresholds": {"limit": 10}, "method2": "method example 2"}',
        "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }
    return json_dict


@pytest.fixture
def no_error_log():
    log = ""
    return log


@pytest.fixture
def missing_field_dict():
    field_dict = {
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "report": "",
        "outputs": "path/to/outputs",
        "methods": {
            "versions": [
                {"name": "a_great_tool", "version": "1.0.0"},
                {"name": "another_great_tool", "version": "2000.0.0"},
            ],
            "thresholds": {"limit": 10},
            "method2": "method example 2",
        },
        "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


@pytest.fixture
def missing_field_log():
    logs = ["Missing required fields: ['name']"]
    return logs


@pytest.fixture
def missing_output_dict():
    field_dict = {
        "name": "test-analysis",
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "methods": {
            "versions": [
                {"name": "a_great_tool", "version": "1.0.0"},
                {"name": "another_great_tool", "version": "2000.0.0"},
            ],
            "thresholds": {"limit": 10},
            "method2": "method example 2",
        },
        "result_metrics": {
            "Example result 1": 9,
            "Example result 2": "Fail",
            "Example result 3": 0.3,
        },
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


@pytest.fixture
def missing_output_log():
    logs = ["Fields dict must contain one of: ['report', 'outputs']"]
    return logs


@pytest.fixture
def missing_both_dict():
    field_dict = {
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "methods": {
            "versions": [
                {"name": "a_great_tool", "version": "1.0.0"},
                {"name": "another_great_tool", "version": "2000.0.0"},
            ],
            "thresholds": {"limit": 10},
            "method2": "method example 2",
        },
        "result_metrics": {
            "Example result 1": 9,
            "Example result 2": "Fail",
            "Example result 3": 0.3,
        },
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


@pytest.fixture
def missing_both_log():
    logs = [
        "Missing required fields: ['name']",
        "Fields dict must contain one of: ['report', 'outputs']",
    ]
    return logs


@pytest.fixture
def example_onyx_json_file():
    file = Path(REPO_PATH / "tests/test_data/example_onyx_analysis.json")
    return file


@pytest.fixture
def example_onyx_json_file_fail():
    file = Path(REPO_PATH / "tests/test_data/example_onyx_analysis_fail.json")
    return file


@pytest.fixture
def invalid_field_dict():
    field_dict = {
        "invalid_name": "test-analysis",
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "report": "",
        "outputs": "path/to/outputs",
        "methods": {
            "versions": [
                {"name": "a_great_tool", "version": "1.0.0"},
                {"name": "another_great_tool", "version": "2000.0.0"},
            ],
            "thresholds": {"limit": 10},
            "method2": "method example 2",
        },
        "result_metrics": {
            "Example result 1": 9,
            "Example result 2": "Fail",
            "Example result 3": 0.3,
        },
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


@pytest.fixture
def example_result_dir():
    result_dir = Path(REPO_PATH / "tests/test_data/")
    return result_dir


@pytest.fixture
def example_result_file():
    result_dir = Path(REPO_PATH / "tests/test_data/ID-123456789_qc_results.json")

    return result_dir


##################
# Function Tests #

MOCK_ONYX_RECORD_OLD: dict[str, str | dict] = {
    "climb-id": "ID-123456",
    "site": "test",
    "published_date": "2026-01-01",
    "data": {"datapoint1": 1, "datapoint2": 2, "datapoint3": 3},
    "classifier_version": "1.0.0",
    "classifier_db_date": "1970-01-01",
    "ncbi_taxonomy_date": "1970-01-01",
    "scylla_version": "1.0.0",
    "sylph_db_version": "1.0.0",
    "alignment_db_version": "1.0.0",
}

MOCK_ONYX_RECORD_NEW: dict[str, str | dict | list[dict[str, str]]] = {
    "climb-id": "ID-123456",
    "site": "test",
    "published_date": "2026-01-01",
    "data": {"datapoint1": 1, "datapoint2": 2, "datapoint3": 3},
    "versions": [
        {"name": "classifier_version", "version": "1.0.0"},
        {"name": "classifier_db_date", "version": "1970-01-01"},
        {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
        {"name": "scylla_version", "version": "1.0.0"},
        {"name": "sylph_db_version", "version": "1.0.0"},
        {"name": "alignment_db_version", "version": "1.0.0"},
        {"name": "new_tool_coming_soon", "version": "0.0.1"},
    ],
}

EXPECTED_VERSIONS_DICTS: list[dict[str, str]] = [
    {"name": "classifier_version", "version": "1.0.0"},
    {"name": "classifier_db_date", "version": "1970-01-01"},
    {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
    {"name": "scylla_version", "version": "1.0.0"},
    {"name": "sylph_db_version", "version": "1.0.0"},
    {"name": "alignment_db_version", "version": "1.0.0"},
]


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test_get_data_and_versions_from_onyx(mocked_onyx_get, caplog):
    """
    Test getting the versions from onyx with the old style - where the versions are across seperate
    fields. These get combined and reformatted in to the list of dicts.
    The onyx query (client.get) is mocked.
    """
    # mock the onyx query return (the record) - must mock the OnyxClient (or whatever is being
    # patched) where it is being imported, not where it is defined
    mocked_onyx_get.return_value = MOCK_ONYX_RECORD_OLD

    record, actual_versions_dicts, exitcode = oa.get_data_and_versions_from_onyx(
        sample_id="ID-123456", server=""
    )

    assert "site" in record and "data" in record
    assert actual_versions_dicts == EXPECTED_VERSIONS_DICTS
    assert exitcode == 0
    print(caplog.text)
    print(f"Got these versions from Onyx record (mock): {actual_versions_dicts}")


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test__get_data_and_versions_from_onyx(mocked_onyx_get, caplog):
    """
    Test getting the versions from onyx with the new style - where all versions are in one
    field called 'versions', already as a list of dicts like:
       'versions' = [{'name': 'tool', 'version':'1.0.0'}]
    The onyx query (client.get) is mocked.
    """
    # mock the onyx query return (the record) - must mock the OnyxClient (or whatever is being
    # patched) where it is being imported, not where it is defined
    mocked_onyx_get.return_value = MOCK_ONYX_RECORD_NEW

    expected_versions_dicts = EXPECTED_VERSIONS_DICTS + [
        {"name": "new_tool_coming_soon", "version": "0.0.1"}
    ]

    record, actual_versions_dicts, exitcode = oa.get_data_and_versions_from_onyx(
        sample_id="ID-123456", server=""
    )

    assert "site" in record and "data" in record
    assert actual_versions_dicts == expected_versions_dicts
    assert exitcode == 0
    print(caplog.text)
    print(f"Got these versions from Onyx record (mock): {actual_versions_dicts}")


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test_get_data_and_versions_from_onyx_and_fields(mocked_onyx_get, caplog):
    """
    Test getting the versions from onyx with the old style but only return specific fields in
    the record.
    The onyx query (client.get) is mocked.
    """
    # mock the onyx query return (the record) - must mock the OnyxClient (or whatever is being
    # patched) where it is being imported, not where it is defined
    mocked_onyx_get.return_value = MOCK_ONYX_RECORD_OLD

    fields = ["published_date", "data"]
    record, actual_versions_dicts, exitcode = oa.get_data_and_versions_from_onyx(
        sample_id="ID-123456", server="", fields=fields
    )

    assert "site" not in record and "data" in record
    assert actual_versions_dicts == EXPECTED_VERSIONS_DICTS
    assert exitcode == 0
    print(caplog.text)
    print(f"Got these versions from Onyx record (mock): {actual_versions_dicts}")


def test_onyx_query_fails(caplog):
    record, exitcode = oa.query_onyx("ID_123456", "SERVER")
    assert record is None
    assert exitcode == 1
    assert "OnyxConnectionError" in caplog.text
    print(f"\nLog text: \n{caplog.text}")


def test_get_data_and_versions_from_onyx_fails_to_query(caplog):
    record, actual_versions_dicts, exitcode = oa.get_data_and_versions_from_onyx(
        sample_id="ID-123456", server="SERVER"
    )

    assert record == {}
    assert exitcode == 1
    assert actual_versions_dicts == []
    assert "OnyxConnectionError" in caplog.text
    assert "Error: Onyx query failed for sample ID ID-123456 and server SERVER." in caplog.text
    print(f"\nLog text: \n{caplog.text}")


#####################################
# Onyx analysis Helper class Tests: #


def test_add_analysis_details():
    expected_name = "example_analysis"
    expected_description = "This is an example analysis."
    analysis = oa.OnyxAnalysis()
    analysis.add_analysis_details(expected_name, expected_description)

    assert analysis.name == expected_name
    assert analysis.description == expected_description


def test_add_analysis_date_no_date():
    analysis = oa.OnyxAnalysis()
    analysis._set_analysis_date()
    print(analysis.analysis_date)

    assert analysis.analysis_date == datetime.datetime.now().date().isoformat()


def test_add_analysis_date_already_date():
    correct_date = datetime.datetime(2025, 8, 21)
    analysis = oa.OnyxAnalysis()
    analysis.analysis_date = correct_date
    analysis._set_analysis_date()

    assert analysis.analysis_date == correct_date


def test__get_fields():
    analysis = oa.OnyxAnalysis()
    analysis.methods = {
        "versions": [
            {"name": "a_great_tool", "version": "1.0.0"},
            {"name": "another_great_tool", "version": "2000.0.0"},
        ],
        "thresholds": {"limit": 10},
        "method2": "method example 2",
    }
    analysis.result_metrics = {
        "Example result 1": 9,
        "Example result 2": "Fail",
        "Example result 3": 0.3,
    }
    # Before function:
    assert isinstance(analysis.methods, dict)
    assert isinstance(analysis.result_metrics, dict)

    fields = analysis._get_fields()
    # after function
    assert isinstance(fields["methods"], str)
    assert isinstance(fields["result_metrics"], str)


def test__get_fields_empty():
    analysis = oa.OnyxAnalysis()
    fields = analysis._get_fields()
    assert len(fields) == 1


def test__get_fields_other_field_is_dict():
    analysis = oa.OnyxAnalysis()
    analysis.add_analysis_details(
        analysis_name="name",
        analysis_description={"name": "analysis", "type": "details"},  # ty:ignore[invalid-argument-type]
    )
    print(analysis.__dict__)
    assert isinstance(analysis.description, dict)
    fields = analysis._get_fields()
    print(fields)
    assert isinstance(fields["description"], str)


def test_add_package_metadata():
    analysis = oa.OnyxAnalysis()
    analysis.add_package_metadata("climb-onyx-client")
    version_check = re.fullmatch("[0-9]+\\.[0-9]+\\.[0-9]+", analysis.pipeline_version)

    assert analysis.pipeline_name == "climb-onyx-client"
    assert version_check is not None
    assert analysis.pipeline_url == "https://github.com/CLIMB-TRE/onyx-client"


def test_add_results(example_results, expected_results):
    result = "headline result"
    analysis = oa.OnyxAnalysis()
    analysis.add_results(result, example_results)

    assert analysis.result == result
    assert analysis.result_metrics == expected_results


def test_add_server_records():
    sample_id = "ID-123456789"
    server = "synthscape"
    analysis = oa.OnyxAnalysis()
    analysis.add_server_records(sample_id, server)
    assert analysis.synthscape_records == ["ID-123456789"]  # ty:ignore[unresolved-attribute]


def test_write_analysis_to_json(onyx_json_file_path, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    for key, value in complete_field_dict.items():
        setattr(analysis, key, value)
    analysis.write_analysis_to_json(onyx_json_file_path)
    print(f"Analysis json written to {onyx_json_file_path}")

    assert Path(onyx_json_file_path).exists()


@pytest.mark.parametrize(
    "field_dict,expected_log_message,expected_output",
    [
        ("complete_field_dict", "no_error_log", False),
        ("missing_field_dict", "missing_field_log", True),
    ],
)
def test_check_required_fields(field_dict, expected_log_message, expected_output, request, caplog):
    field_dict = request.getfixturevalue(field_dict)
    expected_log_message = request.getfixturevalue(expected_log_message)

    analysis = oa.OnyxAnalysis()
    # populate the analysis table class with the attributes from the fixture:
    for key, value in field_dict.items():
        setattr(analysis, key, value)

    field_fail = analysis._check_required_fields()

    assert all(messages in caplog.text for messages in expected_log_message)
    assert field_fail == expected_output


@pytest.mark.parametrize(
    "field_dict,expected_log_message,expected_output",
    [
        ("complete_field_dict", "no_error_log", False),
        ("missing_output_dict", "missing_output_log", True),
    ],
)
def test_check_required_outputs(field_dict, expected_log_message, expected_output, request, caplog):
    field_dict = request.getfixturevalue(field_dict)
    expected_log_message = request.getfixturevalue(expected_log_message)

    assert isinstance(field_dict["methods"], dict)

    analysis = oa.OnyxAnalysis()
    # populate the analysis table class with the attributes from the fixture:
    for key, value in field_dict.items():
        setattr(analysis, key, value)

    output_fail = analysis._check_required_outputs()

    assert all(messages in caplog.text for messages in expected_log_message)
    assert output_fail == expected_output
    assert isinstance(field_dict["methods"], dict)


def test_read_analysis_from_json_pass(example_onyx_json_file, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis.read_analysis_from_json(example_onyx_json_file)
    assert analysis.__dict__ == complete_field_dict


def test_set_analysis_attributes(complete_field_dict_json, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis._set_analysis_attributes(complete_field_dict_json)

    assert analysis.__dict__ == complete_field_dict


def test_check_analysis_attributes_pass(complete_field_dict):
    analysis = oa.OnyxAnalysis()
    # populate the analysis table class with the attributes from the fixture:
    for key, value in complete_field_dict.items():
        setattr(analysis, key, value)
    attr_fail = analysis._check_analysis_attributes()

    assert not attr_fail


def test_check_analysis_attributes_fail(invalid_field_dict, caplog):
    analysis = oa.OnyxAnalysis()
    for field, value in invalid_field_dict.items():
        setattr(analysis, field, value)
    # methods should be dict before and after
    assert isinstance(analysis.methods, dict)
    attr_fail = analysis._check_analysis_attributes()
    assert isinstance(analysis.methods, dict)
    message = "Invalid attribute in onyx analysis: ['invalid_name']"

    assert message in caplog.text
    assert attr_fail


@pytest.mark.parametrize(
    "test_input,publish_boolean,expected_output",
    [
        pytest.param(
            "missing_output_dict",
            False,
            [False, False],
            id="Correct input for prepublish analysis object - no errors",
        ),
        pytest.param(
            "missing_both_dict",
            False,
            [True, False],
            id="Incorrect input for prepublish analysis object - missing field fail",
        ),
        pytest.param(
            "complete_field_dict",
            True,
            [False, False, False],
            id="Correct input for publish analysis object - no errors",
        ),
        pytest.param(
            "invalid_field_dict",
            True,
            [True, True, False],
            id="Incorrect input for publish analysis object - missing field and invalid fields fails",
        ),
    ],
)
def test_check_analysis_object(test_input, publish_boolean, expected_output, request):
    fields_dict = request.getfixturevalue(test_input)

    analysis = oa.OnyxAnalysis()
    for field, value in fields_dict.items():
        setattr(analysis, field, value)

    # methods and results_metrics should be dicts before and after:
    assert isinstance(analysis.methods, dict)
    assert isinstance(analysis.result_metrics, dict)
    status_list = analysis.check_analysis_object(publish_analysis=publish_boolean)
    # print("\n", status_list)

    assert status_list == expected_output
    assert isinstance(analysis.methods, dict)
    assert isinstance(analysis.result_metrics, dict)


def test_add_output_location_dir(example_result_dir):
    analysis = oa.OnyxAnalysis()
    output_fail = analysis.add_output_location(example_result_dir)

    assert not output_fail
    assert analysis.outputs


def test_add_output_location_file(example_result_file):
    analysis = oa.OnyxAnalysis()
    output_fail = analysis.add_output_location(example_result_file)

    assert not output_fail
    assert analysis.report


def test_add_output_location_invalid():
    analysis = oa.OnyxAnalysis()
    output_fail = analysis.add_output_location(Path("not a file path"))

    assert output_fail


def test_add_versions_to_methods_null_args(caplog):
    """Test that not providing any args does not fail but gives warning."""
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods()
    assert not methods_fail
    assert "Warning: No suitable arguments provided" in caplog.text


ONYX_VERSIONS: list[dict[str, str]] = [
    {"name": "classifier_version", "version": "1.0.0"},
    {"name": "classifier_db_date", "version": "1970-01-01"},
    {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
    {"name": "scylla_version", "version": "1.0.0"},
    {"name": "sylph_db_version", "version": "1.0.0"},
    {"name": "alignment_db_version", "version": "1.0.0"},
]


def test_add_versions_to_methods_just_onyx(caplog):
    """
    Test that add_methods functions gets the versions from the query when set to true and populates
    the attribute.
    """

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(onyx_versions=ONYX_VERSIONS)
    print(caplog.text)
    assert analysis.methods["versions"]
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


def test_add_versions_to_methods_plus_tools(caplog):
    """
    Test that add_methods functions gets the versions from the query (plus onyx versions hash)
    and adds user defined tool versions and then populates the methods attribute correctly.
    """

    expected_results = {
        "versions": [
            {"name": "classifier_version", "version": "1.0.0"},
            {"name": "classifier_db_date", "version": "1970-01-01"},
            {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
            {"name": "scylla_version", "version": "1.0.0"},
            {"name": "sylph_db_version", "version": "1.0.0"},
            {"name": "alignment_db_version", "version": "1.0.0"},
            {"name": "my_pkg", "version": "v1.2.3"},
        ],
        "onyx_versions_hash": "e0c8c12a02fa86494059858c41af311d94c086a286bf4c62d53c21261e90f614",
    }

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        tool_versions={"my_pkg": "v1.2.3"},
        onyx_versions=ONYX_VERSIONS,
    )
    print(caplog.text)
    assert analysis.methods == expected_results, "The analysis methods do not look as expected."
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


def test_add_versions_do_not_overwrite(caplog):
    """
    Test that adding versions doesn't overwrite. Includes onyx versions and hash.
    """
    expected_methods = {
        "versions": [
            {"name": "classifier_version", "version": "1.0.0"},
            {"name": "my_pkg", "version": "v1.2.3"},
            {"name": "my_other_pkg", "version": "v2.3.4"},
        ],
        "onyx_versions_hash": "b997b78b7ef8c0e21d8d6c0fe242bb9f5e0b98ff6e13240ef4e341d787605481",
    }
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        onyx_versions=[{"name": "classifier_version", "version": "1.0.0"}],
    )
    assert not methods_fail

    methods_fail_2 = analysis.add_versions_to_methods(
        tool_versions={"my_pkg": "v1.2.3"},
    )
    assert not methods_fail_2
    methods_fail_3 = analysis.add_versions_to_methods(
        tool_versions={"my_other_pkg": "v2.3.4"},
    )
    assert not methods_fail_3
    assert analysis.methods == expected_methods, (
        f"Actual methods attribute does not look as expected: {expected_methods}"
    )
    print(f"Expected methods to correct look like: {analysis.methods}")


def test_add_versions_to_methods_onyx_versions_not_list(caplog):
    """
    Test that methods_fail if the onyx versions not a list.
    """
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        onyx_versions={"tool": "version"},  # ty:ignore[invalid-argument-type]
    )
    print(f"\nLog should record error: \n{caplog.text}")
    assert methods_fail
    assert "Error: Onyx versions must be given as list in format" in caplog.text


def test_add_versions_to_methods_just_versions(caplog):
    """
    Test that versions are added without onyx query.
    """
    expected_results = {
        "versions": [
            {"name": "my_pkg", "version": "v1.2.3"},
        ]
    }

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        tool_versions={"my_pkg": "v1.2.3"},
    )
    print(caplog.text)
    assert analysis.methods == expected_results, "The analysis methods do not look as expected."
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


def test_add_versions_not_hash_by_default():
    """Test versions_hash is not added unless include_versions_hash is True."""
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        tool_versions={"cool_tool": "v1.2.3"},
    )

    assert not methods_fail
    assert "versions_hash" not in analysis.methods


def test_add_versions_can_add_versions_hash():
    """Test include_versions_hash adds a versions_hash after adding versions."""
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        tool_versions={"cool_tool": "v1.2.3"},
        include_versions_hash=True,
    )

    assert not methods_fail
    assert analysis.methods["versions_hash"] == oa._calculate_versions_hash(
        analysis.methods["versions"]
    )


def test_add_versions_can_overwrite_versions_hash():
    """Test include_versions_hash overwrites an existing versions_hash."""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {"versions_hash": "i_am_a_existing_hash_!"}

    methods_fail = analysis.add_versions_to_methods(
        tool_versions={"cool_tool": "v1.2.3"},
        include_versions_hash=True,
    )

    assert not methods_fail
    assert analysis.methods["versions_hash"] != "i_am_a_existing_hash_!"
    assert analysis.methods["versions_hash"] == oa._calculate_versions_hash(
        analysis.methods["versions"]
    )


def test_calculate_hash_not_affected_by_version_order():
    """Test that same entries in different orders produce the same hash."""
    versions = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
        {"name": "important_database", "version": "2026-04-24"},
    ]
    reordered_versions = [
        {"name": "important_database", "version": "2026-04-24"},
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
    ]

    assert oa._calculate_versions_hash(versions) == oa._calculate_versions_hash(reordered_versions)


def test_calculate_hash_is_not_affected_by_dict_key_order():
    """Test that same entries with different dict key orders produce the same hash."""
    versions = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
        {"name": "important_database", "version": "2026-04-24"},
    ]
    reordered_keys_versions = [
        {"version": "v1.2.3", "name": "this_tool_doesnt_exist"},
        {"version": "1.0.0", "name": "neither_does_this_one"},
        {"name": "important_database", "version": "2026-04-24"},
    ]

    assert oa._calculate_versions_hash(versions) == oa._calculate_versions_hash(
        reordered_keys_versions
    )


def test_calculate_hash_changes_when_new_version_is_added():
    """Test adding a version entry changes the hash."""
    versions = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
    ]
    versions_with_new_tool = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
        {"name": "important_database", "version": "2026-04-24"},
    ]

    assert oa._calculate_versions_hash(versions) != oa._calculate_versions_hash(
        versions_with_new_tool
    )


@pytest.mark.parametrize(
    "changed_version",
    [
        pytest.param("oh_look_i_use_strings_as_versions_now", id="string"),
        pytest.param("v1.0.1", id="patch_with_v"),
        pytest.param("2.0.0", id="major"),
        pytest.param("1.1.0", id="minor"),
        pytest.param("1.0.1", id="patch"),
    ],
)
def test_calculate_hash_changes_when_version_changes(changed_version):
    """Test that changing version changes the hash."""
    versions = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
    ]
    versions_with_changed_version = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": changed_version},
    ]

    assert oa._calculate_versions_hash(versions) != oa._calculate_versions_hash(
        versions_with_changed_version
    )


def test_extra_field_in_version_dict_changes_hash():
    """Test that adding an extra field to the version dict changes the hash."""
    versions = [
        {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
        {"name": "neither_does_this_one", "version": "1.0.0"},
    ]
    versions_with_extra_field = [
        {
            "name": "this_tool_doesnt_exist",
            "version": "v1.2.3",
            "i_am_extra": "with_an_extra_value",
        },
        {"name": "neither_does_this_one", "version": "1.0.0"},
    ]

    assert oa._calculate_versions_hash(versions) != oa._calculate_versions_hash(
        versions_with_extra_field
    )


def test_add_versions_hash_to_methods():
    """Test adding a versions hash to the methods dict."""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {
        "versions": [
            {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
            {"name": "neither_does_this_one", "version": "1.0.0"},
        ]
    }

    methods_fail = analysis.add_versions_hash_to_methods()

    assert not methods_fail
    assert analysis.methods["versions_hash"] == oa._calculate_versions_hash(
        analysis.methods["versions"]
    )


def test_add_versions_hash_to_methods_replaces():
    """Test versions hash is overwritten when versions change."""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {
        "versions": [
            {"name": "this_tool_doesnt_exist", "version": "v1.2.3"},
            {"name": "neither_does_this_one", "version": "1.0.0"},
        ]
    }

    first_methods_fail = analysis.add_versions_hash_to_methods()
    first_hash = analysis.methods["versions_hash"]

    analysis.methods["versions"].append({"name": "important_database", "version": "2026-04-24"})
    second_methods_fail = analysis.add_versions_hash_to_methods()

    assert not first_methods_fail
    assert not second_methods_fail
    assert analysis.methods["versions_hash"] != first_hash


def test_add_versions_hash_to_methods_missing_versions_fails(caplog):
    """Test missing versions list fails"""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {"thresholds": {"limit": 10}}

    methods_fail = analysis.add_versions_hash_to_methods()

    assert methods_fail
    assert (
        "Error: versions must be present in methods before calculating versions_hash" in caplog.text
    )
    assert "versions_hash" not in analysis.methods


def test_add_versions_hash_to_methods_wrong_type_fails(caplog):
    """Test non-list versions fail"""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {"versions": {"name": "this_tool_doesnt_exist", "version": "v1.2.3"}}

    methods_fail = analysis.add_versions_hash_to_methods()

    assert methods_fail
    assert "Error: versions must be a list before calculating versions_hash" in caplog.text
    assert "versions_hash" not in analysis.methods


def test_add_methods(caplog):
    expected_methods = {
        "thresholds": {"limit": 10},
        "command": "must_record_this_command.sh",
    }

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_methods(
        {
            "thresholds": {"limit": 10},
            "command": "must_record_this_command.sh",
        }
    )
    print(caplog.text)
    assert analysis.methods == expected_methods
    assert not methods_fail
    print(f"analysis table methods fields correctly looks like: {analysis.methods}")


@pytest.mark.parametrize(
    "input,msg",
    [
        ({"version": ["1.0.0", "2.0.0"]}, "Error: Cannot add 'version'"),
        ({"versions": {"name": "tool", "version": "1.0.0"}}, "Error: Cannot add 'versions'"),
        ("1.2.3", "Error: Methods must be in dict format"),
    ],
)
def test_add_methods_try_adding_versions(input, msg, caplog):
    """Test that adding any kind of version or versions will log an error."""
    analysis = oa.OnyxAnalysis()
    # add_versions_to_methods has been run and "versions" already exists.

    methods_fail = analysis.add_methods(input)

    assert methods_fail
    assert msg in caplog.text
    print(f"\nExpected error in log:\n{caplog.text}")


def test_add_methods_broken_methods_dict_input(caplog):
    """Test error logged if methods_dict input type incorrect."""
    analysis = oa.OnyxAnalysis()
    analysis.methods = {}
    methods_fail = analysis.add_methods(
        "command"  # ty:ignore[invalid-argument-type]
    )
    print(f"\nLog should record error: \n{caplog.text}")
    assert "Error: Methods must be in dict format." in caplog.text
    assert methods_fail
    print("Error correctly caught when input type not dict.")


@pytest.mark.parametrize(
    "vers,truncate,expect",
    [
        ("1.2.3", "MAJOR", "1"),
        ("1.2.3", "MINOR", "1.2"),
        ("1.2.3", "PATCH", "1.2.3"),
        ("1.2.3-rc.4", "MINOR", "1.2"),
        ("1.2.3-rc.4", "PATCH", "1.2.3"),
        ("not a version", "MAJOR", "not a version"),
    ],
)
def test_truncate_version(vers, truncate, expect):
    actual = oa.truncate_version(vers, truncate)
    assert actual == expect


MOCK_ANALYSIS_RECORD = [
    {
        "published_date": "1970-01-01",
        "site": "test",
        "analysis_id": "AID-12345678",
        "analysis_date": "1970-01-01",
        "name": "test-analysis",
        "report": "",
        "outputs": "path/to/outputs/file.json",
    }
]

MOCK_ANALYSIS_TABLE = {
    "name": "test-analysis",
    "description": "This is a test analysis",
    "analysis_date": "1970-01-01",
    "pipeline_name": "test-pipeline",
    "pipeline_url": "test-pipeline-url",
    "pipeline_version": "0.1.0",
    "result": "test result",
    "upstream_analyses": [],
    "report": "",
    "outputs": "path/to/outputs/file.json",
    "methods": {
        "versions": [
            {"name": "a_great_tool", "version": "1.0.0"},
            {"name": "another_great_tool", "version": "2000.0.0"},
        ],
        "thresholds": {"limit": 10},
        "method2": "method example 2",
    },
    "result_metrics": {
        "Example result 1": 9,
        "Example result 2": "Fail",
        "Example result 3": 0.3,
    },
    "synthscape_records": ["ID-123456789"],
    "identifiers": [],
    "analysis_id": "AID-12345678",
}

ANOTHER_MOCK_ANALYSIS_RECORD = [
    {
        "published_date": "1970-01-02",
        "site": "test-the-second",
        "analysis_id": "AID-89012345",
        "analysis_date": "1970-01-02",
        "name": "test-analysis",
        "report": "",
        "outputs": "path/to/file_2.json",
    }
]

ANOTHER_MOCK_ANALYSIS_TABLE = {
    "name": "test-analysis",
    "description": "This is another test analysis",
    "analysis_date": "1970-01-02",
    "pipeline_name": "test-pipeline",
    "pipeline_url": "test-pipeline-url",
    "pipeline_version": "0.1.0",
    "result": "another test result",
    "upstream_analyses": [],
    "report": "",
    "outputs": "path/to/file_2.json",
    "methods": {
        "versions": [
            {"name": "a_great_tool", "version": "1.0.0"},
            {"name": "another_great_tool", "version": "2000.0.0"},
        ],
        "thresholds": {"limit": 10},
        "method2": "method example 2",
    },
    "result_metrics": {
        "Example result 1": 9,
        "Example result 2": "Fail",
        "Example result 3": 0.3,
    },
    "synthscape_records": ["ID-123456789"],
    "identifiers": [],
    "analysis_id": "AID-89012345",
}


@patch(
    target="onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get_analysis",
    return_value=MOCK_ANALYSIS_TABLE.copy(),
)
@patch(
    target="onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.analyses",
    return_value=MOCK_ANALYSIS_RECORD.copy(),
)
def test_get_analysis_records(mocked_analyses, mocked_analysis_table):
    analyses_records, exitcode = oa.get_analysis_records(sample_id="ID-123456", server="")
    assert len(analyses_records) == 1
    assert exitcode == 0


@patch(
    "onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.analyses",
)
def test_get_analysis_records_multiple_analyses(mocked_analyses):
    """
    Get analyses tables from sample with multiple analyses tables. Mock the get_analysis records and
    the analysis table records.

    Note that this function sometimes fails but running alone seems to pass?
    """
    mocked_analyses.return_value = MOCK_ANALYSIS_RECORD + ANOTHER_MOCK_ANALYSIS_RECORD

    with patch(
        "onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get_analysis",
        side_effect=[MOCK_ANALYSIS_TABLE.copy(), ANOTHER_MOCK_ANALYSIS_TABLE.copy()],
    ):
        many_analyses_records, exitcode = oa.get_analysis_records(sample_id="ID-123456", server="")
        print(many_analyses_records)
        assert len(many_analyses_records) == 2
        assert exitcode == 0


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.analyses")
def test_get_analysis_records_no_analyses(mocked_analyses, caplog):
    caplog.set_level(logging.INFO)

    mocked_analyses.return_value = []

    analyses_records, exitcode = oa.get_analysis_records(sample_id="ID-123456", server="")
    assert "No analysis tables found for sample ID-123456" in caplog.text
    assert analyses_records == {}
    assert exitcode == 0
