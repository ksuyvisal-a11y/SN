# -*- coding: utf-8 -*-
"""
Script to translate backend strings in license_engine.py, desktop_app.py, run_studio.py, server.py, batch_engine.py, ADMIN_KEY_GENERATOR.py
"""
from pathlib import Path

def translate_license_engine():
    p = Path('license_engine.py')
    content = p.read_text(encoding='utf-8')
    replacements = [
        ('return False, "❌ License Key នេះត្រូវបាន Admin ផ្អាកការប្រើប្រាស់ (Revoked/Suspended)", {}', 'return False, "❌ This License Key has been suspended/revoked by Admin", {}'),
        ('return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}', 'return False, "❌ This License Key is locked to a different machine (HWID mismatch)", {}'),
        ("return False, f\"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({record.get('expires_at')})\", {}", "return False, f\"⚠️ This License Key has expired ({record.get('expires_at')})\", {}"),
        ('return True, f"✅ License Key {status_tag} ត្រឹមត្រូវ និងសកម្ម!", record', 'return True, f"✅ License Key {status_tag} is valid and active!", record'),
        ('return False, "សូមបញ្ចូល Key ដែលត្រូវ Revoke"', 'return False, "Please enter Key to revoke"'),
        ('return True, f"🚫 បាន Revoke / Ban Key {cleaned} ជោគជ័យ!"', 'return True, f"🚫 Successfully revoked Key {cleaned}!"'),
        ('return True, f"✅ បានដោះសោ (Unban) Key {cleaned} ឱ្យដំណើរការឡើងវិញជោគជ័យ!"', 'return True, f"✅ Successfully unbanned Key {cleaned}!"'),
        ('return False, "សូមជ្រើសរើស Key ដែលត្រូវលុប"', 'return False, "Please select Key to delete"'),
        ('return True, f"🗑️ បានលុប Key {cleaned} ចេញពីបញ្ជីជោគជ័យ!"', 'return True, f"🗑️ Successfully deleted Key {cleaned}!"'),
        ('return True, "✅ បានជម្រះបញ្ជីឈ្មោះ Customer និង Keys ទាំងអស់ជោគជ័យ! បញ្ជី Key ឥឡូវនៅសល់ 0 ត្រៀមសម្រាប់ដាក់លក់ជូន User ថ្មី។"', 'return True, "✅ Cleared all customer and key records successfully!"'),
        ('return "❌ License Key នេះត្រូវបាន Admin បញ្ឈប់ពីចម្ងាយ (Remote Revoked by Admin)"', 'return "❌ License Key remotely revoked by Admin"'),
        ('return "❌ ម៉ាស៊ីននេះត្រូវបាន Admin បញ្ឈប់ពីចម្ងាយ (Device Banned by Admin)"', 'return "❌ Device remotely banned by Admin"'),
        ('rec["status_kh"] = "🚫 បានផ្អាក (Revoked)"', 'rec["status_kh"] = "🚫 Revoked"'),
        ('rec["remaining_text"] = "ត្រូវបានផ្អាកដោយ Admin"', 'rec["remaining_text"] = "Suspended by Admin"'),
        ('rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "មិនទាន់ចូលប្រើ"', 'rec["last_active"] = rec.get("last_active") or rec.get("activated_at") or "Never"'),
        ('rec["status_kh"] = "👑 មួយជីវិត (Lifetime)"', 'rec["status_kh"] = "👑 Lifetime"'),
        ('rec["remaining_text"] = "ប្រើប្រាស់បានរហូត (Lifetime)"', 'rec["remaining_text"] = "Lifetime (Permanent)"'),
        ('rec["status_kh"] = "🟢 សកម្ម (Active)"', 'rec["status_kh"] = "🟢 Active"'),
        ('rec["status_kh"] = f"🔴 ផុតកំណត់ ({abs(days_left)} ថ្ងៃមុន)"', 'rec["status_kh"] = f"🔴 Expired ({abs(days_left)} days ago)"'),
        ('rec["remaining_text"] = f"ផុតកំណត់កាលពី {abs(days_left)} ថ្ងៃមុន"', 'rec["remaining_text"] = f"Expired {abs(days_left)} days ago"'),
        ('rec["status_kh"] = f"⚠️ ជិតផុតកំណត់ (សល់ {days_left} ថ្ងៃ)"', 'rec["status_kh"] = f"⚠️ Expiring Soon ({days_left} days left)"'),
        ('rec["remaining_text"] = f"នៅសល់ {days_left} ថ្ងៃទៀតផុតកំណត់"', 'rec["remaining_text"] = f"{days_left} days remaining"'),
        ('rec["status_kh"] = f"🟢 សកម្ម (សល់ {days_left} ថ្ងៃ)"', 'rec["status_kh"] = f"🟢 Active ({days_left} days left)"'),
        ('rec["remaining_text"] = f"នៅសល់ {days_left} ថ្ងៃ"', 'rec["remaining_text"] = f"{days_left} days remaining"'),
        ('return False, "សូមបញ្ចូល License Key", {}', 'return False, "Please enter License Key", {}'),
        ('return False, "❌ License Key នេះត្រូវបាន Admin បញ្ឈប់/ផ្អាកការប្រើប្រាស់ (Revoked/Suspended by Admin)", {}', 'return False, "❌ This License Key has been suspended/revoked by Admin", {}'),
        ('return True, "✅ License Key ត្រឹមត្រូវ!", {', 'return True, "✅ Valid License Key!", {'),
        ('return False, "❌ Custom Key នេះត្រូវបានផ្អាកដោយ Admin", {}', 'return False, "❌ This Custom Key has been suspended by Admin", {}'),
        ('return False, "❌ Custom Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}', 'return False, "❌ This Custom Key is locked to a different machine (HWID mismatch)", {}'),
        ("return False, f\"⚠️ Custom Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({rec.get('expires_at')})\", {}", "return False, f\"⚠️ This Custom Key has expired ({rec.get('expires_at')})\", {}"),
        ('return True, "✅ Custom Key ផ្ទាល់ខ្លួនត្រឹមត្រូវ និងសកម្ម!", rec', 'return True, "✅ Custom Key is valid and active!", rec'),
        ('return False, "❌ License Key នេះត្រូវបានផ្អាកដោយ Admin", {}', 'return False, "❌ This License Key has been suspended by Admin", {}'),
        ('return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}', 'return False, "❌ This License Key is locked to a different machine (HWID mismatch)", {}'),
        ("return False, f\"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({record.get('expires_at')})\", {}", "return False, f\"⚠️ This License Key has expired ({record.get('expires_at')})\", {}"),
        ('return True, "✅ License Key ត្រឹមត្រូវ និងសកម្ម!", record', 'return True, "✅ License Key is valid and active!", record'),
        ('elif online_msg and ("ផ្អាក" in online_msg or "ផុតកំណត់" in online_msg or "HWID" in online_msg):', 'elif online_msg and ("suspended" in online_msg.lower() or "revoked" in online_msg.lower() or "expired" in online_msg.lower() or "hwid" in online_msg.lower() or "ផ្អាក" in online_msg or "ផុតកំណត់" in online_msg or "HWID" in online_msg):'),
        ('return False, "❌ License Key មិនត្រឹមត្រូវ (Invalid Signature)", {}', 'return False, "❌ Invalid License Key (Invalid Signature)", {}'),
        ('return False, f"⚠️ License Key នេះបានផុតកំណត់កាលបរិច្ឆេទហើយ ({expiry_str})", {}', 'return False, f"⚠️ This License Key has expired ({expiry_str})", {}'),
        ('return False, "❌ ទម្រង់ Expiry នៃ License Key មិនត្រឹមត្រូវ", {}', 'return False, "❌ Invalid License Key Expiry format", {}'),
        ('return False, "❌ License Key នេះត្រូវបានចាក់សោសម្រាប់តែម៉ាស៊ីនមួយផ្សេងទៀតប៉ុណ្ណោះ (HWID មិនត្រឹមត្រូវ)", {}', 'return False, "❌ This License Key is locked to a different machine (HWID mismatch)", {}'),
        ('return True, "✅ License Key ត្រឹមត្រូវ និងសកម្ម!", {', 'return True, "✅ License Key is valid and active!", {'),
        ('return False, "❌ License Key មិនត្រឹមត្រូវ សូមទាក់ទង Admin ដើម្បីទទួលយក Key", {}', 'return False, "❌ Invalid License Key. Please contact Admin to get a valid key.", {}'),
        ('return True, f"🎉 បាន Activate License Key ជោគជ័យ! ស្វាគមន៍ {final_client_name}!", data_to_save', 'return True, f"🎉 License Key activated successfully! Welcome {final_client_name}!", data_to_save'),
        ('"message": "License Gate ត្រូវបានបិទ (បើកដំណើរការដោយសេរី Free 100%)"', '"message": "License Gate is disabled (Free Mode)"'),
        ('"message": "សូមបញ្ចូល License Key ដើម្បីបើកដំណើរការ Tool",', '"message": "Please enter License Key to activate tool",'),
        ('"message": "License Key File ត្រូវបានកែបន្លំ",', '"message": "License Key file has been tampered with",'),
        ('"message": "សូមបញ្ចូល License Key ដើម្បីបើកដំណើរការ Tool (Machine Mismatch)",', '"message": "Please enter License Key to activate tool (Machine Mismatch)",'),
        ('"message": "❌ License Key នេះត្រូវបាន Admin ផ្អាកការប្រើប្រាស់",', '"message": "❌ This License Key has been suspended by Admin",'),
        ("f\"⚠️ License Key របស់អ្នកបានផុតកំណត់កាលពី {abs(live.get('days_remaining', 0))} ថ្ងៃមុន សូមទាក់ទង Admin ដើម្បីបន្តសុពលភាព\"", "f\"⚠️ Your License Key expired {abs(live.get('days_remaining', 0))} days ago. Please contact Admin to renew.\""),
        ('"status_kh": live.get("status_kh", "សកម្ម"),', '"status_kh": live.get("status_kh", "Active"),'),
        ('"message": "License សកម្ម ១០០%"', '"message": "License is 100% active"'),
    ]
    for src, dst in replacements:
        content = content.replace(src, dst)
    p.write_text(content, encoding='utf-8')
    print("Updated license_engine.py")

