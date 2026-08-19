# Third-party license register

This directory records third-party components used or planned by FindCut. The current source milestone invokes FFmpeg as an external executable and uses PySide6 as the Qt application binding.

| Component | Use | License | Distribution note |
|---|---|---|---|
| PySide6 / Qt for Python | Desktop UI | LGPLv3/GPLv3/commercial, depending on selected Qt modules and distribution | Review the exact wheel notices and Qt license terms included in the release package. |
| FFmpeg | Media probing and export backend | LGPLv2.1+ by default; optional components may be GPL or nonfree | Use an LGPL-compatible dynamic build, record its configuration, include notices and corresponding source. |
| MLT | Future native preview/render adapter | LGPL | Not bundled in the current milestone. Re-evaluate module dependencies before integration. |
| libopenshot | Alternative future media engine | LGPLv3 | Not bundled in the current milestone. Confirm commercial redistribution terms if the distribution model changes. |

This register is engineering documentation, not legal advice. Release maintainers must preserve the exact license texts and notices for the binaries shipped in each release.
