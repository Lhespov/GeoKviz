# -*- coding: utf-8 -*-
import json, re

F="C:/Users/andra/claude/geo-quiz.html"
s=open(F,encoding="utf-8").read()

# ---- agent-provided coords + descriptions (29 new) ----
new=json.loads(open("C:/Users/andra/claude/_keva_desc.json",encoding="utf-8").read())
ND={d["key"]:d for d in new}
# small ekavian / wording fixes
ND["krit"]["desc"]=ND["krit"]["desc"].replace("kolijevka","kolevka")
ND["island"]["desc"]=ND["island"]["desc"].replace("Severnom svetlu","severnoj svetlosti")

# ---- keva feature table: (id, key, sr, type, gref) ----
# id 188-216 new (geometry exists), 217-226 duplicates (gref to existing id)
KEVA=[
 # peninsulas 188-197
 (188,"skandinavsko","Skandinavsko poluostrvo","peninsula",None),
 (189,"jiland","Jiland","peninsula",None),
 (190,"balkansko","Balkansko poluostrvo","peninsula",None),
 (191,"apeninsko","Apeninsko poluostrvo","peninsula",None),
 (192,"pirinejsko","Pirinejsko poluostrvo","peninsula",None),
 (193,"korejsko","Korejsko poluostrvo","peninsula",None),
 (194,"malajsko","Malajsko poluostrvo","peninsula",None),
 (195,"indijsko","Indijsko poluostrvo","peninsula",None),
 (196,"somalijsko","Somalijsko poluostrvo","peninsula",None),
 (197,"tunisko","Tunisko poluostrvo","peninsula",None),
 # islands 198-207
 (198,"britanija","Britanija","island",None),
 (199,"irska","Irska","island",None),
 (200,"island","Island","island",None),
 (201,"sicilija","Sicilija","island",None),
 (202,"sardinija","Sardinija","island",None),
 (203,"rodos","Rodos","island",None),
 (204,"lezbos","Lezbos","island",None),
 (205,"krit","Krit","island",None),
 (206,"madagaskar","Madagaskar","island",None),
 (207,"papua","Papua Nova Gvineja","island",None),
 # rivers 208-216
 (208,"volga","Volga","river",None),
 (209,"neva","Neva","river",None),
 (210,"visla","Visla","river",None),
 (211,"zapadna_dvina","Zapadna Dvina","river",None),
 (212,"temza","Temza","river",None),
 (213,"loara","Loara","river",None),
 (214,"gvadalkivir","Gvadalkivir","river",None),
 (215,"arkanzas","Arkanzas","river",None),
 (216,"tenesi","Tenesi","river",None),
]
# duplicates 217-226 : (id, sr, en, lat, lng, type, gref, desc)
DUP=[
 (217,"Florida","Florida",28.0,-81.5,"peninsula",78,"Poluostrvo na jugoistoku SAD, između Meksičkog zaliva i Atlantskog okeana, poznato po toploj klimi i močvarama Everglejdsa."),
 (218,"Jork (poluostrvo)","Cape York Peninsula",-13.5,142.5,"peninsula",178,"Veliko poluostrvo na severoistoku Australije, pruža se prema Toresovom moreuzu i Novoj Gvineji."),
 (219,"Fidži","Fiji",-17.7,178.0,"island",154,"Ostrvska država u jugozapadnom Tihom okeanu, sastoji se od više stotina vulkanskih ostrva."),
 (220,"Tasmanija","Tasmania",-42.0,147.0,"island",149,"Ostrvo na jugu Australije, odvojeno Basovim moreuzom, poznato po netaknutoj prirodi."),
 (221,"Mari","Murray River",-34.5,142.0,"river",167,"Najduža reka Australije, izvire u Australijskim Alpima i uliva se u Indijski okean."),
 (222,"Darling","Darling River",-32.0,142.0,"river",168,"Najduža pritoka reke Mari, teče kroz istočnu Australiju."),
 (223,"Marambidži","Murrumbidgee River",-35.0,146.0,"river",169,"Pritoka reke Mari u jugoistočnoj Australiji."),
 (224,"Misisipi","Mississippi River",32.0,-91.0,"river",102,"Najveći rečni sistem Severne Amerike, teče kroz SAD i uliva se u Meksički zaliv."),
 (225,"Mizuri","Missouri River",41.0,-96.0,"river",103,"Najduža reka Severne Amerike, najveća pritoka Misisipija."),
 (226,"Ohajo","Ohio River",38.7,-85.2,"river",107,"Leva pritoka reke Misisipi, na istoku SAD."),
]

