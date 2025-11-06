#!/usr/bin/env python3
"""
aircast-server.py — AirCast: Stream PC system audio to browsers over LAN.

Author: Utkarsh (https://github.com/utkarsh-deployes)
Purpose:
    Capture Windows system audio (via WASAPI loopback or Stereo Mix fallback)
    and broadcast PCM frames to connected browser clients over WebSocket,
    while serving a minimal HTML5 player UI via Flask.

Usage:
    python aircast-server.py
    python aircast-server.py --http 8080 --ws 9000 --device 2 --rate 48000 --block 2048
"""

from __future__ import annotations
import argparse
import asyncio
import socket
import sys
import signal
from threading import Thread
from typing import Optional, Set

from flask import Flask, send_from_directory
import sounddevice as sd
import numpy as np
import websockets

# ------------------ Defaults ------------------
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 2
DEFAULT_BLOCK = 1024
DEFAULT_HTTP_PORT = 5000
DEFAULT_WS_PORT = 8765

# ------------------ Flask UI ------------------
app = Flask(__name__)

@app.route("/")
def index():
    """Serve the AirCast client page."""
    return send_from_directory(".", "aircast-client.html")

def start_http_server(host: str, port: int = DEFAULT_HTTP_PORT):
    """Run Flask UI server in a separate thread."""
    print(f"[HTTP] Web UI available at: http://{host}:{port}")
    app.run(host="0.0.0.0", port=port, threaded=True)

