# v0.5.1 - Hotfix Onyx Query Failures

## Fixed:
If initial Onyx query fails, the record is returned as None. The wrapper then tries to use
`record.get()` which does not work on nonetype. The wrapper now checks the exitcode, and if not 0,
writes a line to the log, returns empty record dict, empty versions list, and exitcode 1.

# v0.5.0 - April 2026
## Added:
- simple function (query_onyx) to query onyx with decorator
- function (get_data_and_versions_from_onyx) to wrap around query and return versions and fields.
Recommendation going forward is  that modules that require versions must use this function to query,
or write a query that returns the necessary functions.

## Changed:
- add_versions_to_methods no longer queries, user must provide onyx versions.
- docs updated

## Fixed:
- the way dicts are handled in the analysis table class instance vs as json in the outputs. Added
_get_fields function that wrangles this neatly. Attributes are not instantiated unless added
explicitly.



# v0.4.0 - April 2026

## Added:
- Function to query onyx to get the versions of key databases/tools.
- 'add_versions_to_methods' method adds versions to the method dict. This can either add a dict given
    as an arg, or can query onyx and include predefined list of versions from Onyx.
- Unit tests for the new methods which uses patch to mock the returned query record.
- Function to add versions_hash calcualted from versions field onto methods


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
