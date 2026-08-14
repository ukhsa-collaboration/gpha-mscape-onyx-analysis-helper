# v0.6.3 - Patch silence toggle for onyx queries
Problem: Onyx queries exceptions should not always be silenced, allow users to allow exceptions to
be raised with toggle arg in wrapped functions. Implement this in the onyx query functions.

## Add:
- decorator parses the args from the func and if silence is present (either by default or specified
on function call) then use that, else default to True. If True, do not raise exceptions.

_Not a Breaking change_

---
---


# v0.6.1 - Patch publish to onyx
Problem: the update_onyx_analysis function would take the fields of the onyx analysis object, then
set the 'is_published' attribute on the object, but fields (without that attribute) was given to
onyx to publish.

## Fix:
- create _get_onyx_payload function on the object which takes 'publish' boolean as arg, and returns
a payload contains the fields to be updated in onyx, with any dicts converted json.

## Added:
- unittests for _get_onyx_payload.
- explanation in readme.

---
---

# v0.6.0 - Query for analysis tables.

## Added:
- get_analysis_records - gets all analysis records associated with a given sample id.
- trunate_versions function to get major, minor or patch from given version string.
- units tests for both of the above, with patches for the onyx queries.

## Changed:
- Onyx versions hash added when the onyx versions are added to 'onyx_versions_hash' in the methods
in the analysis table.
- unit tests updated to account for above.

---

---


# v0.5.1 - Hotfix Onyx Query Failures

## Fixed:
If initial Onyx query fails, the record is returned as None. The wrapper then tries to use
`record.get()` which does not work on nonetype. The wrapper now checks the exitcode, and if not 0,
writes a line to the log, returns empty record dict, empty versions list, and exitcode 1.

---

---

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

---

---

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
