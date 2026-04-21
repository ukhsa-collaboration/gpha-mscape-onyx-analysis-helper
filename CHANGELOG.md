# v0.4.0 - April 2026

## Added:
Function to query onyx to get the versions of key databases/tools.
Unit tests for the new function which uses patch to mock the returned query record.


## Changed:
Changed add_methods analysis table method to call the new function. The add_methods method now
requires:
- sample_id
- server
- methods_dict
- tool_versions (optional)
Changed the unit test for the add_methods method.

## Fixed:
Type hints - replaced os.path with Path, and json.dumps returns a str.
