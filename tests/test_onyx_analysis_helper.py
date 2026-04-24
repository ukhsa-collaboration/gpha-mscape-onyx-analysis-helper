"""
Unit tests for the OnyxAnalysis class and associated functions. To save
generated test results in the repo, run the following command from the
top folder:
pytest tests/test_onyx_analysis_helper.py -rP --basetemp tests/test_outputs/

WARNING: Using --basetemp on an existing folder will overwrite all files.
"""

import datetime
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
def missing_field_dict_json():
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
        "methods": '{"versions": [{"name": "a_great_tool", "version": "1.0.0"}, {"name": "another_great_tool", "version": "2000.0.0"}], "thresholds": {"limit": 10}, "method2": "method example 2"}',
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
def missing_output_dict_json():
    field_dict = {
        "name": "test-analysis",
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "methods": '{"versions": [{"name": "a_great_tool", "version": "1.0.0"}, {"name": "another_great_tool", "version": "2000.0.0"}], "thresholds": {"limit": 10}, "method2": "method example 2"}',
        "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
        "synthscape_records": ["ID-123456789"],
        "identifiers": [],
    }

    return field_dict


@pytest.fixture
def missing_output_log():
    logs = ["Fields dict must contain one of: ['report', 'outputs']"]
    return logs


@pytest.fixture
def missing_both_dict_json():
    field_dict = {
        "description": "This is a test analysis",
        "analysis_date": "2025-08-21",
        "pipeline_name": "test-pipeline",
        "pipeline_url": "test-pipeline-url",
        "pipeline_version": "0.1.0",
        "result": "test result",
        "upstream_analyses": [],
        "methods": '{"versions": [{"name": "a_great_tool", "version": "1.0.0"}, {"name": "another_great_tool", "version": "2000.0.0"}], "thresholds": {"limit": 10}, "method2": "method example 2"}',
        "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
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
def invalid_field_dict_json():
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
        "methods": '{"versions": [{"name": "a_great_tool", "version": "1.0.0"}, {"name": "another_great_tool", "version": "2000.0.0"}], "thresholds": {"limit": 10}, "method2": "method example 2"}',
        "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
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


# Tests
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
        ("complete_field_dict_json", "no_error_log", False),
        ("missing_field_dict_json", "missing_field_log", True),
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
        ("complete_field_dict_json", "no_error_log", False),
        ("missing_output_dict_json", "missing_output_log", True),
    ],
)
def test_check_required_outputs(field_dict, expected_log_message, expected_output, request, caplog):
    field_dict = request.getfixturevalue(field_dict)
    expected_log_message = request.getfixturevalue(expected_log_message)

    analysis = oa.OnyxAnalysis()
    # populate the analysis table class with the attributes from the fixture:
    for key, value in field_dict.items():
        setattr(analysis, key, value)

    output_fail = analysis._check_required_outputs()

    assert all(messages in caplog.text for messages in expected_log_message)
    assert output_fail == expected_output


