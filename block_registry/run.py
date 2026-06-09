#!/usr/bin/env python3
"""
Universal wrapper for Cerebrum blocks.
Reads JSON from stdin, executes block.run(inputs), writes JSON to stdout.
"""

import sys
import json
import traceback


def main():
    # Read input JSON from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    # Import the block's run function
    try:
        from block import run
    except ImportError as e:
        print(json.dumps({"success": False, "error": f"block.py must define a 'run' function: {e}"}))
        sys.exit(1)

    # Execute the block
    try:
        result = run(**input_data)
        output = {"success": True, "output": result}
    except Exception as e:
        output = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(output))
        sys.exit(1)

    print(json.dumps(output))
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":
    main()
