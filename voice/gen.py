"""สร้างไฟล์เสียงพูดของน้องนำทางจาก voice/phrases.json (รันบน GitHub Actions ทุกชั่วโมงจนครบ)
บริการเสียงฟรีจะปฏิเสธถ้าขอถี่เกินไป จึงสร้างทีละน้อยแล้วเก็บไฟล์ไว้ทุกรอบ"""
import asyncio, json, os, time
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "phrases.json"), encoding="utf-8"))
MAX_PER_RUN = 70
GAP_SECONDS = 2.5
STOP_AFTER_FAILS = 4

def write_manifest():
    files = sorted(f[:-4] for f in os.listdir(HERE) if f.endswith(".mp3"))
    json.dump({"voice": data["voices"], "files": files}, open(os.path.join(HERE, "manifest.json"), "w"))
    return files

async def make(item):
    path = os.path.join(HERE, f"{item['id']}.mp3")
    for attempt in range(2):
        try:
            await edge_tts.Communicate(item["text"], data["voices"][item["lang"]], rate=data.get("rate", "+0%")).save(path)
            if os.path.getsize(path) > 0:
                return True
        except Exception as e:
            print(f"fail {item['id']} ({attempt+1}): {e}")
            time.sleep(4)
    if os.path.exists(path):
        os.remove(path)
    return False

async def main():
    wanted = {it["id"] for it in data["items"]}
    for f in os.listdir(HERE):
        if f.endswith(".mp3") and f[:-4] not in wanted:
            os.remove(os.path.join(HERE, f))
    todo = [it for it in data["items"] if not os.path.exists(os.path.join(HERE, f"{it['id']}.mp3"))]
    todo.sort(key=lambda it: it["lang"] != "th")  # ภาษาไทยก่อน
    made = fails = 0
    for it in todo[:MAX_PER_RUN]:
        if await make(it):
            made += 1; fails = 0
        else:
            fails += 1
            if fails >= STOP_AFTER_FAILS:
                print("service is refusing requests now; will continue next run")
                break
        time.sleep(GAP_SECONDS)
    files = write_manifest()
    print(f"made {made} this run, total {len(files)}/{len(wanted)} clips")

asyncio.run(main())