# ---- build DATA rows + DESC + GREF ----
def esc(t): return t.replace('"','\\"')
data_rows=[]; desc_rows=[]; gref={}
for fid,key,sr,typ,_ in KEVA:
    d=ND[key]
    data_rows.append(f'  ["{esc(sr)}","{esc(d["en"])}",{d["lat"]},{d["lng"]},"kv","{typ}"],')
    desc_rows.append(f'{fid}:"{esc(d["desc"])}",')
for fid,sr,en,lat,lng,typ,gr,desc in DUP:
    data_rows.append(f'  ["{esc(sr)}","{esc(en)}",{lat},{lng},"kv","{typ}"],')
    desc_rows.append(f'{fid}:"{esc(desc)}",')
    gref[fid]=gr

# ---- peninsula geometry (custom polygons) 188-197 ; [lat,lng] ----
PEN={
188:[[71.1,25.8],[69.5,30.0],[65.8,24.1],[60.6,17.1],[59.3,18.1],[56.2,15.6],[55.4,13.0],[58.0,11.2],[59.0,5.0],[62.5,5.0],[66.0,12.0],[68.5,15.0],[70.0,19.0]],
189:[[57.6,10.5],[57.0,8.2],[55.6,8.1],[54.9,8.3],[54.8,9.4],[55.5,10.6],[56.7,10.6],[57.4,10.5]],
190:[[46.0,13.6],[45.2,19.1],[44.6,22.7],[43.7,28.6],[41.0,29.0],[40.6,26.2],[37.0,23.5],[36.4,22.5],[38.0,20.3],[40.5,19.3],[42.1,18.5],[43.5,15.5],[45.3,14.5]],
191:[[45.7,7.0],[44.4,8.9],[43.8,10.3],[41.9,12.4],[40.8,14.2],[38.9,16.0],[37.9,15.6],[40.0,18.5],[41.9,16.0],[43.6,13.5],[44.8,12.3],[45.6,13.6],[45.8,9.0]],
192:[[43.8,-7.9],[43.4,-1.8],[42.4,3.2],[40.0,0.2],[37.6,-0.7],[36.7,-2.2],[36.0,-5.6],[37.2,-7.4],[37.0,-8.9],[39.4,-9.4],[41.9,-8.8]],
193:[[43.0,130.5],[39.0,127.5],[35.5,129.4],[34.3,126.5],[37.0,125.5],[39.8,124.4],[41.5,126.9]],
194:[[10.5,99.0],[7.8,98.3],[5.4,100.2],[2.5,101.3],[1.3,103.6],[3.8,103.4],[6.5,102.0],[9.5,99.9]],
195:[[23.0,70.0],[19.0,72.8],[15.0,74.0],[8.1,77.5],[13.1,80.3],[17.7,83.3],[21.5,87.0],[22.0,78.0]],
196:[[12.0,43.5],[11.5,48.0],[11.83,51.28],[7.0,49.5],[2.0,45.3],[0.0,42.5],[4.0,42.0],[8.0,43.0]],
197:[[37.35,10.1],[37.08,11.04],[36.45,11.0],[36.4,10.5],[36.8,10.2]],
}
pen_parts=[]
for fid in sorted(PEN):
    pen_parts.append(f'{fid}:'+json.dumps({"m":"poly","c":[PEN[fid]]},separators=(',',':')))

# islands+rivers geo from extraction
extr=open("C:/Users/andra/claude/_keva_geo.js",encoding="utf-8").read().strip()
keva_geo=",\n".join(pen_parts)+",\n"+extr

# ---- INSERT into file ----
# 1) DATA
ds=s.index("const DATA = [")
de=s.index("\n];", ds)
block_data="\n  // ---------- KEVA (poseban skup za prijatelja) ----------\n"+"\n".join(data_rows)
s=s[:de]+block_data+s[de:]

# 2) DESC
ps=s.index("const DESC = {")
pe=s.index("\n};", ps)
block_desc="\n// KEVA opisi\n"+"\n".join(desc_rows)
s=s[:pe]+block_desc+s[pe:]

# 3) GEO  (one big line ending with '};' before </script>)
gs=s.index("const GEO = {")
scr=s.index("</script>", gs)
close=s.rfind("};", gs, scr)
s=s[:close]+",\n/*KEVA*/\n"+keva_geo+"\n"+s[close:]

# 4) GREF const — insert right after GEO_FIX line
gf=s.index("const GEO_FIX=")
gfe=s.index("\n", gf)
gref_js="\nconst GREF="+json.dumps(gref,separators=(',',':'))+"; // keva duplikati dele geometriju sa postojećim pojmovima"
s=s[:gfe]+gref_js+s[gfe:]

open(F,"w",encoding="utf-8").write(s)
print("DATA rows added:",len(data_rows))
print("DESC rows added:",len(desc_rows))
print("GREF:",gref)
print("peninsula geo:",len(pen_parts))
