# v0.4.0 - April 2026

## Added:
Function to query onyx to get the versions of key databases/tools.
'add_versions_to_methods' method adds versions to the method dict. This can either add a dict given
as an arg, or can query onyx and include predefined list of versions from Onyx.
Unit tests for the new methods which uses patch to mock the returned query record.


## Changed:
'add_methods' method will no longer allow any key with 'version'. This must be provided with new
'add_versions_to_methods' method.
Changed the unit test for the 'add_methods' method.
Changed the 'write_analysis_to_json' and 'read_analysis_from_json' to write to and read from json
strings respectively, converting between dict and json.
Removed any '_set_analysis_attributes' method use in unit tests and replaced with the code to
populate the analysis table in the test itself (avoid double testing).


## Fixed:
Type hints - replaced os.path with Path, and json.dumps returns a str.
Breaking unit tests - changed test file names.
