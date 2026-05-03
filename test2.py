from ursina import *
import json, struct, base64, math

# ── Charger et décoder les keyframes du GLTF ──────────────────────────────────

def load_gltf_animations(path):
    with open(path) as f:
        data = json.load(f)

    buf_data = base64.b64decode(data['buffers'][0]['uri'].split(',')[1])
    accessors   = data['accessors']
    bufferViews = data['bufferViews']

    def get_accessor(idx):
        acc = accessors[idx]
        bv  = bufferViews[acc['bufferView']]
        off = bv['byteOffset'] + acc.get('byteOffset', 0)
        n   = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[acc['type']]
        cnt = acc['count']
        vals = struct.unpack_from(f'{cnt*n}f', buf_data, off)
        return list(vals) if n == 1 else [vals[i*n:(i+1)*n] for i in range(cnt)]

    nodes = data['nodes']
    result = {}

    for anim in data['animations']:
        channels = []
        for ch in anim['channels']:
            s = anim['samplers'][ch['sampler']]
            channels.append({
                'node_name': nodes[ch['target']['node']]['name'],
                'path':      ch['target']['path'],
                'times':     get_accessor(s['input']),
                'values':    get_accessor(s['output']),
            })
        result[anim['name']] = {
            'duration': max(ch['times'][-1] for ch in channels),
            'channels': channels,
        }

    return result


def quat_to_euler_x(quat):
    """Convertit un quaternion GLTF (x,y,z,w) en angle X Panda3D (degrés)."""
    x, y, z, w = quat
    sinp = 2 * (w * x - z * y)
    sinp = max(-1.0, min(1.0, sinp))
    return math.degrees(math.asin(sinp))


def lerp_angle(a, b, t):
    return a + (b - a) * t


def sample_channel(ch, time):
    """Interpolation linéaire entre deux keyframes."""
    times  = ch['times']
    values = ch['values']

    if time <= times[0]:
        return values[0]
    if time >= times[-1]:
        return values[-1]

    for i in range(len(times) - 1):
        if times[i] <= time <= times[i+1]:
            t = (time - times[i]) / (times[i+1] - times[i])
            a, b = values[i], values[i+1]
            # Lerp composante par composante
            return tuple(a[j] + (b[j] - a[j]) * t for j in range(len(a)))

    return values[-1]


# ── App Ursina ─────────────────────────────────────────────────────────────────

app = Ursina()

cow = Entity(model='assets/models/cow.gltf', scale=1, position=(0, 0, 0))

# Trouver les nœuds par nom (premiers enfants de chaque groupe)
def find_node(name):
    return cow.find(f'**/{name}')

leg0 = find_node('leg0')
leg1 = find_node('leg1')
leg2 = find_node('leg2')
leg3 = find_node('leg3')
head = find_node('head')

# Charger les animations depuis le fichier
ANIMATIONS = load_gltf_animations('assets/models/cow.gltf')

# État courant
current_anim = 'move'
anim_time    = 0.0
playing      = True

# UI
Text('E = manger  |  M = marcher  |  ESPACE = pause', position=(-0.85, 0.45), scale=1.2)
anim_label = Text('', position=(-0.85, 0.40), scale=1.2, color=color.yellow)


def apply_animation(anim_name, t):
    anim = ANIMATIONS[anim_name]
    for ch in anim['channels']:
        quat = sample_channel(ch, t)
        angle_x = quat_to_euler_x(quat)

        node_name = ch['node_name']
        # On anime chaque patte / la tête selon le canal
        if node_name == 'leg0' and leg0:
            leg0.setP(angle_x)
        elif node_name == 'leg1' and leg1:
            leg1.setP(angle_x)
        elif node_name == 'leg2' and leg2:
            leg2.setP(angle_x)
        elif node_name == 'leg3' and leg3:
            leg3.setP(angle_x)
        elif node_name == 'head' and head:
            head.setP(angle_x)


def update():
    global anim_time, playing

    if not playing:
        return

    anim = ANIMATIONS[current_anim]
    anim_time += time.dt
    if anim_time > anim['duration']:
        anim_time = 0.0  # boucle

    apply_animation(current_anim, anim_time)
    anim_label.text = f'anim: {current_anim}  t={anim_time:.2f}s'


def input(key):
    global current_anim, anim_time, playing

    if key == 'm':
        current_anim = 'move'
        anim_time = 0.0
    elif key == 'e':
        current_anim = 'eat'
        anim_time = 0.0
    elif key == 'space':
        playing = not playing


EditorCamera()
app.run()