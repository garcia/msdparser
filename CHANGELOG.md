# 1.1.0

**Bugfix/feature:** Escape sequences are now handled by default. While this is
technically a breaking change, the absence of this feature was a bug in the
spec, hence the lack of major version bump. Backslash escapes can be disabled
by passing `escapes=False` to `parse_msd`, restoring the 1.0.0 behavior
and preserving spec-compliant parsing of e.g. DWI files.

**Feature:** The return type of `parse_msd` has been changed from
`Tuple[str, str]` to `MSDParameter`, which is a `NamedTuple` of two strings,
`key` and `value`. Stringifying an `MSDParameter` interpolates the key/value
pair into the MSD `#KEY:VALUE;` format, escaping special characters by default.

# 1.0.0

Initial stable release.