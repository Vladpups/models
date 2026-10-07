#!/usr/bin/env bash
# Полный пайплайн: Meshy GLB -> лоуполи 5000 tris -> запекание -> риг Mixamo -> экспорт.
# Нужен Python 3.13 с пакетами: bpy==5.2.2 numpy pillow xatlas
# Использование: ./run.sh <meshy.glb> <mixamo_anim.fbx> <рабочая папка>
set -euo pipefail
GLB="$1"; FBX="$2"; W="$3"
PY="${PY:-python3}"
D="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$W"
"$PY" "$D/s1_lowpoly.py"   -- "$GLB" "$W/s1.blend"                    # чистка, вырезание изнанки, децимация, UV (xatlas)
"$PY" "$D/s2_bake.py"      -- "$W/s1.blend" "$W/raw" "$W/s2.blend"    # запекание хайполи -> лоуполи (Cycles)
"$PY" "$D/s2b_textures.py" -- "$W/s2.blend" "$W/raw" "$W/tex"         # финальные текстуры, заливка швов
"$PY" "$D/s3_rig.py"       -- "$W/s2.blend" "$FBX" "$W/s3.blend"      # скелет Mixamo, веса
"$PY" "$D/s4_export.py"    -- "$W/s3.blend" "$W/tex" "$W/out"         # FBX, GLB, blend
"$PY" "$D/verify.py"       -- "$W/out" "$FBX"                         # проверка совместимости с Mixamo
