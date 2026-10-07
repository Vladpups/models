#!/bin/bash
# Full pipeline: Meshy GLB + reference sheet + Mixamo FBX -> 5k-tri game model rigged for Mixamo, face from the reference
# usage: PY=python ./run_all.sh Meshy.glb reference.png Walking.fbx work_dir out_dir
# MediaPipe landmarks are cached in data/; set FACE_MODEL=face_landmarker.task to recompute them.
set -e
D=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python}
GLB=$1; REF=$2; WALK=$3; W=$4; OUT=$5
mkdir -p "$W"
$PY -I "$D/s1_prep.py" "$GLB" "$W/s1.blend" 2.0
if [ -n "$FACE_MODEL" ]; then
  $PY -I "$D/s1a_render_head.py" "$W/s1.blend" "$W/head_front.png"
  $PY -I "$D/facelm.py" "$FACE_MODEL" "$W/head_front.png" 0 0 1000 1000 1 "$W/lm_3d_front.json"
  $PY -I "$D/facelm.py" "$FACE_MODEL" "$REF" 0 690 200 960 3 "$W/lm_ref_front.json"
else
  cp "$D/data/lm_3d_front.json" "$D/data/lm_ref_front.json" "$W/"
fi
$PY -I "$D/s1b_head.py" "$W/s1.blend" "$W/s1b.blend" "$W/lm_3d_front.json" "$W/lm_ref_front.json" \
  '{"center":[0,-0.05,1.84],"size":0.36,"res":1000}' \
  '{"open_r":0.006,"close_r":0.008,"hair_sigma":0.002,"hair_z0":1.89,"hair_z1":1.92,"hair_yf0":-0.15,"hair_yf1":-0.11}'
$PY -I "$D/s1c_lpbase.py" "$W/s1b.blend" "$W/s1c.blend"
$PY -I "$D/s2_decimate.py" "$W/s1c.blend" "$W/s2.blend" ${TRIS:-5000} '{"base":0.2,"boost":{"head":0.25,"face":0.3,"ears":0.1,"neck":0.1,"hands":0.3,"wrists":0.2,"elbows":0.28,"shoulders":0.15,"knees":0.2,"shins":0.05,"feet":-0.15,"hips":0.08,"torso":-0.1}}'
$PY -I "$D/s3_uv.py" "$W/s2.blend" "$W/s3.blend" '{"method":"MINIMUM_STRETCH","max_iter":12,"bad_frac":0.2}'
$PY -I "$D/s3b_pack.py" "$W/s3.blend" "$W/s3b.blend" '{"brute":true}'
$PY -I "$D/s4_bake.py" "$W/s3b.blend" "$W/s4.blend" "$W/tex" '{"res":2048,"ss":2,"samples":1,"ao_res":2048,"ao_samples":64,"extrusion":0.02,"ray":0.045}'
$PY -I "$D/s5_material.py" "$W/s4.blend" "$W/s5.blend" "$W/tex"
$PY -I "$D/s4b_face.py" "$W/s5.blend" "$W/tex" "$REF" "$W/s1b_map.json"
$PY -I "$D/s6_rig.py" "$W/s5.blend" "$WALK" "$W/s6.blend"
$PY -I "$D/s7_export.py" "$W/s6.blend" "$W/tex" "$OUT"
$PY -I "$D/verify.py" "$OUT" "$WALK"
