"""LabLayout smoke tests (headless Chromium via Playwright).

    pip install playwright && python -m playwright install chromium
    python build.py && python tests/smoke_test.py

Covers: builder load/export, undo/redo, multi-select + align, custom library
pieces, re-export keeping data, tracker backup/restore, reorder list, due
dates/overdue, and two-device sync against an in-memory fake Supabase.
"""
import functools, http.server, json, pathlib, re, shutil, sys, tempfile, threading, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
FAILS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def watch_errors(page, bucket):
    page.on("pageerror", lambda e: bucket.append(str(e)))
    page.on("console", lambda m: m.type == "error" and bucket.append(m.text))


def builder_export(page, out):
    with page.expect_download() as d:
        page.click("#bExport")
        if page.locator("#bExport", has_text="Tap again").count():
            page.click("#bExport")
    d.value.save_as(out)


class FakeSupabase:
    """Just enough PostgREST for the tracker's sync: GET/POST/PATCH on lablayout_rooms."""
    def __init__(self):
        self.rows = {}

    def handle(self, route):
        req = route.request
        q = urllib.parse.parse_qs(urllib.parse.urlparse(req.url).query)
        rid = q.get("id", ["eq."])[0][3:]
        if req.method == "GET":
            body = [self.rows[rid]] if rid in self.rows else []
            if not rid:
                body = [{"id": k} for k in self.rows][:1]
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
        data = json.loads(req.post_data or "{}")
        if req.method == "POST":
            self.rows[data["id"]] = {"rev": data["rev"], "data": data["data"]}
            return route.fulfill(status=201, content_type="application/json", body=json.dumps([self.rows[data["id"]]]))
        if req.method == "PATCH":
            want = int(q["rev"][0][3:])
            row = self.rows.get(rid)
            if not row or row["rev"] != want:
                return route.fulfill(status=200, content_type="application/json", body="[]")
            row.update(rev=data["rev"], data=data["data"])
            return route.fulfill(status=200, content_type="application/json", body=json.dumps([row]))
        return route.fulfill(status=405, body="")


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lablayout-test-"))
    shutil.copy(DIST / "builder.html", tmp / "builder.html")
    srv, base = serve(tmp)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            ctx = br.new_context(accept_downloads=True, viewport={"width": 1400, "height": 900})
            errs = []

            print("builder")
            b = ctx.new_page(); watch_errors(b, errs)
            b.goto(base + "/builder.html")
            b.click("#bEx")
            b.wait_for_timeout(200)
            n0 = b.evaluate("P.units.length")
            check(n0 > 3, f"example loads ({n0} units)")
            b.fill("#title", "Smoke Lab")

            b.evaluate("select(P.units[0].id)")
            b.click("#bDel"); b.click("#bDel")
            check(b.evaluate("P.units.length") == n0 - 1, "delete removes a unit")
            b.keyboard.press("Control+z")
            check(b.evaluate("P.units.length") == n0, "Ctrl+Z restores it")
            b.keyboard.press("Control+Shift+z")
            check(b.evaluate("P.units.length") == n0 - 1, "Ctrl+Shift+Z redoes")
            b.keyboard.press("Control+z")

            b.evaluate("selSet.clear();['w1','w2'].forEach(i=>selSet.add(i));selId='w2';selChanged()")
            check(b.locator("#props", has_text="2 pieces selected").count() == 1, "multi-select panel shows")
            b.evaluate("U('w2').x=1.5;alignSel('l')")
            check(b.evaluate("U('w1').x===U('w2').x"), "align left lines pieces up")
            b.keyboard.press("Control+z")

            b.evaluate("select('h')")
            b.fill("#plib", "My Husky")
            b.click("#bLib")
            check(b.locator(".li", has_text="My Husky").count() == 1, "custom piece appears in library")
            b.evaluate("addFromLib(allLib()[0].items[0],3,3)")
            nu = b.evaluate("P.units[P.units.length-1]")
            check(nu["name"].startswith("My Husky") and all(c["id"].startswith(nu["id"] + "-") for c in nu["grid"]["cells"]),
                  "custom piece adds with fresh drawer ids")
            b.keyboard.press("Control+z")

            # measurements + snap-to-wall smoke
            b.evaluate("select('w3')")
            check(b.locator("#plan .meas").count() > 0, "measurement labels drawn for selection")
            snapped = b.evaluate("snapWall({w:2,d:2},0.3,5)")
            check(snapped["x"] == 0, "snaps to a nearby wall")

            check(b.evaluate("LIB.filter(c=>c.grp==='Equipment').reduce((a,c)=>a+c.items.length,0)") >= 100 and b.evaluate("!!libItem('scope4ch')&&!!libItem('laserjet')"), "equipment library pack is bundled")
            check(b.evaluate("addPack({name:'Test pack',categories:[{name:'X',items:[{k:'tp1',n:'Thing',w:5,h:5,fp:[.5,.5]},{k:'scope4ch',n:'dup',w:1,h:1,fp:[1,1]}]}]}).added") == 1, "library packs append and skip duplicate keys")
            print("rooms, inventory mode, metric")
            b.click("#bRoomAdd")
            check(b.evaluate("[PROJ.rooms.length,P.units.length,PROJ.rooms[0].units.length]") == [2, 0, n0], "+ Room adds an empty second room")
            b.click("[data-room='0']")
            check(b.evaluate("P.units.length") == n0, "switching rooms brings the first room back")
            b.click("#mUse"); b.wait_for_timeout(600)
            check(b.frame_locator("#usef").locator(".unit").count() > 0 and b.evaluate("$('editv').style.display")=="none", "Inventory mode shows the tracker in the app")
            b.click("#mEdit")
            b.click("#bUnits")
            check(b.evaluate("[MET(),fmtLen(10),Math.abs(parseLen('3 m')-9.8425)<1e-3,Math.abs(parseLen('2')-6.5617)<1e-3]") == [True, "3.048 m", True, True], "metric display and entry")
            b.click("#bUnits")
            b.evaluate("goRoom(1)"); b.click("#bRoomDel"); b.click("#bRoomDel")
            check(b.evaluate("PROJ.rooms.length") == 1, "room can be deleted")
            print("AI layout spec")
            before = b.evaluate("JSON.stringify(P.units)")
            rt = b.evaluate("(()=>{const s=LabLayout.exportSpec(),a=JSON.stringify(P.units.map(u=>[u.id,u.x,u.y,u.w,u.d,(u.grid||{cells:[]}).cells.map(c=>c.id+c.name)]));const r=LabLayout.importSpec(JSON.parse(JSON.stringify(s)));return [r.ok, a===JSON.stringify(P.units.map(u=>[u.id,u.x,u.y,u.w,u.d,(u.grid||{cells:[]}).cells.map(c=>c.id+c.name)]))]})()")
            check(rt == [True, True], "exportSpec -> importSpec round trip keeps ids, sizes and cells")
            bad = b.evaluate("LabLayout.validate({room:{width:10,depth:10},items:[{kind:'workbench',x:0,y:0},{kind:'custom',x:1,y:1,footprint:[2,2],front:[20,20],cells:[{x:0,y:0,w:30,h:5}]}]}).errors")
            check(len(bad) >= 2 and "Did you mean" in bad[0] and any("extends past" in e for e in bad), "validator explains unknown kinds and oversized cells")
            reply = 'Sure! Here you go:\n```json\n{"lablayout":1,"title":"Bot room","room":{"width":12,"depth":10},"items":[{"kind":"bench2","name":"Bench","x":0,"y":0,"drawers":["Bits"],"on_top":["hakko"]},{"kind":"flam30","x":10,"y":5,"rotate":90}]}\n```\nEnjoy.'
            r = b.evaluate("s=>LabLayout.importSpec(s)", reply)
            got = b.evaluate("[P.title,P.units.length,P.units[0].grid.cells[0].name,P.units[0].eq.map(e=>e.a).join(),P.units[1].w<P.units[1].d]")
            check(r["ok"] and got == ["Bot room", 2, "Bits", "hakko", True], "chatbot reply with prose + fences imports (names, on_top, rotate)")
            b.keyboard.press("Control+z"); b.keyboard.press("Control+z")
            check(b.evaluate("JSON.stringify(P.units)") == before, "undo returns to the original room")
            print("wall sketch tools")
            check(b.evaluate("[parseLen(\"10' 6\\\"\"),parseLen('126\"'),parseLen('10.5'),parseLen('10 6')].every(v=>Math.abs(v-10.5)<1e-9)"),
                  "typed lengths parse (10' 6\", 126\", 10.5, 10 6)")
            hv = b.evaluate("sketchSnap({x:9.93,y:0.08},{pts:[[0,0]],from:[0,0]})")
            check(hv["y"] == 0 and hv["x"] == 10 and hv["tag"] == "Horizontal", "near-horizontal snaps flat onto the 3\" grid")
            al = b.evaluate("sketchSnap({x:6.05,y:9.6},{pts:[[0,0],[6,3]],from:[0,9.6]})")
            check(al["x"] == 6 and al["guides"], "aligns with another corner (inference line)")
            check(b.evaluate("sketchSnap({x:0.04,y:0.03},{pts:[[0,0],[5,0],[5,5]],closing:true}).tag==='Close'"), "snaps to first corner to close")
            b.evaluate("P0=JSON.parse(JSON.stringify(P.room.poly));P.room.poly=[[0,0],[10,0,2],[10,8,0,1.5],[0,8]];setWallLen(0,12)")
            check(b.evaluate("P.room.poly[1][0]===12&&P.room.poly[2][0]===12&&P.room.poly[1][2]===2"), "setting a wall length stretches the room and keeps fillets")
            ol = b.evaluate("roomOutline(P.room.poly)")
            check(len(ol) > 20 and any(abs(p[0]-6) < .3 and abs(p[1]-6.5) < .05 for p in ol), "fillets and curved walls render as smooth outlines")
            b.evaluate("P.room.poly=P0;draw()")

            print("furniture designer")
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="914.4mm" height="762mm" viewBox="0 0 914.4 762">'
                   '<rect x="0" y="0" width="914.4" height="762"/><g transform="translate(10,10)">'
                   '<rect id="rect2" x="0" y="0" width="437.2" height="365"><title>Top drawer</title></rect>'
                   '<rect x="200" y="20" width="40" height="8"/>'
                   '<rect x="0" y="375" width="437.2" height="357"/><text x="218" y="550">Bottom</text>'
                   '<rect id="right_door" x="447.2" y="0" width="447.2" height="732"/></g></svg>')
            b.click("#bDesign")
            b.evaluate("s=>dImportSVG(s)", svg)
            r = b.evaluate("[D.W,D.H,D.rects.map(r=>r.name).sort()]")
            check(r[0] == 36 and r[1] == 30, "SVG in mm imports at real size (36\" x 30\")")
            check(r[2] == ["Bottom", "Top drawer", "right door"], "cells named from <title>, text inside and id; handles ignored")
            check(b.evaluate("D.rects.find(r=>r.name==='right door').cls==='cab'"), "door cells become cabinets")
            g = b.evaluate("(()=>{const u={id:'zz',front:{W:D.W,H:D.H},grid:rectsToGrid(D.rects,'zz',D.W,D.H)};return JSON.stringify(gridToRects(u).map(r=>[r.x,r.y,r.w,r.h]).sort())===JSON.stringify(D.rects.map(r=>[r.x,r.y,r.w,r.h]).sort())})()")
            check(g, "designer layout survives saving and reopening")
            styled = b.evaluate("""(()=>{Object.assign(D.look,{tex:'wood',base:'casters',hs:'knob',body:'#3b2a1e'});D.surf=true;dRender();
                const k=()=>JSON.stringify(D.rects.map(r=>[r.name,r.cls,r.x,r.y,r.w,r.h]).sort()),b4=k();dImportSVG(dSVGText());return b4===k()})()""")
            check(styled, "styled SVG (texture, casters, top) imports back to the same layout")
            b.click("#dSave"); b.click("#dClose")
            check(b.locator(".li", has_text="New piece").count() >= 1, "designed piece saved to My pieces")

            builder_export(b, tmp / "t1.html")
            check((tmp / "t1.html").stat().st_size > 50000, "exported tracker HTML")

            print("tracker")
            t = ctx.new_page(); watch_errors(t, errs)
            t.goto(base + "/t1.html")
            t.fill("#me", "Tester")
            t.evaluate("""()=>{const a=newItem('2x Keep wrench');addTo('w3-d1',a);const g=newItem('Gone hammer');addTo('w1-d1',g);
                          const r=newItem('3x Zip ties');r.min=5;addTo('w3-d2',r);save();render()}""")
            t.click('#tabs [data-k="reorder"]')
            check(t.locator("#reorderlist", has_text="Zip ties").count() == 1, "low item shows in reorder list")
            with t.expect_download() as d:
                t.click("#roCsv")
            csv = pathlib.Path(d.value.path()).read_text(encoding="utf-8")
            check("Zip ties" in csv and csv.startswith("Item,"), "reorder CSV downloads")

            t.evaluate("""()=>{const o=newItem('Old drill');S.out.push({id:'o1',t:o.t,q:1,from:'w3-d3',who:'Maya',at:Date.now()-2*864e5,due:Date.now()-864e5});addPerson('Maya');save();render()}""")
            t.click('#tabs [data-k="out"]')
            check(t.locator("#outlist .late", has_text="Old drill").count() == 1, "past-due checkout marked overdue")
            check("⚠1" in t.inner_text('#tabs [data-k="out"]'), "overdue count on tab")
            check(t.evaluate("S.people.includes('Maya')"), "person added to roster")

            with t.expect_download() as d:
                t.click("#bBackup")
            bk = tmp / "backup.json"; d.value.save_as(bk)
            t.evaluate("S.items['w3-d1']=[];save();render()")
            t.set_input_files("#restoref", str(bk))
            t.click("#rsOk")
            check(t.evaluate("S.items['w3-d1'].some(x=>x.t==='Keep wrench')"), "restore brings data back")

            print("re-export keeps data")
            b.bring_to_front()
            b.evaluate("P.units=P.units.filter(u=>u.id!=='w1');draw()")
            builder_export(b, tmp / "t2.html")  # new name so the browser can't serve a cached copy
            t.goto(base + "/t2.html")
            check(t.evaluate("S.items['w3-d1'].some(x=>x.t==='Keep wrench'&&x.q===2)"), "items in kept drawers stay")
            check(t.evaluate("S.items.pool.some(x=>x.t==='Gone hammer')"), "items from removed drawers go to Unsorted")

            print("sync (fake Supabase)")
            fake = FakeSupabase()
            sctx = [br.new_context() for _ in range(2)]
            pages = []
            for c in sctx:
                c.route(re.compile(r"https://fake\.supabase\.co/.*"), fake.handle)
                pg = c.new_page(); watch_errors(pg, errs)
                pg.goto(base + "/t1.html")
                pg.evaluate("localStorage.setItem(SYNC_KEY,JSON.stringify({url:'https://fake.supabase.co',key:'test',room:'smoke'}));setMe('Dev');syncStart()")
                pg.wait_for_timeout(400)
                pages.append(pg)
            a, z = pages
            a.evaluate("const it=newItem('Synced caliper');addTo('w3-d1',it);log('add',it,1,{});save()")
            a.wait_for_timeout(1700)
            z.evaluate("syncNow()"); z.wait_for_timeout(400)
            check(z.evaluate("S.items['w3-d1'].some(x=>x.t==='Synced caliper')"), "change on device A reaches device B")
            # concurrent edits: both logs survive
            a.evaluate("log('edit',{t:'from A'},1,{});save()")
            z.evaluate("log('edit',{t:'from B'},1,{});save()")
            a.wait_for_timeout(1700); z.wait_for_timeout(300)
            a.evaluate("syncNow()"); a.wait_for_timeout(400)
            z.evaluate("syncNow()"); z.wait_for_timeout(400)
            la = a.evaluate("S.log.map(x=>x.t)")
            check("from A" in la and "from B" in la, "concurrent log entries from both devices kept")
            check("synced" in a.inner_text("#syncst"), "sync status shows synced")
            for c in sctx:
                c.close()

            check(not errs, "no page errors" + (": " + "; ".join(errs[:3]) if errs else ""))
            br.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'FAILED: ' + str(len(FAILS)) if FAILS else 'all passed'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
