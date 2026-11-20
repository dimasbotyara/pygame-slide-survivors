"""Shared settings schema: every exposed option has a runtime consumer."""
# (key, choices); bool choices are displayed as translated on/off values.
TABS = (
    ('DISPLAY', (
        ('fullscreen', (False, True)),
        ('resolution', ((960, 540), (1280, 720), (1600, 900), (1920, 1080), (2560, 1440))),
        ('fps_limit', (30, 60, 90, 120, 144, 165, 240, 0)),
        ('show_fps', (False, True)),
        ('smooth_scaling', (False, True)),
        ('pause_unfocused', (False, True)),
    )),
    ('EFFECTS', (
        ('particle_density', (0, 0.5, 1, 1.5, 2, 3)),
        ('particle_budget', (300, 600, 1200, 2400, 4000)),
        ('screen_shake', (False, True)),
        ('screen_flashes', (False, True)),
        ('slide_trails', (False, True)),
        ('slide_particles', (False, True)),
        ('decorations', (False, True)),
        ('view_culling', (False, True)),
    )),
    ('INTERFACE', (
        ('language', ('ru', 'en')),
        ('minimap', (False, True)),
        ('minimap_biomes', (False, True)),
        ('radar_sweep', (False, True)),
        ('damage_numbers', (False, True)),
        ('notifications', (False, True)),
        ('biome_notifications', (False, True)),
        ('hud_stats', (False, True)),
    )),
    ('CAMERA', (
        ('camera_smoothing', (0, 4, 8, 12, 20)),
        ('camera_lookahead', (0, 30, 60, 90, 120)),
        ('menu_animations', (False, True)),
        ('crosshair', (False, True)),
        ('notification_duration', (1.5, 2.5, 3.5, 5)),
    )),
)

DEFAULTS = {
    'fullscreen': False, 'resolution': (1280, 720), 'fps_limit': 60,
    'show_fps': False, 'smooth_scaling': True, 'pause_unfocused': True,
    'particle_density': 2, 'particle_budget': 2400, 'screen_shake': True,
    'screen_flashes': True, 'slide_trails': True, 'slide_particles': True,
    'decorations': True, 'view_culling': True, 'language': 'ru',
    'minimap': True, 'minimap_biomes': True, 'radar_sweep': True,
    'damage_numbers': True, 'notifications': True, 'biome_notifications': True,
    'hud_stats': True, 'camera_smoothing': 8, 'camera_lookahead': 60,
    'menu_animations': True, 'crosshair': False, 'notification_duration': 2.5,
    'first_launch': True,
}


def valid_value(key, value):
    if key == 'resolution':
        return (isinstance(value, (list, tuple)) and len(value) == 2
                and all(type(n) is int for n in value)
                and 640 <= value[0] <= 7680 and 360 <= value[1] <= 4320)
    if key == 'first_launch':
        return type(value) is bool
    for _, rows in TABS:
        for name, choices in rows:
            if name == key:
                if type(choices[0]) is bool:
                    return type(value) is bool
                return value in choices and not isinstance(value, bool)
    return False
