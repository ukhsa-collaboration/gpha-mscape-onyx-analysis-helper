#!/usr/bin/env python3

"""Script and associated functions to upload analyses to onyx
and add files to s3.
"""

# Imports
import argparse
import logging
import os
import sys
from pathlib import Path

import boto3
from onyx import OnyxConfig, OnyxEnv

from onyx_analysis_helper import onyx_analysis_helper_functions as oa
from onyx_analysis_helper import s3_functions as s3f

# Set up onyx config
CONFIG = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)


# Functions
# Args and logging
def get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(
        prog="onyx_helper",
        description="""Script with sub-commands to populate onyx analysis
        table and push analysis files to s3.
        """,
    )

    # Set up parsers and sub-parsers
    base_subparser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add base args shared by all sub-parsers
    base_subparser.add_argument("--climbid", "-i", type=str, required=True, help="Sample ID")
    base_subparser.add_argument(
        "--output", "-o", type=str, required=True, help="Folder to save outputs"
    )
    base_subparser.add_argument(
        "--server",
        "-s",
        type=str,
        required=True,
        choices=["mscape", "synthscape"],
        help="Specify server code is being run on",
    )

    # Add group for test or prod run of code
    group = base_subparser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--test",
        required=False,
        action="store_true",
        help="Use this option to do a test upload and check for errors before attempting an upload to onyx/s3",
    )
    group.add_argument(
        "--prod",
        required=False,
        action="store_true",
        help="Use this option to upload results to onyx/s3",
    )

    # Add subparsers and specific args for each
    # Onyx write
    onyx_write_subparser = subparsers.add_parser(
        "write", parents=[base_subparser], help="Write initial analysis table to onyx"
    )
    onyx_write_subparser.add_argument(
        "--input-json", "-j", type=Path, help="Path to input file with onyx analysis json"
    )

    # s3 push
    s3_subparser = subparsers.add_parser(
        "s3_upload", parents=[base_subparser], help="Push analysis files to s3"
    )
    s3_subparser.add_argument("--bucket", "-b", type=str, help="s3 bucket to push files to")
    s3_subparser.add_argument("--analysis-id", "-a", type=str, help="File containing analysis ID")
    s3_subparser.add_argument(
        "--input-files", "-f", type=str, help="Comma separated list of files to be uploaded to s3"
    )
    # Onyx update
    onyx_update_subparser = subparsers.add_parser(
        "update", parents=[base_subparser], help="Update onyx analysis with s3 paths"
    )
    onyx_update_subparser.add_argument(
        "--analysis-id", "-a", type=str, help="File containing analysis ID"
    )
    onyx_update_subparser.add_argument(
        "--input-json", "-j", type=Path, help="Path to file of s3 file locations"
    )

    # Onyx publish
    onyx_publish_subparser = subparsers.add_parser(
        "publish", parents=[base_subparser], help="Publish onyx analysis"
    )
    onyx_publish_subparser.add_argument(
        "--analysis-id", "-a", type=str, help="File containing analysis ID"
    )

    return parser.parse_args()


