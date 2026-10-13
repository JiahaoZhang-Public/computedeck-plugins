# Contributing

Use fictional test data. Declare every permission, including each outbound destination.
Undeclared network access is not allowed. Provide English and Chinese labels, tests,
an explicit compatible core `requires` range, and an Apache-2.0-compatible license.
Run `bash scripts/check.sh` before proposing changes.

Third-party plugins stay in their authors' repositories. A catalog contribution must
pin the package version and include the digest of the actual published wheel. Review
permissions, source, dependencies, license, package contents and tests before accepting it.
Do not add unpublished packages, guessed digests or moving Git references to the catalog.
