# 1.1.0

**Bugfix/feature:** Escape sequences are now handled by default. While this is
technically a breaking change, the absence of this feature was a bug in the
spec, hence the lack of major version bump. Backslash escapes can be disabled
by passing `handle_escapes=False` to `parse_msd`, restoring the 1.0.0 behavior
and preserving spec-compliant parsing of e.g. DWI files.

# 1.0.0

Initial stable release.