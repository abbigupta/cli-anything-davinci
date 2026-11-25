# Installation and SDK discovery

Use 64-bit Python 3.10+ in a virtual environment. Install DaVinci Resolve Studio separately. Start the application, wait for it to load and set **Preferences → System → General → External scripting using → Local**. Follow Resolve's restart prompt if shown. The CLI connects to the local running instance.

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1
python -m pip install git+https://github.com/abbigupta/cli-anything-davinci.git
cli-anything-davinci --json doctor
```

For a local checkout, replace the pip command with `python -m pip install -e ".[dev]"`. The Git URL becomes available after publication. The vendor module and native library come from the Resolve installer.

## SDK locations

| OS | Scripting directory | Native library |
| --- | --- | --- |
| macOS | `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting`, or the app bundle's `Contents/Resources/Developer/Scripting` | `Contents/Libraries/Fusion/fusionscript.so` inside the app |
| Windows | `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting` | `%ProgramFiles%\Blackmagic Design\DaVinci Resolve\fusionscript.dll` |
| Linux | `/opt/resolve/Developer/Scripting` | `/opt/resolve/libs/Fusion/fusionscript.so` |

macOS discovery checks both `/Applications/DaVinci Resolve/DaVinci Resolve.app` and `/Applications/DaVinci Resolve.app`. Linux discovery also checks `/home/resolve`.

For a custom installation, set **RESOLVE_SCRIPT_API** to the Scripting directory or its Modules subdirectory and **RESOLVE_SCRIPT_LIB** to the native library file. An explicit missing path produces an error. When no module is found in these locations, the adapter also tries Python's normal module search path, including a vendor-configured PYTHONPATH.

macOS or Linux, using the actual paths for your installation:

```sh
export RESOLVE_SCRIPT_API="/custom/resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/custom/resolve/libs/Fusion/fusionscript.so"
cli-anything-davinci doctor
```

Windows PowerShell:

```powershell
$env:RESOLVE_SCRIPT_API = "$env:ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB = "$env:ProgramFiles\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
cli-anything-davinci doctor
```

The running API supplies the product name and version. On macOS, doctor can also read the installed bundle version while disconnected. On other platforms, version reporting requires a connection. Blackmagic documents the external scripting preference for Studio. Free can include the SDK files and internal console while denying external sessions.
