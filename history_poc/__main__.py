"""Build and verify the tiny offline account-state demonstration."""

import argparse
import json
from pathlib import Path
import time

from .store import build_history


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        fixture = json.loads(args.fixture.read_bytes())
        manifest = build_history(fixture, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"history_poc: error: {error}\n")
    print(
        json.dumps(
            {
                "accounts": len(fixture["accounts"]),
                "versions_verified": manifest["version_count"],
                "patch_objects": manifest["patch_objects"],
                "full_record_bytes": manifest["full_record_bytes"],
                "encoded_object_bytes": manifest["encoded_object_bytes"],
                "compressed_payload_bytes": manifest["compressed_payload_bytes"],
                "compressed_index_bytes": (args.output / "index.zst").stat().st_size,
                "manifest_bytes": (args.output / "manifest.json").stat().st_size,
                "manifest_digest_bytes": (args.output / "manifest.json.sha256").stat().st_size,
                "local_demo_seconds": time.perf_counter() - started,
                "rpc_requests": 0,
                "svm_executions": 0,
                "warning": "This tiny example is not the original native benchmark or a production latency test",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