def translate_desktop_and_run():
    # desktop_app.py
    p1 = Path('desktop_app.py')
    c1 = p1.read_text(encoding='utf-8')
    c1 = c1.replace('print(" ✅ SN TOOL កំពុងដំណើរការស្រេចនៅលើកុំព្យូទ័ររបស់អ្នករួចរាល់ហើយ!")', 'print(" ✅ SN TOOL is already running on your computer!")')
    c1 = c1.replace('print(" 🖥️ កំពុងនាំផ្ទាំងកម្មវិធី Desktop មកមុខអេក្រង់...")', 'print(" 🖥️ Bringing Desktop application window to foreground...")')
    c1 = c1.replace('print("[INFO] រកឃើញ Server ចាស់គ្មានផ្ទាំង (Orphan Process) កំពុងបោសសម្អាតដើម្បីបើក Native Desktop Window ថ្មី...")', 'print("[INFO] Detected orphaned server process. Cleaning up to launch new Native Desktop window...")')
    c1 = c1.replace('"SN TOOL ត្រូវការ Microsoft Edge WebView2 ដើម្បីដំណើរការជាកម្មវិធី Desktop Native។\nសូមដំឡើង Microsoft Edge WebView2 រួចបើកកម្មវិធីម្តងទៀត។"', '"SN TOOL requires Microsoft Edge WebView2 to run as a Native Desktop app.\nPlease install Microsoft Edge WebView2 and reopen the application."')
    c1 = c1.replace('print(" 🎬 កំពុងចាប់ផ្តើម SN TOOL - STUDIO PRO (Native Desktop App)...")', 'print(" 🎬 Starting SN TOOL - STUDIO PRO (Native Desktop App)...")')
    c1 = c1.replace('print(" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")', 'print(" 🎙️ Official Voiceover Models: Piseth (Male Solo) & Sreymom (Female Solo)")')
    p1.write_text(c1, encoding='utf-8')
    print("Updated desktop_app.py")

    # run_studio.py
    p2 = Path('run_studio.py')
    c2 = p2.read_text(encoding='utf-8')
    c2 = c2.replace('print(" 🎬 កំពុងដំណើរការ SN TOOL - STUDIO PRO (Native Desktop App)...")', 'print(" 🎬 Starting SN TOOL - STUDIO PRO (Native Desktop App)...")')
    c2 = c2.replace('print(" 🎙️ សំឡេងខ្មែរផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)")', 'print(" 🎙️ Official Voiceover Models: Piseth (Male Solo) & Sreymom (Female Solo)")')
    c2 = c2.replace('print("\n[INFO] កម្មវិធីកំពុងដំណើរការ! (ចុច Ctrl+C ដើម្បីបិទកម្មវិធី)\n")', 'print("\n[INFO] Application is running! (Press Ctrl+C to stop)\n")')
    c2 = c2.replace('print("\nកំពុងបិទកម្មវិធី...")', 'print("\nStopping application...")')
    p2.write_text(c2, encoding='utf-8')
    print("Updated run_studio.py")

