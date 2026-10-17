"""Run Python inside the running Unreal Editor via Python Remote Execution.

Usage (with the engine's bundled Python):
    G:/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe Scripts/ue_py.py -c "print(unreal.SystemLibrary.get_engine_version())"
    G:/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe Scripts/ue_py.py path/to/script.py

Requires PythonScriptPlugin enabled with bRemoteExecution=True (see Config/DefaultEngine.ini).
"""
import argparse
import sys
import time

sys.path.insert(0, "G:/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python")
import remote_execution as rx  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--command", help="Python source to execute")
    group.add_argument("file", nargs="?", help="Python file to execute")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds to wait for an editor")
    args = parser.parse_args()

    source = args.command if args.command is not None else open(args.file, encoding="utf-8").read()

    remote = rx.RemoteExecution()
    remote.start()
    try:
        deadline = time.time() + args.timeout
        while not remote.remote_nodes and time.time() < deadline:
            time.sleep(0.25)
        if not remote.remote_nodes:
            print("No Unreal Editor found. Is it running with Python remote execution enabled?", file=sys.stderr)
            return 2

        remote.open_command_connection(remote.remote_nodes[0]["node_id"])
        result = remote.run_command(source, unattended=True, exec_mode=rx.MODE_EXEC_FILE)
        for entry in result.get("output", []):
            stream = sys.stderr if entry.get("type") in ("Warning", "Error") else sys.stdout
            print(entry.get("output", "").rstrip("\n"), file=stream)
        if not result.get("success"):
            print(result.get("result", ""), file=sys.stderr)
            return 1
        return 0
    finally:
        remote.stop()


if __name__ == "__main__":
    sys.exit(main())
