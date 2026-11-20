"""Shared settings schema: every exposed option has a runtime consumer."""
# (key, choices); bool choices are displayed as translated on/off values.
TABS = (
    ('DISPLAY', (
        ('fullscreen', (False, True)),
        ('resolution', ((0, 0), (960, 540), (1024, 768), (1280, 720), (1280, 800), (1440, 900), (1600, 900), (1680, 1050), (1920, 1080), (1920, 1200), (2560, 1440))),
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
        ('radar_sweep', (False, True)),
        ('damage_numbers', (False, True)),
        ('notifications', (False, True)),
        ('hud_stats', (False, True)),
    )),
    ('GRAPHICS', (
        ('terrain_quality', ('low', 'medium', 'high')),
        ('biome_blend', (120, 220, 340)),
        ('terrain_shading', (False, True)),
        ('decoration_density', (0.25, 0.5, 1)),
        ('animated_decorations', (False, True)),
        ('entity_shadows', (False, True)),
        ('minimap_pickups', (False, True)),
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
    'minimap': True, 'radar_sweep': True,
    'damage_numbers': True, 'notifications': True,
    'hud_stats': True, 'camera_smoothing': 8, 'camera_lookahead': 60,
    'menu_animations': True, 'crosshair': False, 'notification_duration': 2.5,
    'terrain_quality': 'medium', 'biome_blend': 220, 'terrain_shading': True,
    'decoration_density': 1, 'animated_decorations': True,
    'entity_shadows': True, 'minimap_pickups': True,
    'first_launch': True,
}


def valid_value(key, value):
    if key == 'resolution':
        if isinstance(value, (list, tuple)) and list(value) == [0, 0] and all(type(n) is int for n in value):
            return True
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