def translate_server_py():
    p = Path('server.py')
    c = p.read_text(encoding='utf-8')
    c = c.replace('"message": "ប្រតិបត្តិការមានបញ្ហាបច្ចេកទេសបណ្តោះអាសន្ន ប៉ុន្តែកម្មវិធីនៅតែដំណើរការធម្មតា"', '"message": "Technical issue occurred, but system continues running normally"')
    c = c.replace('text = data.get("text", "សួស្តី")', 'text = data.get("text", "Hello")')
    c = c.replace('return jsonify({"success": False, "error": "សូមបញ្ចូល License Key", "message": "សូមបញ្ចូល License Key"}), 400', 'return jsonify({"success": False, "error": "Please enter License Key", "message": "Please enter License Key"}), 400')
    c = c.replace('"message": f"មិនទាន់មានវីដេអូសម្រាប់ភាគ {ep_num} នៅលើកុំព្យូទ័រទេ",', '"message": f"Episode {ep_num} is not downloaded locally yet",')
    c = c.replace('title="ជ្រើសរើស Folder រឿងភាគដែលបានទាញយក (Select Downloaded Drama Folder)"', 'title="Select Downloaded Drama Folder"')
    c = c.replace('return jsonify({"success": False, "cancelled": True, "message": "បានបោះបង់ការជ្រើសរើស Folder"})', 'return jsonify({"success": False, "cancelled": True, "message": "Folder selection cancelled"})')
    c = c.replace('"step_km": "កំពុងរៀបចំប្រព័ន្ធកែច្នៃ...",', '"step_km": "Initializing pipeline...",')
    c = c.replace('video_auto_tasks[t_id]["step_km"] = "រួចរាល់ ១០០% (ជោគជ័យ!)"', 'video_auto_tasks[t_id]["step_km"] = "100% Completed (Success!)"')
    c = c.replace('video_auto_tasks[t_id]["step_km"] = f"មានបញ្ហា: {str(e)}"', 'video_auto_tasks[t_id]["step_km"] = f"Error: {str(e)}"')
    p.write_text(c, encoding='utf-8')
    print("Updated server.py")