def test_read_analysis_from_json_pass(example_onyx_json_file, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis.read_analysis_from_json(example_onyx_json_file)
    assert analysis.__dict__ == complete_field_dict


def test_set_analysis_attributes(complete_field_dict_json, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis._set_analysis_attributes(complete_field_dict_json)

    assert analysis.__dict__ == complete_field_dict


def test_check_analysis_attributes_pass(complete_field_dict_json, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    # populate the analysis table class with the attributes from the fixture:
    for key, value in complete_field_dict_json.items():
        setattr(analysis, key, value)
    attr_fail = analysis._check_analysis_attributes()

    assert not attr_fail


def test_check_analysis_attributes_fail(invalid_field_dict_json, caplog):
    analysis = oa.OnyxAnalysis()
    for field, value in invalid_field_dict_json.items():
        setattr(analysis, field, value)
    attr_fail = analysis._check_analysis_attributes()

    message = "Invalid attribute in onyx analysis: ['invalid_name']"

    assert message in caplog.text
    assert attr_fail


@pytest.mark.parametrize(
    "test_input,publish_boolean,expected_output",
    [
        pytest.param(
            "missing_output_dict_json",
            False,
            [False, False],
            id="Correct input for prepublish analysis object - no errors",
        ),
        pytest.param(
            "missing_both_dict_json",
            False,
            [True, False],
            id="Incorrect input for prepublish analysis object - missing field fail",
        ),
        pytest.param(
            "complete_field_dict_json",
            True,
            [False, False, False],
            id="Correct input for publish analysis object - no errors",
        ),
        pytest.param(
            "invalid_field_dict_json",
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
    status_list = analysis.check_analysis_object(publish_analysis=publish_boolean)
    # print("\n", status_list)

    assert status_list == expected_output


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


MOCK_ONYX_RECORD_OLD: dict[str, str] = {
    "climb-id": "ID-123456",
    "site": "test",
    "published_date": "2026-01-01",
    "classifier_version": "1.0.0",
    "classifier_db_date": "1970-01-01",
    "ncbi_taxonomy_date": "1970-01-01",
    "scylla_version": "1.0.0",
    "sylph_db_version": "1.0.0",
    "alignment_db_version": "1.0.0",
}

MOCK_ONYX_RECORD_NEW: dict[str, str | list[dict[str, str]]] = {
    "climb-id": "ID-123456",
    "site": "test",
    "published_date": "2026-01-01",
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


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test___get_versions_from_onyx(mocked_onyx_get, caplog):
    """
    Test getting the versions from onyx with the old style - where the versions are across seperate
    fields. These get combined and reformatted in to the list of dicts.
    The onyx query (client.get) is mocked.
    """
    # mock the onyx query return (the record) - you must mock the OnyxClient (or whatever is being
    # patched) where it is being imported, not where it is defined
    mocked_onyx_get.return_value = MOCK_ONYX_RECORD_OLD

    expected_versions_dicts: list[dict[str, str]] = [
        {"name": "classifier_version", "version": "1.0.0"},
        {"name": "classifier_db_date", "version": "1970-01-01"},
        {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
        {"name": "scylla_version", "version": "1.0.0"},
        {"name": "sylph_db_version", "version": "1.0.0"},
        {"name": "alignment_db_version", "version": "1.0.0"},
    ]

    actual_versions_dicts, exitcode = oa._get_versions_from_onyx(sample_id="ID-123456", server="")

    assert actual_versions_dicts == expected_versions_dicts
    assert exitcode == 0
    print(caplog.text)
    print(f"Got these versions from Onyx record (mock): {actual_versions_dicts}")


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test___get_versions_from_onyx_new_style(mocked_onyx_get, caplog):
    """
    Test getting the versions from onyx with the new style - where all versions are in one
    field called 'versions', already as a list of dicts like:
       'versions' = [{'name': 'tool', 'version':'1.0.0'}]
    The onyx query (client.get) is mocked.
    """
    # mock the onyx query return (the record) - you must mock the OnyxClient (or whatever is being
    # patched) where it is being imported, not where it is defined
    mocked_onyx_get.return_value = MOCK_ONYX_RECORD_NEW

    expected_versions_dicts: list[dict[str, str]] = [
        {"name": "classifier_version", "version": "1.0.0"},
        {"name": "classifier_db_date", "version": "1970-01-01"},
        {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
        {"name": "scylla_version", "version": "1.0.0"},
        {"name": "sylph_db_version", "version": "1.0.0"},
        {"name": "alignment_db_version", "version": "1.0.0"},
        {"name": "new_tool_coming_soon", "version": "0.0.1"},
    ]

    actual_versions_dicts, exitcode = oa._get_versions_from_onyx(sample_id="ID-123456", server="")

    assert actual_versions_dicts == expected_versions_dicts
    assert exitcode == 0
    print(caplog.text)
    print(f"Got these versions from Onyx record (mock): {actual_versions_dicts}")


def test_add_versions_to_methods_null_args(caplog):
    """Test that not providing any args does not fail but gives warning."""
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods()
    assert not methods_fail
    assert "Warning: No suitable arguments provided" in caplog.text


@pytest.mark.parametrize(
    "sample_id,server_name", [(None, "server"), ("ID-123456", None), (None, None)]
)
def test_add_versions_to_methods_no_sample_id_or_server_name(sample_id, server_name, caplog):
    """Test that not providing any of sample_id or server_name or neither logs an error."""
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        include_onyx_versions=True, sample_id=sample_id, server_name=server_name
    )
    assert methods_fail
    assert "Error" in caplog.text


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test_add_versions_to_methods(mock_method, caplog):
    """
    Test that add_methods functions gets the versions from the query when set to true and populates
    the attribute.
    """
    # mock what the _get_versions_from_onyx function returns:
    mock_method.return_value = MOCK_ONYX_RECORD_OLD

    expected_results = {
        "versions": [
            {"name": "classifier_version", "version": "1.0.0"},
            {"name": "classifier_db_date", "version": "1970-01-01"},
            {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
            {"name": "scylla_version", "version": "1.0.0"},
            {"name": "sylph_db_version", "version": "1.0.0"},
            {"name": "alignment_db_version", "version": "1.0.0"},
        ]
    }

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        include_onyx_versions=True, sample_id="ID-123456", server_name="synthscape"
    )
    print(caplog.text)
    assert analysis.methods == expected_results, "The analysis methods do not look as expected."
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


@patch("onyx_analysis_helper.onyx_analysis_helper_functions.OnyxClient.get")
def test_add_versions_to_methods_plus_tools(mock_method, caplog):
    """
    Test that add_methods functions gets the versions from the query when set to true and adds
    user defined tool versions and then populates the attribute.
    """
    # mock what the _get_versions_from_onyx function returns:
    mock_method.return_value = MOCK_ONYX_RECORD_OLD

    expected_results = {
        "versions": [
            {"name": "classifier_version", "version": "1.0.0"},
            {"name": "classifier_db_date", "version": "1970-01-01"},
            {"name": "ncbi_taxonomy_date", "version": "1970-01-01"},
            {"name": "scylla_version", "version": "1.0.0"},
            {"name": "sylph_db_version", "version": "1.0.0"},
            {"name": "alignment_db_version", "version": "1.0.0"},
            {"name": "my_pkg", "version": "v1.2.3"},
        ]
    }

    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        include_onyx_versions=True,
        sample_id="ID-123456",
        server_name="synthscape",
        tool_versions={"my_pkg": "v1.2.3"},
    )
    print(caplog.text)
    assert analysis.methods == expected_results, "The analysis methods do not look as expected."
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


def test_add_versions_to_methods_broken_onyx(caplog):
    """
    Test that methods_fail if the onyx call doesn't work.
    """
    analysis = oa.OnyxAnalysis()
    methods_fail = analysis.add_versions_to_methods(
        include_onyx_versions=True,
        sample_id="ID-123456",
        server_name="synthscape",
        tool_versions={"my_pkg": "v1.2.3"},
    )
    print(f"\nLog should record error: \n{caplog.text}")
    assert "Error: Onyx cannot query" in caplog.text
    assert methods_fail
    print("add_methods fails correctly if onyx cannot connect.")


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
        include_onyx_versions=False,
        tool_versions={"my_pkg": "v1.2.3"},
    )
    print(caplog.text)
    assert analysis.methods == expected_results, "The analysis methods do not look as expected."
    assert not methods_fail
    print(f"\nThe methods field correctly looks like: \n{analysis.methods}")


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
        ({"tool_version": "1.2.3"}, "Error: Cannot add 'tool_version'"),
        ({"versions": ["1.0.0", "2.0.0"]}, "Error: Cannot add 'versions'"),
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
