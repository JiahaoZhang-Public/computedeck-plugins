This PR updates the official catalog to a published package version and the wheel digest returned by PyPI.

Before merging, check that:

- The linked release and wheel match the package and version in the entry.
- Permissions, supported core versions and license information match the released code.
- The wheel includes the plugin's built page, if it has one, and its license notices.
- CI passes and an installation from the catalog has been tested.

Code changes belong in a separate PR. Keep the catalog unchanged while package publishing is paused.