def translate_batch_engine():
    p = Path('batch_engine.py')
    c = p.read_text(encoding='utf-8')
    c = c.replace('"step": "រង់ចាំចាប់ផ្តើម",', '"step": "Waiting to start",')
    c = c.replace('target_item["step"] = "មានបញ្ហា"', 'target_item["step"] = "Error"')
    c = c.replace('item["step"] = "1/5 កំពុងទាញយកសំឡេងពីវីដេអូ..."', 'item["step"] = "1/5 Extracting audio from video..."')
    c = c.replace('item["step"] = "2/5 AI កំពុងបំបែកសំឡេង & រក្សាភ្លេង BGM..."', 'item["step"] = "2/5 AI separating vocals & preserving BGM bed..."')
    c = c.replace('item["step"] = "3/5 AI កំពុងស្តាប់ និងចាប់សំឡេង (Faster-Whisper)..."', 'item["step"] = "3/5 AI transcribing speech (Faster-Whisper)..."')
    c = c.replace('"speaker": "តួអង្គ",', '"speaker": "Character",')
    c = c.replace('v_label = "ពិសិដ្ឋ & ស្រីមុំ (Dual Voice)"', 'v_label = "Piseth & Sreymom (Dual Voice)"')
    c = c.replace('v_label = "ស្រីមុំ (Sreymom Solo)"', 'v_label = "Sreymom (Female Solo)"')
    c = c.replace('v_label = "ពិសិដ្ឋ (Piseth Solo)"', 'v_label = "Piseth (Male Solo)"')
    c = c.replace('item["step"] = f"4/5 AI កំពុងបកប្រែជាភាសាខ្មែរ {v_label} (Story Bible)..."', 'item["step"] = f"4/5 AI translating to Khmer {v_label} (Story Bible)..."')
    c = c.replace('item["step"] = f"5/5 កំពុងបញ្ចូលសំឡេងខ្មែរ {v_label} & Render..."', 'item["step"] = f"5/5 Synthesizing audio {v_label} & Rendering..."')
    c = c.replace('item["step"] = "រួចរាល់ ១០០%"', 'item["step"] = "100% Completed"')
    p.write_text(c, encoding='utf-8')
    print("Updated batch_engine.py")

