#!/bin/bash
# Full pipeline: Meshy GLB + Mixamo FBX + reference sheet -> 5k-tri rigged game model
# usage: PY=python ./run_all.sh Meshy.glb Walking.fbx reference.png work_dir out_dir
set -e
D=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python}
GLB=$1; WALK=$2; REF=$3; W=$4; OUT=$5
mkdir -p "$W"
$PY -I "$D/s1_prep.py" "$GLB" "$W/s1.blend" '{"height":1.80}'
$PY -I "$D/s2_gear.py" "$W/s1.blend" "$W/s2g.blend"
$PY -I "$D/s2_decimate.py" "$W/s2g.blend" "$W/s2.blend" ${TRIS:-4824} '{"base":0.2,"boost":{"head":0.14,"neck":0.1,"hands":0.28,"wrists":0.2,"elbows":0.28,"shoulders":0.18,"knees":0.2,"shins":0.08,"feet":-0.1,"hips":0.08}}'
$PY -I "$D/s3_uv.py" "$W/s2.blend" "$W/s3.blend" '{"method":"MINIMUM_STRETCH","max_iter":12,"bad_frac":0.2}'
$PY -I "$D/s3b_pack.py" "$W/s3.blend" "$W/s3b.blend" '{"brute":true}'
$PY -I "$D/s4_bake.py" "$W/s3b.blend" "$W/s4.blend" "$W/tex" '{"res":2048,"ss":2,"samples":1,"ao_res":2048,"ao_samples":64}'
$PY -I "$D/s5_material.py" "$W/s4.blend" "$W/s5.blend" "$W/tex"
$PY -I "$D/s5b_project.py" "$W/s5.blend" "$W/tex" "$REF" "$W/s5b.blend" "$W/dbg"
$PY -I "$D/s6_rig.py" "$W/s5b.blend" "$WALK" "$W/s6.blend"
$PY -I "$D/s7_export.py" "$W/s6.blend" "$W/tex" "$OUT"
$PY -I "$D/verify.py" "$OUT" "$WALK"
