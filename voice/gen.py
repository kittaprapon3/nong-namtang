"""สร้างไฟล์เสียงพูดของน้องนำทางจาก voice/phrases.json (รันบน GitHub Actions ทุกชั่วโมงจนครบ)
บริการเสียงฟรีจะปฏิเสธถ้าขอถี่เกินไป จึงสร้างทีละน้อยแล้วเก็บไฟล์ไว้ทุกรอบ
ไฟล์เก็บแยกโฟลเดอร์ตามเสียงที่ใช้ ถ้าเปลี่ยนเสียง จะสร้างชุดใหม่ทั้งหมด"""
import asyncio, json, os, re, shutil, time
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "phrases.json"), encoding="utf-8"))
RATE, PITCH = data.get("rate", "+0%"), data.get("pitch", "+0Hz")
SLUG = re.sub(r"[^A-Za-z0-9]+", "-", f"{data['voices']['th']}-{data['voices']['en']}-{RATE}-{PITCH}").strip("-").lower()
OUT = os.path.join(HERE, SLUG)
MAX_PER_RUN, GAP_SECONDS, STOP_AFTER_FAILS = 400, 1.0, 4

async def make(item):
    path = os.path.join(OUT, f"{item['id']}.mp3")
    for attempt in range(2):
        try:
            await edge_tts.Communicate(item["text"], data["voices"][item["lang"]], rate=RATE, pitch=PITCH).save(path)
            if os.path.getsize(path) > 0:
                return True
        except Exception as e:
            print(f"fail {item['id']} ({attempt+1}): {e}")
            time.sleep(4)
    if os.path.exists(path):
        os.remove(path)
    return False

async def main():
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(HERE):  # ล้างชุดเสียงเก่า
        p = os.path.join(HERE, name)
        if os.path.isdir(p) and name != SLUG:
            shutil.rmtree(p)
        elif name.endswith(".mp3"):
            os.remove(p)
    wanted = {it["id"] for it in data["items"]}
    for f in os.listdir(OUT):
        if f[:-4] not in wanted:
            os.remove(os.path.join(OUT, f))
    todo = [it for it in data["items"] if not os.path.exists(os.path.join(OUT, f"{it['id']}.mp3"))]
    todo.sort(key=lambda it: it["lang"] != "th")  # ภาษาไทยก่อน
    made = 0
    for lang in ("th", "en"):  # ถ้าเสียงภาษาหนึ่งถูกปฏิเสธ ยังสร้างอีกภาษาต่อได้
        fails = 0
        for it in [t for t in todo if t["lang"] == lang][:MAX_PER_RUN]:
            if await make(it):
                made += 1; fails = 0
            else:
                fails += 1
                if fails >= STOP_AFTER_FAILS:
                    print(f"{lang}: service is refusing requests now; will continue next run")
                    break
            time.sleep(GAP_SECONDS)
    files = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".mp3"))
    json.dump({"dir": SLUG, "voice": data["voices"], "files": files}, open(os.path.join(HERE, "manifest.json"), "w"))
    print(f"made {made} this run, total {len(files)}/{len(wanted)} clips")

asyncio.run(main())
