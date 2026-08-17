#!/usr/bin/env python3

"""
Module containing functions to assist with the reading of analysis
objects to and from s3.
"""

import hashlib
import logging
import os
from functools import wraps
from pathlib import Path

import boto3
import regex as re
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def call_to_s3(func):
    """Decorator that provides error handling for any calls to s3.
    If call is successful, returns the result and an exitcode of 0.
    If call is unsucessful, returns None and an exitcode of 1.
    """

    @wraps(func)
    def call_to_s3_wrapper(*args, **kwargs):
        try:
            logger.debug("Attempting connection to s3")
            result, exitcode = func(*args, **kwargs)
            logger.debug("Successful connection to s3")

            return result, exitcode

        except ClientError as exc:
            logger.error("Client error: %s.", exc)
            result = None
            exitcode = 1

            return result, exitcode

        except FileNotFoundError as exc:
            logger.error("Check file or directory path is correct: %s", exc)
            result = None
            exitcode = 1

            return result, exitcode

        except Exception as exc:
            logger.error("Unhandled error: %s", exc)
            result = None
            exitcode = 1

            return result, exitcode

    return call_to_s3_wrapper


def set_up_s3_client(endpoint_url: str = "https://s3.climb.ac.uk") -> boto3.client:
    """Sets up s3 client including config options such as number of retries.
    Default for endpoint_url can be overridden for testing purposes.
    Returns an s3 client.
    """

    s3_config = Config(retries={"total_max_attempts": 3, "mode": "standard"})

    s3_client = boto3.client("s3", config=s3_config, endpoint_url=endpoint_url)

    return s3_client


@call_to_s3
def upload_file_to_s3(
    analysis_id: str, bucket: str, file_for_upload: os.path, s3_client: boto3.client
) -> str:
    """Uploads a file to s3 bucket using the analysis ID to generate a path
    Arguments:
        analysis_id -- Name of analysis in onyx
        bucket -- Name of bucket in s3
        file_for_upload -- Analysis file to be uploaded to s3
        s3_client -- Client for interacting with s3
    Returns tuple of:
        s3_uri - Path to object in s3
        exitcode - Exit status
    """
    # Make name for s3 object that includes analysis ID
    s3_key = _make_s3_key_name(analysis_id, file_for_upload)

    # Upload file
    s3_client.upload_file(file_for_upload, bucket, s3_key)
    s3_uri = f"s3://{bucket}/{s3_key}"
    exitcode = 0

    return s3_uri, exitcode


def _make_s3_key_name(analysis_id: str, file_for_upload: os.path) -> str:
    """Create a key name for the file to be uploaded to s3 that includes
    the analysis ID and analysis type.
    Arguments:
        analysis_id -- Name of analysis in onyx
        file_for_upload -- Analysis file to be uploaded to s3
    Returns:
        s3_key - Name for object in s3
    """
    # Get name of file without rest of path
    upload_file = Path(file_for_upload).name

    # Join with analysis id
    s3_key = f"{analysis_id}/{analysis_id}_{upload_file}"

    return s3_key


def generate_local_checksum(file_for_upload: os.path, checksum_type: str) -> str:
    """Generates a checksum for local copy of file that will be
    uploaded. Returns sha256 or md5 checksum"""
    with Path(file_for_upload).open("rb") as file:
        digest = hashlib.file_digest(file, f"{checksum_type}")

    checksum = digest.hexdigest()

    return checksum


@call_to_s3
def get_s3_checksum(bucket: str, s3_key: str, s3_client: boto3.client, checksum_type: str):
    """Retrieves checksum from s3 object metadata.
    Arguments:
        bucket -- Name of bucket in s3 where object is stored
        s3_key -- Name of object in s3
        s3_client -- Client for interacting with s3
        checksum_type -- Algorithm for checksum
    Returns tuple of:
        checksum -- sha256 or etag sum for s3 object, None if error
        exitcode - 0 for success, 1 for failure
    """
    response = s3_client.head_object(Bucket=bucket, Key=s3_key)

    if checksum_type == "sha256":
        checksum = response["ResponseMetadata"]["HTTPHeaders"]["x-amz-content-sha256"]

    elif checksum_type == "etag":
        checksum = response["ResponseMetadata"]["HTTPHeaders"]["etag"]
        # Get md5 from within nested "" in etag
        checksum = re.search('"(.*)"', checksum).group(1)
    else:
        logger.error("Invalid checksum type provided, provide one of sha256 or etag")
        result = None
        exitcode = 1

        return result, exitcode

    exitcode = 0

    return checksum, exitcode


def check_checksums_match(local_checksum, s3_checksum):
    """Check s3 checksum and local checksum match. Returns
    exitcode of 0 if checksums match, 1 if they do not.
    """

    if local_checksum == s3_checksum:
        logger.info("Local and s3 checksums match")
        return 0
    else:
        logger.error("Local and s3 checksums do not match")
        return 1


@call_to_s3
def download_file_from_s3(s3_client: boto3.client, bucket: str, s3_key: str, out_dir: os.path):
    """Downloads object from s3.
     Arguments:
        s3_client -- Client for interacting with s3
        bucket -- Name of bucket in s3 where object is stored
        s3_key -- Name of object in s3
        out_dir -- Location to download the file to
    Returns tuple of:
        result_file -- Path to downloaded s3 object
        exitcode - 0 for success, 1 for failure
    """
    s3_key_no_prefix = s3_key.split("/")[-1]
    result_file = Path(out_dir) / f"{s3_key_no_prefix}"

    s3_client.download_file(bucket, s3_key, result_file)

    exitcode = 0

    return result_file, exitcode
