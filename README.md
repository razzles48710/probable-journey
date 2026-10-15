# The Beshara Enchanted Mirror

A Snow White inspired talking mirror: a luminous animated face on black, an antique gold oval, local Ollama conversation, optional local Piper speech, and a Chromium kiosk interface. Original implementation; not a fork of an unidentified Mirror Me project. No paid AI API key and no frontend build step.

## Start here

1. Install Python 3.10+ and [Ollama](https://ollama.com/download) on your mirror computer. Ensure Ollama is running (use `ollama serve` if needed).
2. In a terminal: `ollama pull llama3.2:3b`.
3. From this repository: `python3 server.py` (Windows: `py server.py`).
4. Open **http://localhost:8080** in Chromium/Chrome. Type a question and press Ask. Use Fullscreen to hide the browser frame.

The face moves while audio plays; mouth movement is a stylized speaking animation, not phoneme-accurate lip sync. Conversation stays in page memory and clears on reload or New conversation. The app has no camera, facial recognition, always-listening wake word, or smart-home actions.

## Voice

Browser speech output works without Piper when a voice is installed. Browser microphone input is optional, depends on recognition support, and may send audio to the browser vendor's service; it is not offline speech recognition. Type for a fully local conversation path. Linux Chromium often lacks speech recognition. No microphone permission is needed for typing.

For local neural speech, create a Python virtual environment, activate it, then install `piper-tts` from [Piper](https://github.com/OHF-Voice/piper1-gpl). Download a compatible `.onnx` voice and its matching `.onnx.json` configuration (review the voice's license). Set `PIPER_MODEL` to the absolute `.onnx` path before starting the server. Example on Linux:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install piper-tts
export PIPER_MODEL="$PWD/voices/en_US-lessac-medium.onnx"
python server.py
```

Put the downloaded voice files in `voices/` first; they are not bundled. Optional `PIPER_BIN` selects the executable. If Piper fails, the page tries the browser voice. First interact with the page so the browser permits audio. Speakers and installed voices must work on the mirror computer.

## Raspberry Pi and another Ollama computer

A Pi can display the face while a stronger computer runs Ollama. Set `OLLAMA_URL=http://YOUR-OLLAMA-COMPUTER:11434` on the Pi and run `python3 server.py`. The Ollama computer must be configured to accept connections from the Pi; keep that service on a trusted private network and restrict access with its firewall. Do not expose it to the internet. The mirror web server itself binds only to loopback.

Optional environment variables: `OLLAMA_MODEL` (default `llama3.2:3b`), `OLLAMA_URL`, `PIPER_MODEL`, `PIPER_BIN`, and `PORT` (default 8080). On PowerShell use `$env:OLLAMA_MODEL="llama3.2:3b"`. Choose a smaller installed model if your device is slow. Actual latency depends on hardware; a Pi is not guaranteed to answer quickly.

After starting the server, launch Chromium with:

```sh
chromium --kiosk http://localhost:8080
```

The executable may be named `chromium-browser` on some installations. Exit with Alt+F4. To start at login, add the server and the kiosk command to your desktop's startup settings. Keep the display well ventilated behind the frame.

## Physical mirror

Use a monitor, speakers, optional USB microphone, a frame, and suitable two-way mirror acrylic/glass. Show the face on a black background behind the mirror; brightness, room lighting and mirror transmission determine visibility. Start by testing on a bare monitor. This is a software prototype, not a supplied hardware kit.

## Verify

`python3 -m unittest discover -s tests -v`

Tests use a fake local Ollama endpoint to check the real HTTP request/response path, validation, and unavailable-service handling. Live Ollama, Piper, microphone, audio and Pi hardware require testing on your device.

## Sources and alternatives

- [Ollama API](https://docs.ollama.com/api): this project calls `/api/chat` with `stream: false`.
- [Piper](https://github.com/OHF-Voice/piper1-gpl): optional speech engine, installed separately under its own license.
- [MagicMirror²](https://github.com/MagicMirrorOrg/MagicMirror): an alternative modular dashboard platform; not required or bundled here.

This project draws no code or assets from those repositories. The face is an original SVG illustration. If you meant a particular Mirror Me repository, its renderer can be evaluated separately once its exact URL and license are known.
