"""
AI Viral Facebook & TikTok Movie Recap Engine & Storyteller Hook Generator
"""
import random
from typing import List, Dict, Any, Optional

VIRAL_KHMER_HOOKS = {
    "drama_revenge": [
        "កុំទាន់អាលរំលង! រឿងរ៉ាវរបស់យុវជនម្នាក់នេះនឹងធ្វើឱ្យអ្នកស្មានមិនដល់...",
        "មនុស្សគ្រប់គ្នាមើលងាយគាត់ថាជាអ្នកក្រ ប៉ុន្តែការពិតគាត់គឺជាមហាសេដ្ឋីលាក់មុខ!",
        "៣ ឆ្នាំក្រោយមក គាត់បានត្រលប់មកវិញជាមួយអំណាច និងការសងសឹកដ៏កក្រើក!"
    ],
    "romance_emotional": [
        "រឿងស្នេហាដ៏កម្សត់មួយនេះ បានធ្វើឱ្យមនុស្សរាប់លាននាក់ស្រក់ទឹកភ្នែក...",
        "ទោះបីជាពិភពលោកទាំងមូលប្រឆាំង ក៏បងនៅតែជ្រើសរើសការពារអូនជានិច្ច!",
        "តើអ្នកធ្លាប់ស្រលាញ់មនុស្សម្នាក់ដែលមិនអាចនៅក្បែរគ្នាបានដែរទេ?"
    ],
    "action_suspense": [
        "ត្រៀមខ្លួនឱ្យហើយ! នេះគឺជាឈុតឆាកប្រយុទ្ធដ៏រំភើបញាប់ញ័រដែលអ្នកមិនដែលបានឃើញពីមុនមក!",
        "ពេលវេលានៅសល់តែ ៦០ វិនាទីប៉ុណ្ណោះ តើពួកគេអាចគេចផុតពីគ្រោះថ្នាក់នេះបានដែរឬទេ?",
        "កុំភ្លេចដកដង្ហើម ព្រោះសាច់រឿងបន្ទាប់ពីនេះនឹងធ្វើឱ្យអ្នករំភើបស្ទើរគាំងបេះដូង!"
    ],
    "comedy_funny": [
        "ធានាថាមើលហើយមិនសើច មិនយកលុយទេបងប្អូន!",
        "គ្រាន់តែជួបគ្នាថ្ងៃដំបូងសោះ តួឯកប្រុសស្រីរបស់យើងបានបង្កភាពចលាចលពេញក្រុង!",
        "តោះមកមើលរឿងកំប្លែងសើចចុកពោះប្រចាំថ្ងៃទាំងអស់គ្នា!"
    ]
}

VIRAL_KHMER_OUTROS = [
    "តើអ្នកទាំងអស់គ្នាគិតថាតួឯករបស់យើងនឹងដោះស្រាយរឿងនេះយ៉ាងណា? កុំភ្លេចចុច Like & Follow ដើម្បីរង់ចាំទស្សនាភាគ ២ ទាំងអស់គ្នា!",
    "សាច់រឿងភាគទីមួយត្រូវបានបញ្ចប់ត្រឹមនេះ! សូមជួយចុច Share ម្នាក់មួយដើម្បីទទួលបានភាគបន្តភ្លាមៗ!",
    "តើអ្នកយល់យ៉ាងណាដែរចំពោះរឿងមួយនេះ? សូមបញ្ចេញមតិនៅខាងក្រោម!"
]


class RecapEngine:
    @staticmethod
    def get_hooks(genre: str = "drama_revenge") -> List[str]:
        """Get pre-curated viral hooks for selected genre."""
        return VIRAL_KHMER_HOOKS.get(genre, VIRAL_KHMER_HOOKS["drama_revenge"])

    @staticmethod
    def inject_viral_hook(dialogues: List[Dict[str, Any]], hook_text: str, voice: str = "piseth") -> List[Dict[str, Any]]:
        """Prepend a viral hook to the dialogue script and shift timestamps."""
        hook_item = {
            "id": 1,
            "start": 0.0,
            "end": 3.5,
            "speaker": "អ្នកសម្រាយ (Viral Hook)",
            "text_original": hook_text,
            "text_km": hook_text,
            "voice": voice,
            "rate_percent": 5,
            "pitch_hz": 0
        }
        
        # Shift existing dialogues by 3.8s
        shifted = []
        for idx, item in enumerate(dialogues, start=2):
            item_copy = dict(item)
            item_copy["id"] = idx
            item_copy["start"] = round(item.get("start", 0) + 3.8, 2)
            item_copy["end"] = round(item.get("end", 3.0) + 3.8, 2)
            shifted.append(item_copy)

        return [hook_item] + shifted

    @staticmethod
    def inject_viral_outro(dialogues: List[Dict[str, Any]], outro_text: Optional[str] = None, voice: str = "piseth") -> List[Dict[str, Any]]:
        """Append a call-to-action outro (Like & Follow for Part 2)."""
        outro = outro_text or random.choice(VIRAL_KHMER_OUTROS)
        last_end = dialogues[-1].get("end", 10.0) if dialogues else 0.0
        
        outro_item = {
            "id": len(dialogues) + 1,
            "start": round(last_end + 0.5, 2),
            "end": round(last_end + 4.5, 2),
            "speaker": "អ្នកសម្រាយ (Call To Action)",
            "text_original": outro,
            "text_km": outro,
            "voice": voice,
            "rate_percent": 0,
            "pitch_hz": 0
        }
        return list(dialogues) + [outro_item]
