import os,json
from pathlib import Path
w=Path(os.environ["MARGARET_WORK"])
root=Path("/Applications/BambuStudio.app/Contents/Resources/profiles/BBL")
def preset(kind,name):
    d=json.loads((root/kind/(name+".json")).read_text())
    data=preset(kind,d["inherits"]) if "inherits" in d else {}
    for template in d.get("include",[]):
        data.update({k:v for k,v in preset(kind,template).items() if k not in {"type","instantiation","name","from","setting_id","description"}})
    data.update(d)
    data.pop("inherits",None)
    data.pop("include",None)
    return data
m=preset("machine","Bambu Lab P2S 0.4 nozzle")
p=preset("process","0.16mm Standard @BBL P2S")
f=preset("filament","Bambu PLA Basic @BBL P2S")
m["printer_settings_id"]=m["name"]
p["print_settings_id"]=p["name"]
p.update(wall_generator="arachne",wall_loops="2",sparse_infill_density="7%",enable_support="1",support_type="normal(auto)",support_on_build_plate_only="1",support_threshold_angle="38",brim_type="no_brim",enable_prime_tower="1",prime_tower_width="32",
         wipe_tower_x=["216"],wipe_tower_y=["24"],curr_bed_type="Textured PEI Plate")
# rev 17: a multi-plate project needs one prime-tower position per plate
n=len(json.loads((w/"plate.json").read_text())["plates"]) if (w/"plate.json").exists() else 1
p.update(wipe_tower_x=["216"]*n,wipe_tower_y=["24"]*n)
for n,d in [("machine",m),("process",p)]: (w/(n+".json")).write_text(json.dumps(d))
for i,col in enumerate(["#F6F5EE","#15499D","#173347","#BF8A54"],1):
    d=dict(f,filament_colour=[col],default_filament_colour=[col],filament_settings_id=[f["name"]])
    (w/f"f{i}.json").write_text(json.dumps(d))
