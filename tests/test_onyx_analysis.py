#!/usr/bin/env python3

"""
Unit tests for functions in the onyx_analysis.py
script in bin/.
"""

import json
import logging
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws
from moto.server import ThreadedMotoServer
from onyx_analysis_helper import s3_functions as s3f  # noqa: F401
from onyx_analysis_helper import onyx_analysis as oas

# Fixtures
@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="module")
def moto_server(aws_credentials):
    """Fixture to run a mocked AWS server for testing."""

    # Note: pass `port=0` to get a random free port.
    server = ThreadedMotoServer(port=0)
    server.start()
    host, port = server.get_host_and_port()
    yield f"http://{host}:{port}"
    server.stop()


@pytest.fixture
def s3_client(moto_server):
    with mock_aws():
        s3_client = boto3.client("s3", endpoint_url=moto_server)
        yield s3_client


@pytest.fixture
def test_bucket(s3_client):
    s3_client.create_bucket(Bucket="testbucket")


@pytest.fixture
def analysis_id_file():
    file = "tests/test_data/ID-123456789.onyx_analysis.write.analysis_id.txt"
    return file


@pytest.fixture
def quality_file():
    file = "tests/test_data/ID-123456789_quality_system_data.csv"
    return file


@pytest.fixture
def result_file():
    file = "tests/test_data/ID-123456789_result_data.csv"
    return file


@pytest.fixture
def data_file():
    file = "tests/test_data/ID-123456789_alldata.csv"
    return file




@pytest.fixture
def s3_file_list():
    files = [
        "s3://testbucket/ID-1234/ID-1234_ID-123456789_quality_system_data.csv",
        "s3://testbucket/ID-1234/ID-1234_ID-123456789_result_data.csv",
        "s3://testbucket/ID-1234/ID-1234_ID-123456789_alldata.csv",
    ]
    return files


@pytest.fixture
def s3_file(s3_client, test_bucket, example_result_file):
    s3_client.upload_file(
        example_result_file, "testbucket", "ID-1234/ID-1234_ID-123456789_quality_system_data.csv"
    )


@pytest.fixture
def output_file_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("test_outputs")
    return str(tmp_dir)


@pytest.fixture
def expected_s3_json():
    s3_json = {"identifiers": [], "outputs": "s3://testbucket/ID-1234", "methods": "{}", "result_metrics": "{}"}
    return s3_json


# Tests
def test_read_analysis_id_from_file(analysis_id_file):
    tuple_return = oas.read_analysis_id_from_file(analysis_id_file, 0)

    print(tuple_return)
    assert tuple_return == ("ID-1234", 0)

@mock_aws
def test_upload_file_to_s3(
    s3_client, test_bucket, quality_file, result_file, data_file, s3_file_list, caplog
):
    caplog.set_level(logging.INFO)

    files_for_upload = f"{quality_file},{result_file},{data_file}"
    print(files_for_upload)
    tuple_return = oas.upload_files_to_s3(
        files_for_upload=files_for_upload,
        analysis_id="ID-1234",
        bucket="testbucket",
        s3_client=s3_client,
    )

    print(tuple_return)
    assert tuple_return == (s3_file_list, 0)


def test_write_s3_locations_to_json(s3_file_list, output_file_path, expected_s3_json):
    s3_json_file = oas.write_s3_locations_to_json(
        s3_file_list, "ID-1234", "testbucket", output_file_path, "ID-123456789"
    )

    with Path.open(s3_json_file) as file:
        s3_json = json.load(file)
    print(s3_json)
    assert s3_json == expected_s3_json
