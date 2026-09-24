import asyncio
import aiohttp
import ssl
import json
import uuid
from datetime import datetime

WSS_URL = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
HEADERS = {
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
}

formats_to_test = [
    "audio-24khz-48kbitrate-mono-mp3",
    "audio-24khz-96kbitrate-mono-mp3",
    "audio-24khz-160kbitrate-mono-mp3",
    "audio-48khz-96kbitrate-mono-mp3",
    "audio-48khz-192kbitrate-mono-mp3",
    "riff-24khz-16bit-mono-pcm",
    "riff-48khz-16bit-mono-pcm"
]

async def test_format(fmt):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        conn_id = uuid.uuid4().hex
        url = f"{WSS_URL}&ConnectionId={conn_id}"
        async with session.ws_connect(url, ssl=ssl_ctx) as ws:
            # 1. Send speech.config
            cfg = (
                "Content-Type:application/json; charset=utf-8\r\n"
                "Path:speech.config\r\n\r\n"
                '{"context":{"synthesis":{"audio":{"metadataoptions":{'
                '"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"'
                '},'
                f'"outputFormat":"{fmt}"'
                "}}}}\r\n"
            )
            await ws.send_str(cfg)

            # 2. Send SSML
            req_id = uuid.uuid4().hex
            timestamp = datetime.utcnow().strftime("%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)")
            ssml = (
                f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='km-KH'>"
                f"<voice name='km-KH-PisethNeural'>"
                f"<prosody rate='+0%' pitch='+0Hz'>សួស្តី និងសូមស្វាគមន៍មកកាន់ SN TOOL</prosody>"
                f"</voice></speak>"
            )
            msg = (
                f"X-RequestId:{req_id}\r\n"
                f"Content-Type:application/ssml+xml\r\n"
                f"X-Timestamp:{timestamp}Z\r\n"
                f"Path:ssml\r\n\r\n"
                f"{ssml}"
            )
            await ws.send_str(msg)

            total_audio = 0
            while True:
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.BINARY:
                    data = msg.data
                    # Find path:audio\r\n
                    idx = data.find(b"Path:audio\r\n")
                    if idx != -1:
                        hdr_end = data.find(b"\r\n\r\n", idx)
                        if hdr_end != -1:
                            audio_chunk = data[hdr_end + 4:]
                            total_audio += len(audio_chunk)
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    if "turn.end" in msg.data:
                        break
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
            print(f"Format: {fmt:<35} -> Received {total_audio} audio bytes")
            return total_audio

async def main():
    for f in formats_to_test:
        try:
            await test_format(f)
        except Exception as e:
            print(f"Format: {f:<35} -> ERROR: {e}")

asyncio.run(main())
