
__all__ = [
    'DEFAULT_SKIN',
]


DEFAULT_SKIN = {
    'meta': {
        'name': 'DefaultSkin',
        'author': 'Jorge A. G.',
    },

    'metrics': {
        'image': {
            'skin': {
                'filenames': []
            },
            'iconset': {
                'using': False,
                'filename': "",
                'icon_size': (16, 16),
                'columns': 4,
                'count': 16,         # total number of icons in this set
                'spacing': (0, 0),   # blank space between icons (horizontal and vertical)
                'offset': (0, 0)     # position (top-left corner) of the icon grid inside the image
            },
        },
        'font': {
            'size': {
                'tiny': 9,
                'small': 12,
                'medium': 18,
                'large': 24,
                'huge': 36
            },
            'gui': {
                'is_sysfont': True,
                'name': 'Play',
                'path': '',
            },
            'text': {
                'is_sysfont': True,
                'name': 'Arial',
                'path': '',
            },
            'code': {
                'is_sysfont': True,
                'name': 'CourierNew',
                'path': '',
            }
        },
        'default': {
            'margin': (1, 1, 1, 1),
            'padding': (2, 2, 2, 2),
            'valign': 'MIDDLE',  # read from enum: value = Alignment['MIDDLE']
            'halign': 'CENTER',
            'fit': False,   # resize to fit
            'erase_color': (255, 255, 255),
        },
    },
    'PushButton': {
        'size': (60, 20),
        'method': 'render_pushbutton',
        'image_index': 0,
        'image_border': (2, 2, 2, 2),
        'erase_background': True,
        'render_layers': ('BACKGROUND', 'ABOVE_BACKGROUND', 'FOREGROUND'),
        'style': {
            'size': 'medium',
            'valign': 'MIDDLE',
            'halign': 'CENTER',
            'bold': False,
            'italic': False,
            'underline': False,
        },
        'layout': {
            'size': (60, 20),
            'padding': (8, 8, 8, 8),
            'margin': (1, 1, 1, 1),
            'fit': True,
        },
        'normal': {
            'color': (32, 32, 32),
            'backcolor': (232, 232, 232),
            'bordercolor': (32, 32, 32),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'hilighted': {
            'color': (64, 64, 64),
            'backcolor': (255, 255, 255),
            'bordercolor': (0, 0, 0),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'pressed': {
            'color': (32, 32, 32),
            'backcolor': (192, 192, 192),
            'bordercolor': (0, 0, 0),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'disabled': {
            'color': (128, 128, 128),
            'backcolor': (160, 160, 160),
            'bordercolor': (128, 128, 128),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
    },
    'CheckBox': {
        'size': (60, 20),
        'method': 'render_checkbox',
        'image_index': 0,
        'image_border': (2, 2, 2, 2),
        'erase_background': True,
        'render_layers': ('ABOVE_BACKGROUND',),
        'style': {
            'size': 'medium',
            'valign': 'MIDDLE',
            'halign': 'RIGHT',
            'bold': False,
            'italic': False,
            'underline': False,
        },
        'layout': {
            'size': (60, 20),
            'padding': (2, 2, 10, 2),
            'margin': (1, 1, 1, 1),
            'fit': True,
        },
        'normal': {
            'color': (32, 32, 32),
            'checkmark': {
                'color': (0, 96, 0),
                'image_area': (0, 0, 1, 1),
                'image_kind': 'IMK_IMAGE'
            },
            'backcolor': (255, 255, 255),
            'bordercolor': (32, 32, 32),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'hilighted': {
            'color': (32, 32, 32),
            'checkmark': {
                'color': (0, 128, 0),
                'image_area': (0, 0, 1, 1),
                'image_kind': 'IMK_IMAGE'
            },
            'backcolor': (255, 255, 255),
            'bordercolor': (32, 32, 32),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'pressed': {
            'color': (0, 0, 0),
            'checkmark': {
                'color': (0, 64, 0),
                'image_area': (0, 0, 1, 1),
                'image_kind': 'IMK_IMAGE'
            },
            'backcolor': (255, 255, 255),
            'bordercolor': (32, 32, 32),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'disabled': {
            'color': (128, 128, 128),
            'checkmark': {
                'color': (128, 128, 128),
                'image_area': (0, 0, 1, 1),
                'image_kind': 'IMK_IMAGE'
            },
            'backcolor': (160, 160, 160),
            'bordercolor': (128, 128, 128),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
    },
    'Panel': {
        'size': (240, 180),
        'method': 'render_panel',
        'image_index': 0,
        'image_border': (2, 2, 2, 2),
        'erase_background': True,
        'render_layers': ('BACKGROUND', 'ABOVE_BACKGROUND', 'FOREGROUND'),
        'style': {
            'size': 'medium',
            'valign': 'TOP',
            'halign': 'LEFT',
            'bold': False,
            'italic': False,
            'underline': False,
        },
        'layout': {
            'size': (120, 120),
            'padding': (2, 2, 2, 2),
            'margin': (2, 2, 2, 2),
            'fit': True,
        },
        'normal': {
            'color': (128, 128, 128),
            'backcolor': (192, 192, 192),
            'bordercolor': (128, 128, 128),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
        'disabled': {
            'color': (128, 128, 128),
            'backcolor': (160, 160, 160),
            'bordercolor': (128, 128, 128),
            'image_area': (0, 0, 1, 1),
            'image_kind': 'IMK_NINEPATCH'
        },
    },
    'ToggleButton': {
        'size': (60, 20),
        'style': {
            'size': 'medium',
            'valign': 'MIDDLE',
            'halign': 'LEFT',
            'bold': False,
            'italic': False,
            'underline': False,
        },
        'on': {
            'normal': {
                'color': (64, 64, 64),
                'backcolor': (232, 232, 232),
                'bordercolor': (32, 32, 32),
            },
            'hilighted': {
                'color': (0, 0, 0),
                'backcolor': (255, 255, 255),
                'bordercolor': (0, 0, 0),
            },
            'pressed': {
                'color': (0, 0, 0),
                'backcolor': (160, 160, 160),
                'bordercolor': (0, 0, 0),
            },
        },
        'off': {
            'normal': {
                'font_color': (64, 64, 64),
                'backcolor': (232, 232, 232),
                'bordercolor': (32, 32, 32),
            },
            'hilighted': {
                'font_color': (0, 0, 0),
                'backcolor': (255, 255, 255),
                'bordercolor': (0, 0, 0),
            },
            'pressed': {
                'font_color': (0, 0, 0),
                'backcolor': (160, 160, 160),
                'bordercolor': (0, 0, 0),
            },
        },
    },
}
