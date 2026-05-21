import asyncio
import json

from config import BENCHMARK_DIR, LANGUAGES
from googletrans import Translator

FILE_IN = BENCHMARK_DIR / "en.json"


async def main():
    data_in = json.loads(FILE_IN.read_text(encoding="utf-8"))
    for target_lang in LANGUAGES:
        if target_lang == "en":
            continue
        file_out = BENCHMARK_DIR / f"{target_lang}.json"
        data_out = (
            json.loads(file_out.read_text(encoding="utf-8"))
            if file_out.exists()
            else []
        )

        # Get the last processed ID to skip already translated items
        last_id = data_out[-1]["global_id"] if data_out else -1

        async with Translator() as translator:
            for entry in data_in:
                if entry["global_id"] <= last_id:
                    continue

                print(f"Translating ID: {entry['global_id']}")
                try:
                    # Translate and update the question
                    res = await translator.translate(
                        entry["question"], dest=target_lang
                    )
                    entry["question"] = res.text
                    data_out.append(entry)

                    # Save progress
                    file_out.write_text(
                        json.dumps(data_out, indent=4, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Error at {entry['global_id']}: {e}")
                    break


if __name__ == "__main__":
    asyncio.run(main())
