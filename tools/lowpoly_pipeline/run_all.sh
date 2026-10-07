#!/bin/bash
# Full pipeline: Meshy GLB + Mixamo FBX -> 5k-tri rigged game model.
# Usage: LP_CFG=configs/<character>.py ./run_all.sh Meshy.glb Mixamo_anim.fbx workdir outdir
# Character-specific data (height, decimation zones, UV segments, joints, fingers) lives in the config.
set -e
D=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python}
: "${LP_CFG:?set LP_CFG to a character config, e.g. LP_CFG=$D/configs/soldier.py}"
export LP_CFG=$(cd "$(dirname "$LP_CFG")" && pwd)/$(basename "$LP_CFG")
GLB=$1; ANIM=$2; W=$3; OUT=$4
mkdir -p "$W"
$PY -I "$D/s1_prep.py" "$GLB" "$W/s1.blend"
$PY -I "$D/s2_decimate.py" "$W/s1.blend" "$W/s2.blend"
$PY -I "$D/s3_uv.py" "$W/s2.blend" "$W/s3.blend"
$PY -I "$D/s3b_pack.py" "$W/s3.blend" "$W/s3b.blend"
$PY -I "$D/s4_bake.py" "$W/s3b.blend" "$W/s4.blend" "$W/tex"
$PY -I "$D/s5_material.py" "$W/s4.blend" "$W/s5.blend" "$W/tex"
$PY -I "$D/s6_rig.py" "$W/s5.blend" "$ANIM" "$W/s6.blend"
$PY -I "$D/s7_export.py" "$W/s6.blend" "$W/tex" "$OUT"
