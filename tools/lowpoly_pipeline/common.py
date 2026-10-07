# Shared helpers: character config loading (LP_CFG env var -> python file)
import importlib.util, os
def load_cfg():
    path = os.environ.get('LP_CFG')
    assert path, 'set LP_CFG to a character config file (configs/*.py)'
    spec = importlib.util.spec_from_file_location('lp_cfg', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
def smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0); return t * t * (3 - 2 * t)
def band(x, a, b, f):  # 1 inside [a,b], smooth falloff of width f outside
    if x < a: return 1 - smoothstep(0, f, a - x)
    if x > b: return 1 - smoothstep(0, f, x - b)
    return 1.0