def translate_pipeline_steps():
    p = Path('pipeline.py')
    c = p.read_text(encoding='utf-8')
    c = c.replace('v_desc = "ស្រីមុំ (Sreymom Solo)" if chosen_v == "sreymom" else "ពិសិដ្ឋ (Piseth Solo)"', 'v_desc = "Sreymom (Female Solo)" if chosen_v == "sreymom" else "Piseth (Male Solo)"')
    c = c.replace('voice_label = "ពិសិដ្ឋ & ស្រីមុំ (Dual Voice)"', 'voice_label = "Piseth & Sreymom (Dual Voice)"')
    c = c.replace('voice_label = "ស្រីមុំ (Sreymom Solo)"', 'voice_label = "Sreymom (Female Solo)"')
    c = c.replace('voice_label = "ពិសិដ្ឋ (Piseth Solo)"', 'voice_label = "Piseth (Male Solo)"')
    c = c.replace('update_prog(12, "១/៧ កំពុងទាញយកសំឡេងពីវីដេអូ...", "Extracting audio from video...")', 'update_prog(12, "1/7 Extracting audio from video...", "Extracting audio from video...")')
    c = c.replace('update_prog(28, "២/៧ កំពុងច្រោះសំឡេងចិនដើមចេញពីភ្លេង (Vocal Isolation)...", "Separating Chinese vocals from BGM...")', 'update_prog(28, "2/7 Separating original vocals from BGM...", "Separating vocals from BGM...")')
    c = c.replace('update_prog(45, f"៣/៧ AI កំពុងស្តាប់ និងចាប់សំឡេងដើម ({voice_label})...", "Transcribing speech...")', 'update_prog(45, f"3/7 AI transcribing dialogue ({voice_label})...", "Transcribing speech...")')
    c = c.replace('update_prog(48, f"៣/៧ កំពុងស្កេនសំឡេងដើមឡើងវិញ ({voice_label})...", "Retrying transcription on original audio...")', 'update_prog(48, f"3/7 Scanning original audio ({voice_label})...", "Retrying transcription on original audio...")')
    c = c.replace('update_prog(62, f"៤/៧ AI កំពុងបកប្រែជាភាសាខ្មែរ {voice_label} (Story Bible)...", f"Translating script to {voice_label}...")', 'update_prog(62, f"4/7 AI translating script ({voice_label})...", f"Translating script to {voice_label}...")')
    c = c.replace('update_prog(68, f"៤/៧ បកប្រែបានជោគជ័យ! កំពុងត្រៀមបញ្ចូលសំឡេង {voice_label}...", "Translation completed! Preparing voice synthesis...", dialogues=translated)', 'update_prog(68, f"4/7 Translation completed! Preparing voice synthesis ({voice_label})...", "Translation completed! Preparing voice synthesis...", dialogues=translated)')
    c = c.replace('update_prog(76, f"៥/៧ កំពុងបញ្ចូលសំឡេងខ្មែរ {voice_label}...", f"Synthesizing Khmer neural speech ({voice_label})...")', 'update_prog(76, f"5/7 Synthesizing neural voice ({voice_label})...", f"Synthesizing neural voice ({voice_label})...")')
    c = c.replace('update_prog(88, "៦/៧ កំពុងសម្រួលសំឡេង BGM & សំឡេងខ្មែរ (Zero Vocal Leakage)...", "Mixing dubbed audio with clean BGM...")', 'update_prog(88, "6/7 Mixing dubbed voice with BGM (Zero Vocal Leakage)...", "Mixing dubbed audio with clean BGM...")')
    c = c.replace('update_prog(95, "៧/៧ កំពុង Render វីដេអូ MP4 ជាសំឡេងខ្មែរ...", "Rendering final dubbed video...")', 'update_prog(95, "7/7 Rendering final dubbed MP4 video...", "Rendering final dubbed video...")')
    c = c.replace('update_prog(100, "🎉 រួចរាល់ ១០០%! វីដេអូសម្រេចបានរក្សាទុក!", "Completed! Video ready.")', 'update_prog(100, "🎉 100% Complete! Dubbed video saved successfully!", "Completed! Video ready.")')
    p.write_text(c, encoding='utf-8')
    print("Updated pipeline.py")