# ------------------ Utilities ------------------
def get_local_ip() -> str:
    """Get LAN IP address or 127.0.0.1 if unavailable."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def list_devices() -> list:
    """List and return all available audio devices."""
    try:
        devices = sd.query_devices()
        print("\n--- Available Audio Devices ---")
        for i, d in enumerate(devices):
            print(f"{i:3}: {d['name']} | Out: {d['max_output_channels']:2} | In: {d['max_input_channels']:2}")
        print("--- end devices ---\n")
        return devices
    except Exception as e:
        print(f"[AUDIO] Failed to query devices: {e}")
        return []

# ------------------ Audio Capture ------------------
def open_wasapi_loopback(device_idx: int, samplerate: int, channels: int, blocksize: int):
    """Attempt to open WASAPI loopback stream."""
    try:
        settings = sd.WasapiSettings(loopback=True)
        stream = sd.InputStream(
            device=device_idx,
            samplerate=samplerate,
            channels=channels,
            blocksize=blocksize,
            dtype="int16",
            extra_settings=settings,
        )
        stream.start()
        print(f"[AUDIO] WASAPI loopback started (device={device_idx})")
        return stream
    except Exception as e:
        print(f"[AUDIO] WASAPI loopback failed: {e}")
        return None

def open_standard_input(device_idx: int, samplerate: int, channels: int, blocksize: int):
    """Fallback: Open normal input stream (Stereo Mix / Microphone)."""
    try:
        stream = sd.InputStream(
            device=device_idx,
            samplerate=samplerate,
            channels=channels,
            blocksize=blocksize,
            dtype="int16",
        )
        stream.start()
        print(f"[AUDIO] Standard input stream started (device={device_idx})")
        return stream
    except Exception as e:
        print(f"[AUDIO] Input stream failed: {e}")
        return None

# ------------------ WebSocket Handling ------------------
clients: Set[websockets.WebSocketServerProtocol] = set()
audio_stream: Optional[sd.InputStream] = None

async def broadcast_audio(blocksize: int, samplerate: int, channels: int):
    """Continuously capture PCM audio and send to connected clients."""
    global audio_stream, clients
    if audio_stream is None:
        print("[WS] No audio stream — cannot broadcast.")
        return

    print(f"[WS] Broadcasting audio (rate={samplerate}, channels={channels}, block={blocksize})")
    try:
        while True:
            data, overflow = audio_stream.read(blocksize)
            if overflow:
                print("[AUDIO] Buffer overflow — some frames dropped")

            try:
                raw = data.tobytes()
            except Exception as e:
                print(f"[AUDIO] Conversion error: {e}")
                continue

            # Send to all clients
            disconnected = []
            for ws in clients.copy():
                try:
                    await ws.send(raw)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                clients.discard(ws)

            await asyncio.sleep(0)
    except asyncio.CancelledError:
        print("[WS] Broadcast stopped.")
    except Exception as e:
        print(f"[WS] Broadcast error: {e}")

async def ws_handler(websocket):
    """Manage a single websocket client connection."""
    global clients
    clients.add(websocket)
    addr = websocket.remote_address
    print(f"[WS] Client connected: {addr} (total={len(clients)})")

    try:
        await websocket.wait_closed()
    finally:
        clients.discard(websocket)
        print(f"[WS] Client disconnected: {addr} (total={len(clients)})")

async def start_ws_server(host: str, ws_port: int, blocksize: int, samplerate: int, channels: int):
    """Start the WebSocket server and audio broadcast task."""
    print(f"[WS] Listening on ws://{host}:{ws_port}")
    async with websockets.serve(ws_handler, "0.0.0.0", ws_port, max_size=None):
        task = asyncio.create_task(broadcast_audio(blocksize, samplerate, channels))
        try:
            await asyncio.Future()  # run indefinitely
        except asyncio.CancelledError:
            pass
        finally:
            task.cancel()

# ------------------ Main Entry ------------------
def main():
    global audio_stream

    parser = argparse.ArgumentParser(description="AirCast — Stream PC audio to browsers over LAN")
    parser.add_argument("--http", type=int, default=DEFAULT_HTTP_PORT, help="HTTP UI port (default 5000)")
    parser.add_argument("--ws", type=int, default=DEFAULT_WS_PORT, help="WebSocket port (default 8765)")
    parser.add_argument("--device", type=int, default=None, help="Audio device index to use")
    parser.add_argument("--rate", type=int, default=DEFAULT_SAMPLE_RATE, help="Sample rate (default 44100)")
    parser.add_argument("--block", type=int, default=DEFAULT_BLOCK, help="Audio block size (default 1024)")
    parser.add_argument("--channels", type=int, default=DEFAULT_CHANNELS, help="Channels (default 2)")
    args = parser.parse_args()

    print("=== AirCast Server — by Utkarsh ===")
    print(f"[CONFIG] HTTP={args.http}, WS={args.ws}, Rate={args.rate}, Block={args.block}, Channels={args.channels}")

    devices = list_devices()
    if not devices:
        print("[AUDIO] No devices found — exiting.")
        sys.exit(1)

    # Pick device(s)
    if args.device is not None:
        candidates = [args.device]
    else:
        candidates = [i for i, d in enumerate(devices) if d["max_output_channels"] > 0]
        candidates += [i for i, d in enumerate(devices) if "stereo" in d["name"].lower()]

    # Try WASAPI or fallback
    for idx in candidates:
        stream = open_wasapi_loopback(idx, args.rate, args.channels, args.block)
        if stream:
            audio_stream = stream
            mode = "WASAPI Loopback"
            chosen = idx
            break
        stream = open_standard_input(idx, args.rate, args.channels, args.block)
        if stream:
            audio_stream = stream
            mode = "Input Stream"
            chosen = idx
            break
    else:
        print("[AUDIO] Could not open any capture device. Please enable Stereo Mix or WASAPI loopback.")
        sys.exit(1)

    print(f"[AUDIO] Using device #{chosen}: {devices[chosen]['name']} ({mode})")

    host_ip = get_local_ip()
    http_thread = Thread(target=start_http_server, args=(host_ip, args.http), daemon=True)
    http_thread.start()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown_handler(sig, frame):
        print("\n[MAIN] Shutting down...")
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.stop()

    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        loop.run_until_complete(start_ws_server(host_ip, args.ws, args.block, args.rate, args.channels))
    except KeyboardInterrupt:
        pass
    finally:
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
        print("[MAIN] AirCast stopped cleanly.")

if __name__ == "__main__":
    main()
