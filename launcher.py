#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
import os

CRM_PORT = 8000
MCP_PORT = 8765

processes = []


def kill_all():
    print("\nShutting down...")
    for proc in processes:
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
    time.sleep(1)
    for proc in processes:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
    for proc in processes:
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        except ProcessLookupError:
            pass
    print("Stopped.")


def signal_handler(sig, frame):
    kill_all()
    sys.exit(0)


def wait_for_server(url: str, name: str, timeout: int = 30):
    import httpx
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = httpx.get(url, timeout=5.0)
            if resp.status_code < 500:
                print(f"{name} is ready at {url}")
                return True
        except:
            pass
        time.sleep(0.5)
    print(f"Warning: {name} not responding at {url}")
    return False


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 50)
    print("CRM Emulator + MCP Server Launcher")
    print("=" * 50)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    print("\n[1/2] Starting CRM API...")
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(CRM_PORT)],
        cwd=base_dir,
    )
    processes.append(api_proc)

    api_ready = wait_for_server(f"http://localhost:{CRM_PORT}/", "CRM API")
    if not api_ready:
        print("CRM API failed to start, continuing anyway...")

    print("\n[2/2] Starting MCP Server...")
    mcp_proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        cwd=base_dir,
    )
    processes.append(mcp_proc)

    mcp_ready = wait_for_server(f"http://localhost:{MCP_PORT}/", "MCP Server")
    if not mcp_ready:
        print("MCP Server failed to start, continuing anyway...")

    print("\n" + "=" * 50)
    print("Services:")
    print(f"  CRM API:      http://localhost:{CRM_PORT}")
    print(f"  MCP Server:   http://localhost:{MCP_PORT}")
    print(f"  API Docs:    http://localhost:{CRM_PORT}/docs")
    print("=" * 50)
    print("\nPress Ctrl+C to stop all services\n")

    try:
        while True:
            time.sleep(1)
            for proc in processes:
                if proc.poll() is not None:
                    print(f"Warning: a process died unexpectedly")
                    kill_all()
                    return
    except KeyboardInterrupt:
        kill_all()
        return


if __name__ == "__main__":
    main()