def translate_admin_key_generator():
    p = Path('ADMIN_KEY_GENERATOR.py')
    c = p.read_text(encoding='utf-8')
    replacements = [
        ('lic_mode = "🟢 ON (ត្រូវវាយ Key ទើបប្រើបាន)" if is_license_required() else "🟡 OFF (Free Mode - ប្រើបានភ្លាមៗមិនបាច់ Key)"', 'lic_mode = "🟢 ON (Key Required)" if is_license_required() else "🟡 OFF (Free Mode - No Key Required)"'),
        ('server_status = f"🟢 ដំណើរការស្រេច ({ADMIN_URL})" if is_server_running() else "🟡 កំពុងបើក..."', 'server_status = f"🟢 Running ({ADMIN_URL})" if is_server_running() else "🟡 Starting..."'),
        ('print(" 👑 SN STUDIO - ADMIN KEY GENERATOR (ប្រព័ន្ធគ្រប់គ្រង KEY ជូន USER)")', 'print(" 👑 SN STUDIO - ADMIN KEY GENERATOR (KEY MANAGEMENT SYSTEM)")'),
        ('f"👉 របៀបប្រើ៖ បើក SN STUDIO -> យក Key នេះ Paste ចូលរួចចុច Activate\\n"', 'f"👉 Instructions: Open SN STUDIO -> Paste this Key and click Activate\\n"'),
        ('print(" (✨ បាន Copy Key ចូល Clipboard ស្វ័យប្រវត្ត រួចជាស្រេច!)")', 'print(" (✨ Key copied to Clipboard automatically!)")'),
        ('print(" 🌐 ផ្នែកទី ១: WEB ADMIN DASHBOARD (ផ្ទាំងគ្រប់គ្រងលើ BROWSER)")', 'print(" 🌐 SECTION 1: WEB ADMIN DASHBOARD (BROWSER DASHBOARD)")'),
        ('print(" [1] បើកផ្ទាំង Admin Dashboard (http://127.0.0.1:8888/admin)")', 'print(" [1] Open Admin Dashboard (http://127.0.0.1:8888/admin)")'),
        ('print(" 🔑 ផ្នែកទី ២: បង្កើត KEY ជូនអតិថិជន (KEY GENERATION)")', 'print(" 🔑 SECTION 2: GENERATE KEY (KEY GENERATION)")'),
        ('print(" [2] បង្កើត License Key ថ្មី (កំណត់ចំនួនថ្ងៃ 30d, 90d, 1y, មួយជីវិត)")', 'print(" [2] Generate New License Key (Duration: 30d, 90d, 1y, Lifetime)")'),
        ('print(" [3] បង្កើត Custom Key ផ្ទាល់ខ្លួន (វាយអក្សរតាមចិត្ត ឧ. SAL-2026)")', 'print(" [3] Generate Custom Key Code (e.g. SAL-2026)")'),
        ('print(" [9] បង្កើត Lifetime Key មួយជីវិតភ្លាមៗ (Quick Lifetime)")', 'print(" [9] Quick Lifetime Key (Permanent Key)")'),
        ('print(" 👥 ផ្នែកទី ៣: គ្រប់គ្រងអតិថិជន & BLOCK USER (MANAGEMENT)")', 'print(" 👥 SECTION 3: CUSTOMER MANAGEMENT & BLOCK USER")'),
        ('print(" [4] បញ្ឈប់ / Block Key របស់ User (Revoke / Ban Key មិនឱ្យប្រើ)")', 'print(" [4] Block / Revoke User Key (Revoke / Ban Key)")'),
        ('print(" [5] ដោះសោ / Unban Key (Restore Key ឱ្យដំណើរការឡើងវិញ)")', 'print(" [5] Unban Key (Restore / Reactivate Key)")'),
        ('print(" [7] មើលប្រវត្តិ Key និងអតិថិជនទាំងអស់ (View All Keys History)")', 'print(" [7] View All Keys History")'),
        ('print(" [8] ត្រួតពិនិត្យ និង Verify License Key")', 'print(" [8] Verify License Key")'),
        ('print(" ⚙️ ផ្នែកទី ៤: ការកំណត់ GATE & SYSTEM (GATE SETTINGS)")', 'print(" ⚙️ SECTION 4: GATE & SYSTEM SETTINGS")'),
        ('print(" [6] បិទ / បើក ការទាមទារ Key (Toggle Free Mode vs Require Key)")', 'print(" [6] Toggle Free Mode vs Require Key")'),
        ('print(" [S] 🔄 ធ្វើបច្ចុប្បន្នភាព Key Online ទាំងអស់ (Sync & Export Online Keys)")', 'print(" [S] 🔄 Sync & Export Online Keys")'),
        ('print(" [0] ចាកចេញពីកម្មវិធី (Exit)")', 'print(" [0] Exit")'),
        ('choice = input("👉 សូមជ្រើសរើសជម្រើស (0-9 ឬ S): ").strip()', 'choice = input("👉 Select option (0-9 or S): ").strip()'),
        ('print("\\n\\n⚠️ បានទទួលសញ្ញាផ្អាក។ ប្រសិនបើចង់ចាកចេញ សូមជ្រើសរើសលេខ 0។")', 'print("\\n\\n⚠️ Interrupted. To exit, choose 0.")'),
        ('print("\\n⏳ កំពុងត្រួតពិនិត្យ និងបើកដំណើរការ Admin Server (Port 8888)...")', 'print("\\n⏳ Checking and starting Admin Server (Port 8888)...")'),
        ('print(f"🌐 Admin Server ដំណើរការរួចរាល់! កំពុងបើកផ្ទាំង Dashboard ក្នុង Browser ({url})...")', 'print(f"🌐 Admin Server ready! Opening Dashboard in browser ({url})...")'),
        ('print(f"⚠️ Admin Server កំពុងបើកយឺតបន្តិច ប៉ុន្តែកំពុងព្យាយាមបើក Browser ទៅកាន់៖ {url}")', 'print(f"⚠️ Admin Server starting slowly, attempting to open: {url}")'),
        ('print(f"✅ ប្រសិនបើ Browser មិនបើកដោយស្វ័យប្រវត្ត សូមចុចបើកតំណភ្ជាប់នេះ៖ {url}")', 'print(f"✅ If browser does not open automatically, visit: {url}")'),
        ('input("\\nចុច Enter ដើម្បីបន្ត...")', 'input("\\nPress Enter to continue...")'),
        ('client_name = input("\\n👤 បញ្ចូលឈ្មោះ Client/User (ឧ. Sokha_FB): ").strip() or "Client"', 'client_name = input("\\n👤 Enter Client/User Name (e.g. Sokha_FB): ").strip() or "Client"'),
        ('print("\\nជ្រើសរើសកាលកំណត់ (Duration):")', 'print("\\nSelect Duration:")'),
        ('print(" [1] 30 ថ្ងៃ (1 Month)")', 'print(" [1] 30 Days (1 Month)")'),
        ('print(" [2] 90 ថ្ងៃ (3 Months)")', 'print(" [2] 90 Days (3 Months)")'),
        ('print(" [3] 365 ថ្ងៃ (1 Year)")', 'print(" [3] 365 Days (1 Year)")'),
        ('print(" [4] ពេញមួយជីវិត (Lifetime)")', 'print(" [4] Lifetime (Permanent)")'),
        ('print(" [5] Trial 3 ថ្ងៃ (3-Day Trial)")', 'print(" [5] 3-Day Trial")'),
        ('print(" [6] វាយចំនួនថ្ងៃផ្ទាល់ខ្លួន (Custom Days ឧ. 5, 14, 60, 180...)")', 'print(" [6] Custom Days (e.g. 5, 14, 60, 180...)")'),
        ('dur_choice = input("👉 ជ្រើសរើស (1-6): ").strip()', 'dur_choice = input("👉 Select (1-6): ").strip()'),
        ('custom_d = int(input("👉 បញ្ចូលចំនួនថ្ងៃ (វាយ 0 សម្រាប់មួយជីវិត): ").strip() or "30")', 'custom_d = int(input("👉 Enter number of days (0 for Lifetime): ").strip() or "30")'),
        ('bind_hw = input("\\n🔒 ចង់ចាក់សោតាម HWID របស់ម៉ាស៊ីន Client ទេ?\\n(ចុច Enter ដើម្បីអនុញ្ញាតប្រើបានគ្រប់ម៉ាស៊ីន ឬ Paste HWID របស់ Client): ").strip()', 'bind_hw = input("\\n🔒 Lock to Client Machine HWID?\\n(Press Enter for Any Machine, or paste Client HWID): ").strip()'),
        ('print("\\n✍️ បង្កើត Custom Key ផ្ទាល់ខ្លួន (User-Defined Key / Password):")', 'print("\\n✍️ Create Custom Key (User-Defined Key / Password):")'),
        ('print(" (ឧទាហរណ៍៖ SAL-2026, SAL888, KHMER-STUDIO)")', 'print(" (e.g.: SAL-2026, SAL888, VIP-STUDIO)")'),
        ('custom_key = input("👉 បញ្ចូល Key ឬពាក្យសម្ងាត់ដែលបងចង់បាន: ").strip()', 'custom_key = input("👉 Enter desired Key code: ").strip()'),
        ('print("⚠️ មិនបានបញ្ចូល Key ទេ!")', 'print("⚠️ No Key entered!")'),
        ('client_name = input("👤 ឈ្មោះ Client (ឧ. Sal / Sokha): ").strip() or "Client"', 'client_name = input("👤 Client Name (e.g. Sal / Sokha): ").strip() or "Client"'),
        ('print("\\nកាលកំណត់សម្រាប់ Key នេះ:")', 'print("\\nDuration for this Key:")'),
        ('print(" [1] ពេញមួយជីវិត (Lifetime - គ្មានថ្ងៃផុតកំណត់)")', 'print(" [1] Lifetime (Permanent - Never Expires)")'),
        ('print(" [2] វាយចំនួនថ្ងៃជាក់លាក់ (Custom Days ឧ. 7, 30, 90, 365...)")', 'print(" [2] Custom Days (e.g. 7, 30, 90, 365...)")'),
        ('d_opt = input("👉 ជ្រើសរើស (1 ឬ 2): ").strip()', 'd_opt = input("👉 Select (1 or 2): ").strip()'),
        ('days = int(input("👉 បញ្ចូលចំនួនថ្ងៃ: ").strip() or "30")', 'days = int(input("👉 Enter number of days: ").strip() or "30")'),
        ('bind_hw = input("\\n🔒 ចង់ចាក់សោតាម HWID របស់ម៉ាស៊ីន Client ទេ?\\n(ចុច Enter ដើម្បីប្រើបានគ្រប់ម៉ាស៊ីន ឬ Paste HWID): ").strip()', 'bind_hw = input("\\n🔒 Lock to Client Machine HWID?\\n(Press Enter for Any Machine, or paste HWID): ").strip()'),
        ('print("\\n🚫 បញ្ឈប់ / Block Key របស់ User (Revoke / Ban Key):")', 'print("\\n🚫 Block / Revoke User Key:")'),
        ('key_to_ban = input("👉 បញ្ចូល Key ដែលបងចង់ Block មិនឱ្យប្រើ: ").strip()', 'key_to_ban = input("👉 Enter Key to block: ").strip()'),
        ("confirm = input(f\"⚠️ តើបងប្រាកដទេថាចង់បញ្ឈប់/Block Key '{key_to_ban}'? (y/n): \").strip().lower()", "confirm = input(f\"⚠️ Are you sure you want to block Key '{key_to_ban}'? (y/n): \").strip().lower()"),
        ("if confirm in ('y', 'yes', 'បាទ', 'ចាស'):", "if confirm in ('y', 'yes'):"),
        ('print("🚫 បានបោះបង់ប្រតិបត្តិការ។")', 'print("🚫 Operation cancelled.")'),
        ('print("\\n♻️ ដោះសោ / Unban Key (Restore Key):")', 'print("\\n♻️ Unban / Restore Key:")'),
        ('key_to_unban = input("👉 បញ្ចូល Key ដែលចង់ Unblock ឱ្យដំណើរការវិញ: ").strip()', 'key_to_unban = input("👉 Enter Key to unblock: ").strip()'),
        ("print(f\"\\n⚙️ ស្ថានភាពបច្ចុប្បន្ន៖ {'🟢 កំពុងទាមទារ License Key (ON)' if current_status else '🟡 កំពុងបើក Free Mode (OFF - មិនបាច់វាយ Key)'}\")", "print(f\"\\n⚙️ Current Status: {'🟢 License Key Required (ON)' if current_status else '🟡 Free Mode (OFF - No Key Required)'}\")"),
        ('print(" [1] បើកការទាមទារ Key (User ត្រូវតែមាន Key ទើបប្រើបាន)")', 'print(" [1] Enable Key Requirement (Valid key required)")'),
        ('print(" [2] បិទការទាមទារ Key (Free Mode - អ្នកណាក៏បើកប្រើបានភ្លាមៗ)")', 'print(" [2] Disable Key Requirement (Free Mode - Open to all)")'),
        ('toggle_choice = input("👉 ជ្រើសរើស (1 ឬ 2): ").strip()', 'toggle_choice = input("👉 Select (1 or 2): ").strip()'),
        ('print("✅ បានបើកការទាមទារ License Key (User ត្រូវវាយ Key ទើបប្រើបាន)")', 'print("✅ Enabled License Key Requirement (Key required)")'),
        ('print("🎉 បានបើក Free Mode (User មិនបាច់វាយ Key ទេ បើកមកប្រើបានភ្លាមៗ)")', 'print("🎉 Enabled Free Mode (No key required)")'),
        ("print(f\"\\n📜 បញ្ជី License Keys ទាំងអស់ ({len(history)} Keys):\")", "print(f\"\\n📜 All License Keys ({len(history)} Keys):\")"),
        ('print("\\n⚠️ មិនទាន់មាន Key ណាមួយត្រូវបានបង្កើតនៅឡើយទេ។")', 'print("\\n⚠️ No keys generated yet.")'),
        ('test_key = input("\\n🔍 បញ្ចូល License Key ដែលចង់ Check: ").strip()', 'test_key = input("\\n🔍 Enter License Key to check: ").strip()'),
        ('name = input("\\n👤 ឈ្មោះ Client: ").strip() or "User_Lifetime"', 'name = input("\\n👤 Client Name: ").strip() or "User_Lifetime"'),
        ('print("\\n🔄 កំពុង Sync Key ទាំងអស់ទៅកាន់ Online Registry...")', 'print("\\n🔄 Syncing keys to Online Registry...")'),
        ("print(f\"✅ បាន Sync Key សរុប {len(keys)} Keys ទៅកាន់ data/license_keys_online.json និង dist/ រួចរាល់!\")", "print(f\"✅ Synced {len(keys)} keys to data/license_keys_online.json and dist/ successfully!\")"),
        ('confirm = input("👉 តើអ្នកពិតជាចង់ចាកចេញមែនទេ? (y/n): ").strip().lower()', 'confirm = input("👉 Are you sure you want to exit? (y/n): ").strip().lower()'),
        ('print("\\n👋 អរគុណ! ចាកចេញពី Admin Key Generator ដោយសុវត្ថិភាព។\\n")', 'print("\\n👋 Goodbye! Safely exited Admin Key Generator.\\n")'),
        ("print(f\"\\n⚠️ ជម្រើស '{choice}' មិនត្រឹមត្រូវទេ! សូមជ្រើសរើសជម្រើសដែលមានក្នុងបញ្ជី (0-9 ឬ S)។\")", "print(f\"\\n⚠️ Invalid choice '{choice}'! Please select from list (0-9 or S).\")"),
        ("print(f\"\\n⚠️ កើតមានបញ្ហា៖ {e}\")", "print(f\"\\n⚠️ An error occurred: {e}\")"),
        ('input("\\nចុច Enter ដើម្បីបិទ...")', 'input("\\nPress Enter to close...")'),
    ]
    for src, dst in replacements:
        c = c.replace(src, dst)
    p.write_text(c, encoding='utf-8')
    print("Updated ADMIN_KEY_GENERATOR.py")

if __name__ == '__main__':
    translate_license_engine()
    translate_desktop_and_run()
    translate_server_py()
    translate_batch_engine()
    translate_pipeline_steps()
    translate_admin_key_generator()

