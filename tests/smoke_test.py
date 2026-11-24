"""LabLayout smoke tests (headless Chromium via Playwright).

    pip install playwright && python -m playwright install chromium
    python tests/smoke_test.py

Covers: builder load/export, undo/redo, multi-select + align, custom library
pieces, re-export keeping data, tracker backup/restore, reorder list, due
dates/overdue, and two-device sync against an in-memory fake Supabase.
"""
import functools, http.server, json, pathlib, re, shutil, sys, tempfile, threading, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "site"
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


def embedded_copies():
    """builder.html carries its own copy of the tracker template and the library packs."""
    print("embedded copies")
    b = (DIST / "builder.html").read_text(encoding="utf-8")
    tpl = re.search(r'<script type="text/plain" id="tpl-tracker">(.*?)</script>', b, re.S).group(1).replace("<//script", "</script")
    check(tpl == (DIST / "example-tracker.html").read_text(encoding="utf-8"), "tracker template in builder.html matches example-tracker.html")
    packs = json.loads(re.search(r'<script type="application/json" id="lib-packs">(.*?)</script>', b, re.S).group(1))
    files = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "library").glob("*.json"))]
    check(packs == files, "built-in library in builder.html matches library/*.json")


def main():
    embedded_copies()
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
            b.click("details.menu summary"); b.click("#bEx")
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
            check(not b.frame_locator("#usef").locator("#bCB").is_visible(), "Inventory view has only one colour-blind button")
            b.click("#mEdit")
            b.click("#bUnits")
            check(b.evaluate("[MET(),fmtLen(10),Math.abs(parseLen('3 m')-9.8425)<1e-3,Math.abs(parseLen('2')-6.5617)<1e-3]") == [True, "3.048 m", True, True], "metric display and entry")
            b.click("#bUnits")
            cases = {"45 in":3.75,"45in":3.75,"1/2 in":1/24,"3 1/2 ft":3.5,"5' 6\"":5.5,"5 ft 6 in":5.5,"5 6":5.5,"30 cm":30/30.48,"3/5 cm":.6/30.48,"1.2 m":120/30.48,"1 m 20 cm":120/30.48,"2.5":2.5,"-6 in":-.5,"abc":None,"1/0 in":None}
            got = b.evaluate("(c=>Object.fromEntries(Object.keys(c).map(k=>[k,parseLen(k)])))(%s)" % __import__('json').dumps(cases))
            bad = [k for k,v in cases.items() if (v is None) != (got[k] is None) or (v is not None and abs(got[k]-v) > 1e-6)]
            check(not bad, "lengths accept in/ft/cm/m, fractions and mixed units " + (str([(k,got[k]) for k in bad]) if bad else ""))
            b.evaluate("UU=JSON.stringify(P.units);P.units=[];addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),3,3);select(P.units[0].id)")
            b.fill("#pw", "45 in"); b.press("#pw", "Tab")
            check(b.evaluate("P.units[0].w===3.75&&$('pw').value==='3.75'&&/45 in → 3' 9\" = 1.143 m/.test($('toast').textContent)"), "typing 45 in converts to feet and shows the metric too")
            b.fill("#pw", "30cm"); b.press("#pw", "Tab"); b.fill("#pfw", "30 cm"); b.press("#pfw", "Tab")
            check(b.evaluate("!MET()&&Math.abs(P.units[0].w-30/30.48)<1e-3&&Math.abs(P.units[0].front.W-30/2.54)<1e-2"), "in feet mode, 30cm works in footprint and front-view boxes")
            b.evaluate("select(null);P.units=JSON.parse(UU);draw()")
            b.evaluate("goRoom(1)"); b.click("#bRoomDel"); b.click("#bRoomDel")
            check(b.evaluate("PROJ.rooms.length") == 1, "room can be deleted")
            check(b.evaluate("(()=>{const r=JSON.parse(JSON.stringify(P));const n=importRooms({lablayout_room:1,room:r});const ok=PROJ.rooms.length===2&&P.units.length===r.units.length&&P.storeKey!==PROJ.rooms[0].storeKey;goRoom(1);PROJ.rooms.splice(1,1);PROJ.cur=0;P=PROJ.rooms[0];init();return n===1&&ok})()"), "room JSON import adds a room with its own inventory key")
            b.set_input_files("#file", files=[{"name": "r.room.json", "mimeType": "application/json", "buffer": b.evaluate("JSON.stringify({lablayout_room:1,room:P})").encode()}]); b.wait_for_timeout(300)
            check(b.evaluate("[PROJ.rooms.length,P.units.length]") == [1, n0], "Import layout JSON also opens a room JSON")
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
            # drag-to-stretch walls, click into line with other walls, move the room
            b.evaluate("P0=JSON.parse(JSON.stringify(P.room.poly));U0=JSON.stringify(P.units);P.room.poly=[[0,0],[14,0],[14,10],[8,10],[8,20],[0,20]];fit();startEdit()")
            def scr(x, y):
                return b.evaluate(f"(()=>{{const a=toScreen({x},{y}),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]}})()")
            def mdrag(p0, p1):
                b.mouse.move(*p0); b.mouse.down(); b.mouse.move((p0[0]+p1[0])/2, (p0[1]+p1[1])/2); b.mouse.move(*p1); b.mouse.up()
            mdrag(scr(8, 18), scr(13.93, 18))
            check(b.evaluate("JSON.stringify(P.room.poly)")=="[[0,0],[14,0],[14,20],[0,20]]", "dragging a wall stretches it, clicks into line and merges the leftover corners")
            b.evaluate("P.room.poly=[[0,0],[14,0],[14,10],[8,10],[8,20],[0,20]];draw()")
            mdrag(scr(8, 18), scr(10.6, 18))
            check(b.evaluate("P.room.poly[3][0]===11&&P.room.poly[4][0]===11"), "a dragged wall snaps to the grid")
            mdrag(scr(4, 5), scr(7, 7))
            check(b.evaluate("P.room.poly[0][0]===3&&P.room.poly[0][1]===2"), "dragging the floor in Edit walls moves the whole room")
            b.evaluate("P.room.poly=[[0,0],[14,0],[14,10],[8,10],[8,20],[0,20]];draw()")
            mdrag(scr(14, 10), scr(0.15, 10.3))
            check(b.evaluate("P.room.poly[2][0]===0"), "a dragged corner snaps onto another wall")
            b.evaluate("exitEdit();P.room.poly=P0;P.units=JSON.parse(U0);draw()")
            check(b.evaluate("/Grid: /.test($('bGrid').textContent)"), "grid button shows the grid size")
            # anchoring stops accidental moves
            b.evaluate("P0=JSON.parse(JSON.stringify(P.room.poly));U0=JSON.stringify(P.units);P.room.poly=[[0,0],[14,0],[14,12],[0,12]];P.units=[];draw()")
            b.evaluate("addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),5,5)")
            b.evaluate("select(P.units[0].id)"); b.click("#bLock")
            check(b.evaluate("P.units[0].locked===true&&$('bLock').textContent.includes('Anchored')&&getComputedStyle(document.querySelector('.u.locked rect.b')).stroke==='rgb(45, 108, 223)'&&!document.querySelector('.u.locked text.anc')"), "anchored piece gets a blue outline (no badge)")
            x0 = b.evaluate("[P.units[0].x,P.units[0].y,P.units[0].w]")
            c = b.evaluate("(()=>{const u=P.units[0],a=toScreen(u.x+u.w/2,u.y+u.d/2),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]})()")
            b.mouse.move(*c); b.mouse.down(); b.mouse.move(c[0]+60, c[1]+40); b.mouse.move(c[0]+120, c[1]+80); b.mouse.up()
            b.keyboard.press("ArrowRight"); b.click("#bRot"); b.click("#bDel"); b.click("#bDel")
            check(b.evaluate("[P.units[0].x,P.units[0].y,P.units[0].w]") == x0 and b.evaluate("P.units.length") == 1, "anchored piece can't be dragged, nudged, rotated or deleted")
            b.click("#bLock"); b.keyboard.press("ArrowRight")
            check(b.evaluate("P.units[0].locked") is None and b.evaluate("P.units[0].x") == x0[0] + .25, "unanchoring lets it move again")
            # multi-select: ctrl-click, then rotate / duplicate / anchor / delete the group
            b.evaluate("P.units=[];addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),3,3);addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),9,3);select(null)")
            for i in range(2):
                c = b.evaluate("(()=>{const u=P.units[%d],a=toScreen(u.x+u.w/2,u.y+u.d/2),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]})()" % i)
                b.keyboard.down("Control"); b.mouse.click(*c); b.keyboard.up("Control")
            check(b.evaluate("selSet.size") == 2, "ctrl-click selects several pieces")
            ws = b.evaluate("P.units.map(u=>u.w)"); b.click("#bRot")
            check(b.evaluate("P.units.map(u=>u.d)") == ws, "rotate turns the whole selection")
            b.click("#bDup")
            check(b.evaluate("P.units.length===4&&selSet.size===2&&[...selSet].every(i=>!['%s','%s'].includes(i))" % tuple(b.evaluate("P.units.slice(0,2).map(u=>u.id)"))), "duplicate copies the whole selection")
            b.click("#bLock")
            check(b.evaluate("[...selSet].every(i=>U(i).locked)"), "anchor applies to every selected piece")
            b.click("#bLock"); b.click("#bDel"); b.click("#bDel")
            check(b.evaluate("P.units.length") == 2, "delete removes the whole selection")
            # groups: select and move together
            b.evaluate("P.units=[];addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),3,3);addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),9,3);addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),3,9);selSet.clear();selSet.add(P.units[0].id);selSet.add(P.units[1].id);selId=P.units[1].id;selChanged()")
            b.keyboard.press("Control+g")
            check(b.evaluate("P.units[0].grp&&P.units[0].grp===P.units[1].grp&&!P.units[2].grp&&!!document.querySelector('.gbox')"), "Ctrl+G groups the selection and outlines the group")
            b.evaluate("select(null)")
            c = b.evaluate("(()=>{const u=P.units[0],a=toScreen(u.x+u.w/2,u.y+u.d/2),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]})()")
            b.mouse.click(*c)
            check(b.evaluate("selSet.size") == 2, "clicking one grouped piece selects the whole group")
            g0 = b.evaluate("P.units.map(u=>u.x)")
            b.keyboard.press("ArrowRight")
            check(b.evaluate("P.units.map(u=>u.x)") == [g0[0]+.25, g0[1]+.25, g0[2]], "a group moves together")
            b.keyboard.press("Control+Shift+g")
            check(b.evaluate("P.units.every(u=>!u.grp)"), "Ctrl+Shift+G ungroups")
            # copy / paste across rooms
            b.evaluate("select(P.units[2].id)"); b.keyboard.press("Control+c")
            b.keyboard.press("Control+v")
            check(b.evaluate("P.units.length===4&&P.units[3].x===P.units[2].x+1&&P.units[3].name===P.units[2].name"), "paste in the same room lands offset")
            b.evaluate("$('bRoomAdd').click()"); b.keyboard.press("Control+v")
            check(b.evaluate("PROJ.cur>0&&P.units.length===1&&!!P.units[0].grid"), "paste into another room")
            b.evaluate("PROJ.rooms.splice(PROJ.cur,1);goRoom(PROJ.cur-1)")
            # measure tool
            b.evaluate("P.units=[];draw()"); b.click("#bMeasure")
            mdown = lambda x, y: b.mouse.click(*b.evaluate(f"(()=>{{const a=toScreen({x},{y}),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]}})()"))
            mdown(0, 0); mdown(14, 0)
            check(b.evaluate("MS&&MS.b&&Math.abs(Math.hypot(MS.b[0]-MS.a[0],MS.b[1]-MS.a[1])-14)<.01&&/14/.test(document.querySelector('.mslbl').textContent)"), "measure tool shows the distance between two points")
            b.keyboard.press("Escape")
            check(b.evaluate("MS===null&&!document.querySelector('.mslbl')"), "Esc leaves the measure tool")
            # room-area corners can be dragged
            b.evaluate("P.units=[];zoneFromPts([[2,2],[8,2],[8,8],[2,8]])")
            h = b.evaluate("(()=>{const r=document.querySelectorAll('.zh')[2].getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
            t2 = b.evaluate("(()=>{const a=toScreen(11,6),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]})()")
            b.mouse.move(*h); b.mouse.down(); b.mouse.move((h[0]+t2[0])/2, (h[1]+t2[1])/2); b.mouse.move(*t2); b.mouse.up()
            check(b.evaluate("(u=>u.poly&&u.w===9&&Math.abs(zonePts(u)[2][0]-11)<.01&&Math.abs(zonePts(u)[2][1]-6)<.01)(P.units[0])"), "dragging a room-area corner reshapes it")
            b.evaluate("select(P.units[0].id);renderProps()"); b.select_option("#pasg","blocked")
            check(b.evaluate("(u=>u.assign==='blocked'&&asgLabel(u).endsWith('blocked off')&&document.querySelector('.u.zonep path.b').getAttribute('fill-opacity')==='0.88')(P.units[0])"), "a room area can be blocked off (blacked out)")
            b.evaluate("select(P.units[0].id);draw()")
            check(b.evaluate("document.querySelectorAll('.zcl').length===zonePts(P.units[0]).length"), "a selected room shows its corner coordinates")
            b.click(".zcl[data-zv='1']"); b.fill("#dimin", "9, 3"); b.press("#dimin", "Enter")
            check(b.evaluate("(p=>Math.abs(p[0]-9)<.001&&Math.abs(p[1]-3)<.001)(zonePts(P.units[0])[1])"), "clicking a corner lets you type it exactly")
            b.evaluate("P.units=[];addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),3,3);addFromLib(allLib().flatMap(c=>c.items).find(i=>i.kind==='storage'),9,3);select(P.units[0].id)")
            b.click(".swatches [data-col='#455a64']")
            check(b.evaluate("P.units[0].mapColor==='#455a64'&&P.units[0].mapTextColor==='#eeeeee'"), "a swatch recolours furniture with readable text")
            b.evaluate("selSet.add(P.units[1].id);selChanged()"); b.click(".swatches [data-col='#a5d6a7']")
            check(b.evaluate("P.units.every(u=>u.mapColor==='#a5d6a7')"), "colour applies to every selected piece")
            b.evaluate("select(null);P.room.poly=P0;P.units=JSON.parse(U0);draw()")
            # interior walls enclose rooms automatically; click-a-space fills one
            b.evaluate("P.units=[];P.autoSig=null;const w=allLib().flatMap(c=>c.items).find(i=>i.kind==='wall');addFromLib(w,3,3);const u=P.units[0];u.x=7;u.y=0;u.w=.5;u.d=20;commit('Wall')")
            check(b.evaluate("P.units.filter(u=>u.kind==='zone').length===2"), "a wall splitting the floor makes two rooms automatically")
            b.evaluate("P.units=[{id:'w1',kind:'wall',mapOnly:true,name:'W',x:7.1,y:0,w:.4,d:4},{id:'d1',kind:'door',mapOnly:true,name:'D',x:7.1,y:4,w:.4,d:3},{id:'w3',kind:'wall',mapOnly:true,name:'W',x:7.1,y:7,w:.4,d:3},{id:'w2',kind:'wall',mapOnly:true,name:'W',x:0,y:10,w:14,d:.5}];P.autoSig=null;commit('x')")
            check(b.evaluate("JSON.stringify(P.units.filter(u=>u.kind==='zone').map(z=>[z.x,z.y,z.w,z.d]).sort())") == "[[0,0,7.1,10],[0,10.5,14,9.5],[7.5,0,6.5,10]]", "auto rooms follow wall faces and doorways keep rooms apart")
            b.evaluate("P.units.find(u=>u.kind==='zone'&&u.x===0&&u.y===0).name='Office';P.units.find(u=>u.id==='w2').y=9;P.units.find(u=>u.id==='w3').d=2;commit('x')")
            check(b.evaluate("(z=>z&&z.d===9)(P.units.find(u=>u.name==='Office'))"), "moving a wall reshapes its auto room and keeps the name")
            b.evaluate("P.units=[{id:'w1',kind:'wall',mapOnly:true,name:'W',x:7,y:0,w:.5,d:20}];P.autoSig=null;commit('x')")
            b.evaluate("P.units=P.units.filter(u=>u.kind!=='zone');draw()"); b.click("#bZFill")
            b.mouse.click(*b.evaluate("(()=>{const a=toScreen(3,10),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]})()"))
            check(b.evaluate("(z=>z&&z.x===0&&z.w===7&&z.d===20)(P.units.find(u=>u.kind==='zone'))"), "clicking a space bounded by walls makes it a room")
            b.click("#bZFill")
            b.evaluate("select(null);P.room.poly=P0;P.units=JSON.parse(U0);P.autoSig=null;draw()")
            # nested layouts: an area opens its own room; inventory clicks go in and back out
            b.evaluate("P.units=[];P.autoSig='x';zoneFromPts([[1,1],[7,1],[7,9],[1,9]]);P.units[0].name='Lab A';select(P.units[0].id);renderProps()")
            b.click("#bLinkNew")
            check(b.evaluate("(t=>t&&t.title==='Lab A'&&JSON.stringify(t.room.poly)==='[[0,0],[6,0],[6,8],[0,8]]')(roomByRid(P.units[0].link))"), "an area can become its own room, shaped like the area")
            b.click("#bLinkGo"); b.click("#mUse"); b.wait_for_timeout(500)
            check(b.evaluate("P.title")=="Lab A" and "Lab A" in b.frame_locator("#usef").locator("#crumbs").inner_text(), "inside a linked room the breadcrumb shows the layout above it")
            bx = b.frame_locator("#usef").locator("#map").bounding_box(); b.mouse.click(bx["x"]+3, bx["y"]+3); b.wait_for_timeout(600)
            check(b.evaluate("P.title")!="Lab A", "clicking outside the room in inventory goes back to the layout")
            b.frame_locator("#usef").locator("#map path.zgo").first.click(); b.wait_for_timeout(600)
            check(b.evaluate("P.title")=="Lab A", "clicking an area in inventory goes into its room")
            b.click("#mEdit"); b.evaluate("const i=PROJ.rooms.findIndex(r=>r.title==='Lab A');PROJ.rooms.splice(i,1);goRoom(0);select(null);P.room.poly=P0;P.units=JSON.parse(U0);P.autoSig=null;draw()")
            # mark rooms / areas: drag a box, or draw a polygon like walls
            b.evaluate("P0=JSON.parse(JSON.stringify(P.room.poly));U0=JSON.stringify(P.units);P.room.poly=[[0,0],[20,0],[20,14],[0,14]];P.units=[];syncPoly();fit()")
            def zs(x, y):
                return b.evaluate(f"(()=>{{const a=toScreen({x},{y}),r=$('stage').getBoundingClientRect();return [a.x+r.left,a.y+r.top]}})()")
            b.click("#bZRect"); p0, p1 = zs(0.1, 0.1), zs(8, 6)
            b.mouse.move(*p0); b.mouse.down(); b.mouse.move((p0[0]+p1[0])/2, (p0[1]+p1[1])/2); b.mouse.move(*p1); b.mouse.up()
            check(b.evaluate("(u=>u.kind==='zone'&&u.x===0&&u.y===0&&u.w===8&&u.d===6&&!u.poly)(P.units[0])"), "drag a box marks a rectangular area")
            b.click("#bZone")
            for x, y in [(10, 0), (20, 0), (20, 14), (14, 14), (14, 7), (10, 7)]:
                b.mouse.click(*zs(x, y))
            b.keyboard.press("Enter")
            check(b.evaluate("(u=>u.kind==='zone'&&u.poly.length===6&&u.x===10&&u.w===10&&u.d===14)(P.units[0])"), "draw area makes an L-shaped zone snapped to the walls")
            check(b.evaluate("document.querySelectorAll('.u.zonep path.b').length===P.units.filter(u=>u.kind==='zone').length"), "room areas render as shapes")
            b.evaluate("select(P.units[0].id);renderProps()"); b.select_option("#pasg","ours")
            check(b.evaluate("P.units[0].assign==='ours'&&asgColor(P.units[0])==='#cfe0f7'&&asgLabel(P.units[0]).endsWith('ours only')"), "a room can be marked strictly ours")
            b.evaluate("select(null);P.room.poly=P0;P.units=JSON.parse(U0);syncPoly();draw()")
            # colour-blind mode
            b.click("#bCB")
            check(b.evaluate("cbOn()&&getComputedStyle($('bDel')).color==='rgb(213, 94, 0)'"), "colour-blind mode swaps red for vermillion")
            b.click("#bCB")
            check(b.evaluate("!cbOn()&&getComputedStyle($('bDel')).color==='rgb(198, 40, 40)'"), "colour-blind mode turns back off")
            # doorways snap into walls and show their swing
            b.evaluate("P0=JSON.parse(JSON.stringify(P.room.poly));U0=JSON.stringify(P.units);P.room.poly=[[0,0],[14,0],[14,12],[0,12]];P.units=[];draw()")
            b.evaluate("addFromLib(allLib().flatMap(c=>c.items).find(i=>i.k==='door'),5,0.6)")
            check(b.evaluate("(u=>u.y===-0.2&&u.w===3&&u.d===0.4)(P.units[0])"), "a door dropped near a wall snaps into it")
            b.evaluate("addFromLib(allLib().flatMap(c=>c.items).find(i=>i.k==='door2'),13.5,6)")
            check(b.evaluate("(u=>u.x===13.8&&u.d===6&&u.dtype==='double')(P.units[1])"), "a double door turns to fit a side wall")
            check(b.evaluate("document.querySelectorAll('.u.door path').length===3"), "doors draw their swing arcs (1 single + 2 double)")
            b.evaluate("select(P.units[0].id)"); b.click("#bSwing"); b.click("#bHinge")
            check(b.evaluate("P.units[0].out===true&&P.units[0].hinge==='b'"), "swing direction and hinge side can be flipped")
            b.click("#mUse"); b.wait_for_timeout(800)
            fr = b.frame_locator("#usef")
            check(fr.locator("#map path.swing").count() == 3, "Inventory map shows door swings too")
            check("14 ft" in fr.locator("#map").text_content(), "doorways don't change the room size label")
            b.click("#mEdit")
            b.evaluate("select(null);P.room.poly=P0;P.units=JSON.parse(U0);draw()")

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
