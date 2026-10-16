"""Atomic synthetic evaluation artifacts, safe to inspect during a live run."""
import json
import time
from pathlib import Path


def write_json(path,values):
    path=Path(path)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding='utf8')
    for attempt in range(8):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            # Windows readers/antivirus can briefly deny replacement. Keep the
            # complete temp file and retry instead of losing a long live run.
            if attempt==7: raise
            time.sleep(min(.05*(2**attempt),.5))
