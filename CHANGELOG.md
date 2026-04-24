# v0.4.0 - April 2026

## Added:
- Function to query onyx to get the versions of key databases/tools.
- Extra function to add custom methods to the methods field in the analysis table. Now, add_methods
must be run first, then add_other_methods run afterwards (optional).
- Unit tests for the new function which uses patch to mock the returned query record.
- OnyxAnalysis method to add a calculated hash from all versions to the methods as versions_hash.


## Changed:
Changed add_methods analysis table method to call the new function. The add_methods method now
requires:
- sample_id
- server
- tool_versions (optional)
Changed the unit test for the add_methods method.
Changed the write_analysis_to_json and read_analysis_from_json to write to and read from json
strings respectively, converting between dict and json.
Removed any '_set_analysis_attributes' method use in unit tests and replaced with the code to
populate the analysis table in the test itself (avoid double testing).


## Fixed:
Type hints - replaced os.path with Path, and json.dumps returns a str.
Breaking unit tests.