def set_up_logger(stdout_file):
    """Creates logger for component - all logging messages go to stdout
    log file, error messages also go to stderr log. If component runs
    correctly, stderr is empty.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

    out_handler = logging.FileHandler(stdout_file, mode="a")
    out_handler.setFormatter(formatter)
    logger.addHandler(out_handler)

    return logger


# General functions
def read_analysis_id_from_file(analysis_id_file: Path, exitcode: int) -> tuple[str | None, int]:
    """Function to read in analysis ID from file. If file not correct structure or can't be
    found, a non-zero exitcode is returned.
    Arguments:
        analysis_id_file -- Text file containing analysis ID
        exitcode -- Exitcode from parent code - should be 0
    Returns:
        analysis_id -- Analysis ID from onyx
        exitcode -- Exitcode for function, remains as 0 if analysis ID read correctly
    """
    try:
        with Path(analysis_id_file).open("r") as file:
            lines = [line.rstrip() for line in file]
            # Need code to catch if for some reason the analysis_id_file has >1 analysis_id in it
            # e.g. something like if len(lines) != 1: crash with exitcode=1
            if len(lines) == 1:
                analysis_id = lines[0]
                logging.info("Analysis ID read from file %s", analysis_id_file)
            else:
                logging.error(
                    "Analysis_id_file should contain 1 line: %s contained %s lines",
                    analysis_id_file,
                    len(lines),
                )
                exitcode = 1
                return None, exitcode
    except Exception as error:
        logging.error("Couldn't read analysis_id from file: %s, %s", analysis_id_file, error)
        exitcode = 1
        return None, exitcode

    return analysis_id, exitcode


def upload_files_to_s3(
    files_for_upload: str, analysis_id: str, bucket: str, s3_client: boto3.client
) -> tuple[list, int]:
    """Function for attempting to write a list of files to s3. Returns a non-zero
    exitcode if unsuccessful.
    Arguments:
        files_for_upload -- Str list of files to be uploaded to s3
        analysis_id -- Analysis ID to include in s3 file name
        bucket -- Bucket to upload files to
    Returns:
        s3_locations -- List of locations of files in s3
        exitcode -- Exitcode for function, remains as 0 if all files successfully added to s3
    """
    exitcode = 0
    # Get paths for files to be uploaded
    local_file_list = files_for_upload.split(",")
    # List to store s3 URIs
    s3_file_list = []
    # Attempt upload to s3
    for file in local_file_list:
        s3_uri, exitcode = s3f.upload_file_to_s3(
            analysis_id=analysis_id, bucket=bucket, file_for_upload=file, s3_client=s3_client
        )
        s3_file_list.append(s3_uri)
        if exitcode == 0:
            logging.info("S3 transfer complete for %s", file)
        else:
            logging.error("S3 transfer failed for %s, see logs for details", file)
            return None, exitcode  # Exit s3 upload attempts if any fail? Or try other files?

    return s3_file_list, exitcode


def write_s3_locations_to_json(
    s3_locations: list, analysis_id: str, bucket: str, outdir: Path, climb_id: str
) -> Path:
    """Function to write the s3 keys for uploaded files to an output file
    in OnyxAnalysis structure json.
    Arguments:
        s3_locations -- List containing s3 uri's for all uploaded files
        analysis_id -- Analysis ID
        bucket -- Bucket s3 files were uploaded to
        outdir -- Location to store s3 location json file
    Returns:
        s3_locations_file -- File containing onyx analysis json with s3 URI
    """
    onyx_analysis = oa.OnyxAnalysis()
    # Add files to outputs field - if one file use whole URI, if multiple files use prefix
    if len(s3_locations) == 1:
        s3_output_location = f"{s3_locations[0]}"
        onyx_analysis.outputs = s3_output_location
    else:
        s3_output_location = f"s3://{bucket}/{analysis_id}"
        onyx_analysis.outputs = s3_output_location
    # TODO: Handle HTML/report
    # Write s3 locations to onyx analysis json
    s3_file = Path(outdir) / f"{climb_id}.onyx_analysis.s3_upload.analysis_fields.json"

    s3_json = onyx_analysis.write_analysis_to_json(s3_file)

    return s3_json


# Main script
def main():
    "Main function to handle onyx helper commands"
    args = get_args()
    exitcode = 0

    # Set up log file
    log_file = Path(args.output) / f"{args.climbid}.onyx_analysis.{args.command}.log.txt"
    set_up_logger(log_file)

    # Check if test or prod run
    if args.test:
        dryrun = True
    elif args.prod:
        dryrun = False

    if args.command == "write":
        # Check if analysis ID file already exists
        analysis_id_file = (
            Path(args.output) / f"{args.climbid}.onyx_analysis.{args.command}.analysis_id.txt"
        )
        if analysis_id_file.exists():
            logging.info("Existing analysis ID file found, exiting program")
            return exitcode
        # Read in analysis json
        try:
            onyx_analysis = oa.OnyxAnalysis()
            onyx_analysis.read_analysis_from_json(args.input_json)
            logging.info("Analysis table successfully read from json: %s", args.input_json)
        except Exception as error:
            logging.error("Couldn't read analysis from json: %s, %s", args.input_json, error)
            exitcode = 1
            return exitcode
        # Check correctly formatted
        check_status_list = onyx_analysis.check_analysis_object(publish_analysis=False)
        if any(status for status in check_status_list):  # noqa SIM108
            logging.error("Analysis fields read in from json failed checks")
            exitcode = 1
            return exitcode
        # Write to onyx
        analysis_id, exitcode = onyx_analysis.write_analysis_to_onyx(
            server=args.server,
            dryrun=dryrun,
            publish_analysis=False,
        )
        if exitcode != 0:
            logging.error("Unsuccessful write to onyx, check logs for details.")
            return exitcode
        # Write analysis ID to file
        if not dryrun:
            analysis_id = analysis_id['analysis_id']
        with Path(analysis_id_file).open("w") as file:
            file.write(f"{analysis_id}")
        logging.info("Analysis ID written to file %s", analysis_id_file)

        return exitcode

    elif args.command == "s3_upload":
        # Read in analysis id from file
        analysis_id, exitcode = read_analysis_id_from_file(args.analysis_id, exitcode)
        if exitcode != 0:
            return exitcode
        # Set up s3 client
        s3_client = s3f.set_up_s3_client()
        # Upload files to s3
        s3_locations, exitcode = upload_files_to_s3(
            args.input_files, analysis_id, args.bucket, s3_client
        )
        if exitcode != 0:
            return exitcode
        # Write s3 locations to onyx analysis json
        s3_json = write_s3_locations_to_json(
            s3_locations, analysis_id, args.bucket, args.output, args.climbid
        )
        logging.info("s3 information written to file %s", s3_json)

        return exitcode

    elif args.command == "update":
        # Read in analysis id from file
        analysis_id, exitcode = read_analysis_id_from_file(args.analysis_id, exitcode)
        if exitcode != 0:
            return exitcode
        # Read in analysis json
        onyx_analysis = oa.OnyxAnalysis()
        try:
            onyx_analysis.read_analysis_from_json(args.input_json)
            logging.info("Analysis table successfully read from json: %s", args.input_json)
        except Exception as error:
            logging.error("Couldn't read analysis from json: %s, %s", args.input_json, error)
            exitcode = 1
            return exitcode
        # Write to onyx
        analysis_id, exitcode = onyx_analysis.update_onyx_analysis(
            server=args.server,
            analysis_id=analysis_id,
            dryrun=dryrun,
            publish_analysis=False,
        )
        if exitcode != 0:
            logging.error("Unsuccessful write to onyx, check logs for details.")
            return exitcode
        # Write analysis ID to file
        analysis_id_file = (
            Path(args.output) / f"{args.climbid}.onyx_analysis.{args.command}.analysis_id.txt"
        )
        with Path(analysis_id_file).open("w") as file:
            file.write(f"{analysis_id['analysis_id']}")

        return exitcode

    elif args.command == "publish":
        # Read in analysis id from file
        analysis_id, exitcode = read_analysis_id_from_file(args.analysis_id, exitcode)
        if exitcode != 0:
            return exitcode
        # Update publish status
        onyx_analysis = oa.OnyxAnalysis()
        analysis_id, exitcode = onyx_analysis.update_onyx_analysis(
            server=args.server,
            analysis_id=analysis_id,
            dryrun=dryrun,
            publish_analysis=True,
        )
        if exitcode != 0:
            logging.error("Unsuccessful publishing of onyx analysis, check logs for details.")
        # Write analysis ID to file
        analysis_id_file = (
            Path(args.output) / f"{args.climbid}.onyx_analysis.{args.command}.analysis_id.txt"
        )
        with Path(analysis_id_file).open("w") as file:
            file.write(f"{analysis_id['analysis_id']}")

        return exitcode

    return exitcode


if __name__ == "__main__":
    sys.exit(main())