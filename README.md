# overbuild

Runtime instrumentation for Python projects to detect unreached and cold code paths under real workloads.

This MVP installs an import hook from the top of your entry file, instruments project-local modules at import time, and records function and branch hit counts into a JSON report on process exit.

## What it does

- install an import hook as early as possible
- instrument only project-local `.py` files
- count:
  - function entries
  - `if` true/false branch hits
- write a report at exit to `overbuild_report.json`

## Quick start

Put this at the very top of your entry file:

```python
from overbuild import install_import_hook
install_import_hook()
```

Then run your app normally.

## Example

```python
# main.py
from overbuild import install_import_hook
install_import_hook()

import sample_app.service as service

if __name__ == "__main__":
    service.run(True)
    service.run(False)
```

## Output

Example `overbuild_report.json`:

```json
{
  "func:/abs/path/sample_app/service.py:run:1": 2,
  "branch:/abs/path/sample_app/service.py:2:true": 1,
  "branch:/abs/path/sample_app/service.py:2:false": 1
}
```

## Notes

- The entry file itself is usually **not** instrumented, because the hook is installed after that file has already started executing.
- This finds **runtime-unreached** code under observed workloads, not mathematically proven dead code.
- Only modules imported **after** `install_import_hook()` are instrumented.

## Minimal usage pattern

```python
from overbuild import install_import_hook
install_import_hook()

import app
app.main()
```

## Report generation ideas

This MVP writes raw counters. You can post-process them into:
- never-called functions
- zero-hit branches
- low-frequency paths
- 7d / 30d / 90d rollups

## License

MIT
