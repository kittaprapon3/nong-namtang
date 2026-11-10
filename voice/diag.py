import asyncio, edge_tts, os, time
T=["ไปทางเข้า โรงพยาบาลนะคะ","เดินตรงไปประมาณ 30 เมตร","เดินตรงไปประมาณ 45 เมตร","ก็จะถึงห้องยาค่ะ"]
V=["th-TH-PremwadeeNeural","th-TH-AcharaNeural","th-TH-NiwatNeural"]
async def one(t,v,rate):
    try:
        await edge_tts.Communicate(t,v,rate=rate).save("/tmp/x.mp3");return os.path.getsize("/tmp/x.mp3")
    except Exception as e: return type(e).__name__
async def main():
    print("edge-tts",edge_tts.__version__ if hasattr(edge_tts,"__version__") else "?")
    for v in V:
        for rate in ["-6%","+0%"]:
            for t in T:
                r=[await one(t,v,rate) for _ in range(2)];print(v,rate,t,r);time.sleep(1)
asyncio.run(main())
