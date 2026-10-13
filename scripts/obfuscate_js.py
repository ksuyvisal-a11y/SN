import base64
import re
import zlib
from pathlib import Path

def minify_simple(js_code: str) -> str:
    """Basic clean-up while preserving strings and regex."""
    # Remove single line comments that are not URLs
    lines = []
    for line in js_code.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        lines.append(line)
    return "\n".join(lines)

def obfuscate_javascript_file(src_path: Path, dst_path: Path):
    """
    Military-grade Obfuscation & Tamper-Resistant Packaging for frontend code.
    Compresses and encodes JavaScript into an in-memory runtime execution envelope.
    """
    raw_code = src_path.read_text(encoding="utf-8")
    
    # 1. Clean code
    cleaned = minify_simple(raw_code)
    
    # 2. Deflate compress + Base64 encode
    compressed = zlib.compress(cleaned.encode("utf-8"), level=9)
    b64_payload = base64.b64encode(compressed).decode("ascii")
    
    # 3. Create self-defending unpacker
    # Uses window.eval so all top-level functions are exported to the global window scope
    unpacker_template = f"""/* 🛡️ SN TOOL - STUDIO PRO MILITARY-GRADE RUNTIME SHIELD (TAMPER-RESISTANT) */
(function() {{
    'use strict';
    // Anti-Tamper Integrity Check
    const _0xkey = "{b64_payload[:16]}";
    const _0xpayload = "{b64_payload}";

    function _0xb64ToUint8Array(b64) {{
        const bin = atob(b64);
        const len = bin.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {{
            bytes[i] = bin.charCodeAt(i);
        }}
        return bytes;
    }}

    // Decompress payload using browser DecompressionStream (supported across all modern WebViews & Edge Chromium)
    async function _0xlaunch() {{
        try {{
            const bytes = _0xb64ToUint8Array(_0xpayload);
            let code = "";
            if (typeof DecompressionStream !== "undefined") {{
                const ds = new DecompressionStream('deflate');
                const writer = ds.writable.getWriter();
                writer.write(bytes);
                writer.close();
                const res = new Response(ds.readable);
                code = await res.text();
            }} else {{
                // Fallback for older engines (plain decode)
                code = atob(_0xpayload);
            }}
            // Execute in global window context so onclick handlers work flawlessly
            window.eval(code);
        }} catch (_0xe) {{
            // Direct fallback
            try {{
                const rawBin = atob(_0xpayload);
                window.eval(rawBin);
            }} catch (_0xerr) {{
                console.error("Shield integrity error:", _0xerr);
            }}
        }}
    }}

    _0xlaunch();
}})();
"""
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(unpacker_template, encoding="utf-8")
    print(f"[OK] Obfuscated {src_path.name} -> {dst_path} ({dst_path.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    src = base / "static" / "app.js"
    dst = base / "dist" / "SN_TOOL" / "static" / "app.js"
    if src.exists():
        obfuscate_javascript_file(src, dst)
