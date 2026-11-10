"""สร้างไฟล์เสียงพูดของน้องนำทางจาก voice/phrases.json (รันบน GitHub Actions)"""
import asyncio, json, os, sys
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "phrases.json"), encoding="utf-8"))

async def make(item):
    path = os.path.join(HERE, f"{item['id']}.mp3")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return True
    voice = data["voices"][item["lang"]]
    for attempt in range(4):
        try:
            await edge_tts.Communicate(item["text"], voice, rate=data.get("rate", "+0%")).save(path)
            if os.path.getsize(path) > 0:
                return True
        except Exception as e:
            print(f"retry {attempt+1} {item['id']}: {e}", file=sys.stderr)
            await asyncio.sleep(2 * (attempt + 1))
    if os.path.exists(path):
        os.remove(path)
    return False

async def main():
    sem = asyncio.Semaphore(4)
    async def run(it):
        async with sem:
            return await make(it)
    results = await asyncio.gather(*(run(it) for it in data["items"]))
    wanted = {it["id"] for it in data["items"]}
    for f in os.listdir(HERE):
        if f.endswith(".mp3") and f[:-4] not in wanted:
            os.remove(os.path.join(HERE, f))
    files = sorted(f[:-4] for f in os.listdir(HERE) if f.endswith(".mp3"))
    json.dump({"voice": data["voices"], "files": files}, open(os.path.join(HERE, "manifest.json"), "w"))
    print(f"ok {sum(results)}/{len(results)} clips")
    if sum(results) < len(results) * 0.9:
        sys.exit(1)

asyncio.run(main())
