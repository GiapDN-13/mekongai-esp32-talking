"""
Voiceprint Registration & Test Script
========================================
Script to register speakers from WAV files and test identification.

Usage:
  # Register a speaker
  python register_speaker.py register --id test1 --name "Minh" --audio path/to/minh.wav

  # Identify who is speaking
  python register_speaker.py identify --audio path/to/unknown.wav --candidates test1,test2,test3

  # List all registered speakers
  python register_speaker.py list

  # Delete a speaker
  python register_speaker.py delete --id test1

  # Record from microphone and register (requires sounddevice)
  python register_speaker.py record --id test1 --name "Minh" --duration 10
"""

import os
import sys
import argparse
import requests

API_URL = os.getenv("VOICEPRINT_URL", "http://localhost:8100")
API_KEY = os.getenv("VOICEPRINT_API_KEY", "voiceprint-secret-key")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def health_check():
    """Check if the voiceprint service is running."""
    try:
        r = requests.get(f"{API_URL}/voiceprint/health", params={"key": API_KEY}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"[OK] Service healthy")
            print(f"  Encoder loaded: {data.get('encoder_loaded', False)}")
            print(f"  Speakers registered: {data.get('speakers_registered', 0)}")
            return True
        else:
            print(f"[FAIL] Status {r.status_code}: {r.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Cannot connect to {API_URL}")
        print("  Start the service: cd main/voiceprint-service && python app.py")
        return False


def register_speaker(speaker_id: str, audio_path: str):
    """Register a speaker from a WAV file."""
    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio file not found: {audio_path}")
        return False

    with open(audio_path, "rb") as f:
        files = {"file": ("audio.wav", f, "audio/wav")}
        data = {"speaker_id": speaker_id}
        r = requests.post(
            f"{API_URL}/voiceprint/register",
            headers=HEADERS,
            files=files,
            data=data,
            timeout=30,
        )

    if r.status_code == 200:
        result = r.json()
        print(f"[OK] {result.get('message', 'Registered')}")
        return True
    else:
        print(f"[FAIL] Status {r.status_code}: {r.text}")
        return False


def identify_speaker(audio_path: str, candidate_ids: str):
    """Identify who is speaking from an audio file."""
    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio file not found: {audio_path}")
        return

    with open(audio_path, "rb") as f:
        files = {"file": ("audio.wav", f, "audio/wav")}
        data = {"speaker_ids": candidate_ids}
        r = requests.post(
            f"{API_URL}/voiceprint/identify",
            headers=HEADERS,
            files=files,
            data=data,
            timeout=30,
        )

    if r.status_code == 200:
        result = r.json()
        print(f"[RESULT] Best match: {result.get('speaker_id')} (score: {result.get('score', 0):.4f})")
        scores = result.get("all_scores", {})
        if scores:
            print("  All scores:")
            for sid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 40)
                print(f"    {sid}: {score:.4f} {bar}")
    else:
        print(f"[FAIL] Status {r.status_code}: {r.text}")


def list_speakers():
    """List all registered speakers."""
    r = requests.get(
        f"{API_URL}/voiceprint/list",
        headers=HEADERS,
        timeout=10,
    )
    if r.status_code == 200:
        result = r.json()
        speakers = result.get("speakers", [])
        print(f"Total registered speakers: {result.get('total', 0)}")
        for s in speakers:
            print(f"  - {s['speaker_id']} (dim={s.get('embedding_dim', '?')}, registered: {s.get('registered_at', '?')})")
    else:
        print(f"[FAIL] Status {r.status_code}: {r.text}")


def delete_speaker(speaker_id: str):
    """Delete a speaker registration."""
    r = requests.delete(
        f"{API_URL}/voiceprint/{speaker_id}",
        headers=HEADERS,
        timeout=10,
    )
    if r.status_code == 200:
        result = r.json()
        print(f"[OK] {result.get('message', 'Deleted')}")
    else:
        print(f"[FAIL] Status {r.status_code}: {r.text}")


def record_and_register(speaker_id: str, duration: int = 10):
    """Record from microphone and register speaker."""
    try:
        import sounddevice as sd
        import soundfile as sf_lib
        import tempfile
    except ImportError:
        print("[ERROR] Install sounddevice: pip install sounddevice soundfile")
        return

    sample_rate = 16000
    print(f"Recording {duration}s from microphone... Speak now!")
    print("=" * 40)

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()

    print("Recording finished!")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf_lib.write(tmp.name, audio, sample_rate)
    tmp.close()

    register_speaker(speaker_id, tmp.name)
    os.unlink(tmp.name)


def main():
    parser = argparse.ArgumentParser(description="Voiceprint Registration & Test Tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check service health")

    reg = sub.add_parser("register", help="Register a speaker")
    reg.add_argument("--id", required=True, help="Speaker ID")
    reg.add_argument("--audio", required=True, help="Path to WAV audio file")

    ident = sub.add_parser("identify", help="Identify who is speaking")
    ident.add_argument("--audio", required=True, help="Path to WAV audio file")
    ident.add_argument("--candidates", required=True, help="Comma-separated speaker IDs")

    sub.add_parser("list", help="List all registered speakers")

    dl = sub.add_parser("delete", help="Delete a speaker")
    dl.add_argument("--id", required=True, help="Speaker ID to delete")

    rec = sub.add_parser("record", help="Record from microphone and register")
    rec.add_argument("--id", required=True, help="Speaker ID")
    rec.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command != "health" and not health_check():
        print("\nService is not available. Please start it first.")
        return

    if args.command == "health":
        health_check()
    elif args.command == "register":
        register_speaker(args.id, args.audio)
    elif args.command == "identify":
        identify_speaker(args.audio, args.candidates)
    elif args.command == "list":
        list_speakers()
    elif args.command == "delete":
        delete_speaker(args.id)
    elif args.command == "record":
        record_and_register(args.id, args.duration)


if __name__ == "__main__":
    main()
