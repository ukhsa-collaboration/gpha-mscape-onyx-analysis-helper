"""
Unit tests for s3 functions included in this repo. To save
generated test results in the repo, run the following command from the
top folder:
pytest tests/test_s3_functions.py -rP --basetemp tests/test_outputs/

WARNING: Using --basetemp on an existing folder will overwrite all files.
"""

import os

import boto3
import pytest
from moto import mock_aws
from moto.server import ThreadedMotoServer

from onyx_analysis_helper import s3_functions as s3f


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
def example_result_file():
    result_dir = "tests/test_data/C-123456789_qc_results.json"

    return result_dir


@pytest.fixture
def example_result_file_sha256():
    checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    return checksum


@pytest.fixture
def s3_file(s3_client, test_bucket, example_result_file):
    s3_client.upload_file(example_result_file, "testbucket", "A-1234_C-123456789_qc_results.json")


@pytest.fixture
def download_file_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("test_outputs")
    return str(tmp_dir)


# Tests
def test_make_s3_name(example_result_file):
    s3_key = s3f._make_s3_key_name(analysis_id="A-1234", file_for_upload=example_result_file)
    print(s3_key)
    assert s3_key == "A-1234_C-123456789_qc_results.json"


@mock_aws
def test_set_up_s3_client(moto_server):
    s3_client = s3f.set_up_s3_client(endpoint_url=moto_server)

    s3_client.create_bucket(Bucket="test")
    result = s3_client.list_buckets()

    assert len(result["Buckets"]) == 1


@mock_aws
def test_upload_file_to_s3(s3_client, test_bucket, example_result_file, example_result_file_sha256):
    tuple_return = s3f.upload_file_to_s3(
        analysis_id="A-1234",
        bucket="testbucket",
        file_for_upload=example_result_file,
        s3_client=s3_client,
    )

    response = s3_client.head_object(Bucket="testbucket", Key="A-1234_C-123456789_qc_results.json")

    assert tuple_return == ("s3://testbucket/A-1234_C-123456789_qc_results.json", 0)
    assert (
        response["ResponseMetadata"]["HTTPHeaders"]["x-amz-content-sha256"]
        == example_result_file_sha256
    )


@mock_aws
def test_upload_file_to_s3_client_error_handling(s3_client, test_bucket, example_result_file):
    tuple_return = s3f.upload_file_to_s3(
        analysis_id="A-1234",
        bucket="wrongbucket",
        file_for_upload=example_result_file,
        s3_client=s3_client,
    )

    assert tuple_return == (None, 1)


@mock_aws
def test_upload_file_to_s3_generic_error_handling(s3_client, test_bucket):
    tuple_return = s3f.upload_file_to_s3(
        analysis_id="A-1234",
        bucket="testbucket",
        file_for_upload="notafile.json",
        s3_client=s3_client,
    )

    assert tuple_return == (None, 1)


def test_generate_local_sha256sum(example_result_file, example_result_file_sha256):
    checksum = s3f.generate_local_sha256sum(example_result_file)

    assert checksum == example_result_file_sha256


@mock_aws
def test_get_s3_checksum(s3_client, test_bucket, example_result_file_sha256, s3_file):
    tuple_return = s3f.get_s3_checksum(
        "testbucket", "A-1234_C-123456789_qc_results.json", s3_client
    )

    assert tuple_return == (example_result_file_sha256, 0)


@mock_aws
def test_get_s3_checksum_error_handling(s3_client, test_bucket, s3_file):
    tuple_return = s3f.get_s3_checksum("testbucket", "wrongkey", s3_client)

    assert tuple_return == (None, 1)


def test_check_sha256sums_match_pass(example_result_file_sha256):
    result = s3f.check_sha256sums_match(example_result_file_sha256, example_result_file_sha256)

    assert result == 0


def test_check_sha256sums_match_fail(example_result_file_sha256):
    result = s3f.check_sha256sums_match(example_result_file_sha256, "incorrectsha256string")

    assert result == 1


@mock_aws
def test_download_file_from_s3(s3_client, test_bucket, s3_file, download_file_path):
    out_file, exitcode = s3f.download_file_from_s3(
        s3_client, "testbucket", "A-1234_C-123456789_qc_results.json", download_file_path
    )

    assert out_file.exists()
    assert exitcode == 0


@mock_aws
def test_download_file_from_s3_error_handling(s3_client, test_bucket, s3_file, download_file_path):
    tuple_return = s3f.download_file_from_s3(
        s3_client, "testbucket", "wrongkey", download_file_path
    )

    assert tuple_return == (None, 1)
