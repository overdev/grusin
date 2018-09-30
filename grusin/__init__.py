import ast
import io
import sys
import pygame as pg
from collections import OrderedDict
from contextlib import contextmanager
from typing import Any, Tuple, Optional, Union, List, Callable, Dict, Type
from enum import IntFlag, Enum, IntEnum
from skin import DEFAULT_SKIN

DEFAULT = object()

MB_NONE = 0
MB_LEFT = 1
MB_MIDDLE = 2
MB_RIGHT = 3
MB_WHEEL_UP = 4
MB_WHEEL_DOWN = 5

class GrUsInRendererError(Exception):
    pass

class Message(IntEnum):
    # Mouse related
    MOUSE_FIRST = 0x1
    HIT_TEST = MOUSE_FIRST + 0
    MOUSE_ENTER = MOUSE_FIRST + 1
    MOUSE_HOVER = MOUSE_FIRST + 2
    MOUSE_MOVE = MOUSE_FIRST + 3
    MOUSE_PRESS = MOUSE_FIRST + 4
    MOUSE_DOWN = MOUSE_FIRST + 5
    MOUSE_RELEASE = MOUSE_FIRST + 6
    MOUSE_CLICK = MOUSE_FIRST + 7
    MOUSE_STARTDRAG = MOUSE_FIRST + 8
    MOUSE_DRAGMOVE = MOUSE_FIRST + 9
    MOUSE_STOPDRAG = MOUSE_FIRST + 10
    MOUSE_WHEEL = MOUSE_FIRST + 11
    MOUSE_LEAVE = MOUSE_FIRST + 12
    MOUSE_LAST = MOUSE_FIRST + 12

    # Drag 'n' Drop
    DRAG_FIRST = 0x20
    DRAG_ACCEPT = DRAG_FIRST + 0
    DRAG_SENDDATA = DRAG_FIRST + 1
    DRAG_RECVDATA = DRAG_FIRST + 2
    DRAG_LAST = DRAG_FIRST + 2

    # Keyboard related
    KEY_FIRST = 0x40
    KEY_CHAR = KEY_FIRST + 0
    KEY_PRESS = KEY_FIRST + 1
    KEY_DOWN = KEY_FIRST + 2
    KEY_RELEASE = KEY_FIRST + 3
    KEY_LAST = KEY_FIRST + 3

    # Render related
    RENDER_FIRST = 0x60
    INVALIDATED = RENDER_FIRST + 0
    RENDER_BACKGROUND = RENDER_FIRST + 2
    RENDER = RENDER_FIRST + 3
    RENDER_FOREGROUND = RENDER_FIRST + 4
    ERASE_CHILD = RENDER_FIRST + 5
    RENDER_LAST = RENDER_FIRST + 5

    # Control related
    CONTROL_FIRST = 0x80
    DEACTIVATED = CONTROL_FIRST + 0
    ACTIVATED = CONTROL_FIRST + 1
    ADD_CHILD = CONTROL_FIRST + 2
    REMOVE_CHILD = CONTROL_FIRST + 3
    REMOVE_CHILDREN = CONTROL_FIRST + 4
    LAYOUT_CHILDREN = CONTROL_FIRST + 5
    CHILD_INDEX = CONTROL_FIRST + 6
    SELECT = CONTROL_FIRST + 7
    SELECTED = CONTROL_FIRST + 8
    FOCUSED = CONTROL_FIRST + 9
    DEFOCUSED = CONTROL_FIRST + 10
    CREATED = CONTROL_FIRST + 11
    INITIALIZE = CONTROL_FIRST + 12
    TEXTCHANGED = CONTROL_FIRST + 13
    SIZECHANGED = CONTROL_FIRST + 14
    CONTROL_LAST = CONTROL_FIRST + 14

    # App related
    APP_FIRST = 0xA0
    QUIT_REQUEST = APP_FIRST + 0
    QUIT_CANCELED = APP_FIRST + 1
    QUIT_CONFIRMED = APP_FIRST + 2
    APP_LAST = APP_FIRST + 2


class HitTest(Enum):
    NONE = 0
    NONCLIENT = 1
    CLIENT = 2
    CAPTION = 4
    SIZEBORDER = 3
    CRTLBOX = 4


HT_NONE = HitTest.NONE
HT_NONCLIENT = HitTest.NONCLIENT
HT_CLIENT = HitTest.CLIENT
HT_CAPTION = HitTest.CAPTION
HT_SIZEBORDER = HitTest.SIZEBORDER
HT_CRTLBOX = HitTest.CRTLBOX


class LayoutNext(Enum):
    """LayoutNext enumeration.

    Used to control the placement of child controls in the parent's client area. The
    placement is always relative to the current control being placed or to the current
    row of controls placed.
    SAMELINE: places the next control at the left, aligned to the TOP of current control;
    BELLOW: places the next control below the currrent control, LEFT aligned to the
            current control;
    NEWLINE: places the next control at the LEFT of the parent's client area. A row of
             controls has the height of the control with the larger height.
    CASCADE: places the next control 32 pixels to the right and bottom of previous
             control's top-left corner.
    MANUAL: does nothing, as this means the control will be placed in a specific position.
    """
    SAMELINE = 0
    BELOW = 1
    NEWLINE = 2
    CASCADE = 3
    MANUAL = 4


LON_SAMELINE = LayoutNext.SAMELINE
LON_BELOW = LayoutNext.BELOW
LON_NEWLINE = LayoutNext.NEWLINE
LON_CASCADE = LayoutNext.CASCADE
LON_MANUAL = LayoutNext.MANUAL


class RenderLayer(IntFlag):
    """RenderLayer enumeration.

    Used to specify the render stages of a control and wich layer is currently being
    rendered.
    BACKGROUND: normally used to render anything tha goes below its contents.
    ABOVE_BACKGROUND: used to render the control contents before its children, if any.
    BELOW_FOREGROUND: used to render the control contents after its children, if any.
    FOREGROUND: normally used to render anything that goes above its contents.

    Note: ABOVE_BACKGROUND and BELOW_FOREGROUND are mutually exclusive.
    """
    NONE = 0
    BACKGROUND = 1
    ABOVE_BACKGROUND = 2    # immediately after background and immediately before client/nonclient
    BELOW_FOREGROUND = 4    # immediately after client/nonclient and immediately before foreground
    FOREGROUND = 8


RL_NONE = RenderLayer.NONE
RL_BACKGROUND = RenderLayer.BACKGROUND
RL_ABOVE_BACKGROUND = RenderLayer.ABOVE_BACKGROUND
RL_BELOW_FOREGROUND = RenderLayer.BELOW_FOREGROUND
RL_FOREGROUND = RenderLayer.FOREGROUND


class Behavior(IntFlag):
    """Behavior enumeration.

    Used to specify some major control characteristics.
    SELECTABLE: the control can receive focus;
    FIXED_WIDTH: the control's width can't be changed except by its own code.
    FIXED_HEIGHT: the control's height can't be changed except by its own code.
    FIXED_SIZE: the control's size can't be changed except by its own code.
    MODAL: the control can't lose focus unless it's dismissed.
    MODELESS: the control can't be place behind others, even when loses focus.
    NON_CLIENT: the control is a component of it's parent.
    """
    SELECTABLE = 1
    FIXED_WIDTH = 2
    FIXED_HEIGHT = 4
    FIXED_SIZE = FIXED_WIDTH | FIXED_HEIGHT
    MODAL = 8
    MODELESS = 16
    NON_CLIENT = 32


BE_SELECTABLE = Behavior.SELECTABLE
BE_FIXED_WIDTH = Behavior.FIXED_WIDTH
BE_FIXED_HEIGHT = Behavior.FIXED_HEIGHT
BE_FIXED_SIZE = Behavior.FIXED_SIZE
BE_MODAL = Behavior.MODAL
BE_MODELESS = Behavior.MODELESS
BE_NON_CLIENT = Behavior.NON_CLIENT


class Scrollbars(IntFlag):
    """Scrollbars enumeration.

    Used to specify the behavior of scrollbars (its visibility) on scrollable controls.
    AUTO: scrollbars are hidden or shown automatically as needed.
    ALWAYS_VERTICAL: vertical scrollbars never hides
    ALWAYS_HORIZONTAL: horizontal scrollbars never hides
    ALWAYS: scrollbars are always visible
    NEVER_VERTICAL: vertical scrollbars are always hidden
    NEVER_HORIZONTAL: horizontal scrollbars are always hidden
    NEVER: scrollbars are always hidden
    """
    AUTO = 0
    ALWAYS_VERTICAL = 1
    ALWAYS_HORIZONTAL = 2
    ALWAYS = ALWAYS_HORIZONTAL | ALWAYS_VERTICAL
    NEVER_VERTICAL = 4
    NEVER_HORIZONTAL = 8
    NEVER = NEVER_HORIZONTAL | NEVER_VERTICAL


SB_AUTO = Scrollbars.AUTO
SB_ALWAYS_VERTICAL = Scrollbars.ALWAYS_VERTICAL
SB_ALWAYS_HORIZONTAL = Scrollbars.ALWAYS_HORIZONTAL
SB_ALWAYS = Scrollbars.ALWAYS
SB_NEVER_VERTICAL = Scrollbars.NEVER_VERTICAL
SB_NEVER_HORIZONTAL = Scrollbars.NEVER_HORIZONTAL
SB_NEVER = Scrollbars.NEVER


class BoundsChange(IntFlag):
    """BoundsChanged enumeration.

    Used in Rectangle.set_bounds() method to specify wich rect coordinates had its
    values changed. This allows to change a rect coordinate without moving the rect
    as it is the normal behavior when changing values directly.
    NONE: Nothing has changed;
    LEFT: The left coordinate changed;
    TOP: The top coordinate changed;
    RIGHT: The right coordinate changed;
    BOTTOM: The bottom coordinate changed;
    """
    NONE = 0
    LEFT = 1
    TOP = 2
    RIGHT = 4
    BOTTOM = 8
    ALL = LEFT | TOP | RIGHT | BOTTOM


BC_NONE = BoundsChange.NONE
BC_LEFT = BoundsChange.LEFT
BC_TOP = BoundsChange.TOP
BC_RIGHT = BoundsChange.RIGHT
BC_BOTTOM = BoundsChange.BOTTOM
BC_ALL = BoundsChange.ALL


class Alignment(IntFlag):
    """Alignment enumeration.

    Used to position an object's bounds relative to other.
    NONE: No aligment;
    LEFT: Aligns this with other's left coordinate.
    RIGHT: Aligns this with other's right coordinate.
    CENTER: Centralizes horizontally this with other's.
    TOP: Aligns this with other's top coordinate.
    BOTTOM: Aligns this with other's bottom coordinate.
    MIDDLE: Centralizes vertically this with other's.
    """
    NONE = 0
    LEFT = 1
    RIGHT = 2
    CENTER = LEFT | RIGHT
    TOP = 4
    BOTTOM = 8
    MIDDLE = TOP | BOTTOM


AL_NONE = Alignment.NONE
AL_LEFT = Alignment.LEFT
AL_RIGHT = Alignment.RIGHT
AL_CENTER = Alignment.CENTER
AL_TOP = Alignment.TOP
AL_BOTTOM = Alignment.BOTTOM
AL_MIDDLE = Alignment.MIDDLE


class ButtonPressedState(Enum):
    """ButtonPressedState enumeration.

    Used to specify the state ob a button.
    NORMAL: The button is not pressed and the mouse is not hovering it;
    HILIGHTED: The button is not pressed but the mouse is hovering it;
    PRESSED: The button is pressed.
    """
    NORMAL = 1
    HILIGHTED = 2
    PRESSED = 3


BPS_NORMAL = ButtonPressedState.NORMAL
BPS_HILIGHTED = ButtonPressedState.HILIGHTED
BPS_PRESSED = ButtonPressedState.PRESSED


class ButtonToggleState(Enum):
    """ButtonToggleState enumeration.

    For controls that behaves as ON/OFF switches (such as ToggleButtons), this
    enumeration is used to specify the toggle state.
    ON: The control is on, or checked;
    OFF: The control is off, or unchecked;
    UNDEFINED: The initial state of the control is yet to be defined or depend on other conditions.
    """
    OFF = 0
    ON = 1
    UNDEFINED = 2

BTS_ON = ButtonToggleState.ON
BTS_OFF = ButtonToggleState.OFF
BTS_UNDEFINED = ButtonToggleState.UNDEFINED


class CheckBoxState(Enum):
    """CheckBoxState enumeration.

    Similar to ButtonToggleState, this enumeration is used to specifiy the state of
    a CheckBox.
    UNCHECKED: The option this control represents is not checked.
    CHECKED: The option this control represents is checked.
    UNDEFINED: The option this control represents is in undefined state.
    """
    UNCHECKED = 0
    CHECKED = 1
    UNDFINED = 2


CBS_UNCHECKED = CheckBoxState.UNCHECKED
CBS_CHECKED = CheckBoxState.CHECKED
CBS_UNDFINED = CheckBoxState.UNDFINED


class SingletonMeta(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


#crsr
class LayoutCursor:

    __slots__ = '_controls', '_layout'

    def __init__(self) -> None:
        self._controls: List[Control] = []
        self._layout: List[LayoutNext] = []
        # remove these
        # self.left: int = left
        # self.top: int = top
        # self.row_bottom: int = 0
        # self.next: LayoutNext = LON_SAMELINE
        # self.ref: 'Control' = None

    def __nonzero__(self) -> bool:
        return True

    def __str__(self) -> str:
        return "LAYOUT[{}]".format(len(self))

    def __call__(self, control: 'Control', layout: 'LayoutNext') -> None:
        self._controls.append(control)
        self._layout.append(layout)

    def __len__(self) -> int:
        return len(self._controls)

    def __iter__(self):
        return [(self._controls[i], self._layout[i]) for i in range(len(self))].__iter__()


# rndr
class RendererBase:

    @classmethod
    def initialize_display(cls, size: 'Size', caption: str, **kwargs) -> 'RendererBase':
        pg.display.set_mode(size, kwargs.get('flags', 0), kwargs.get('depth', 32))
        pg.display.set_caption(caption, caption)
        return cls(kwargs.get('skin', DEFAULT_SKIN))

    def __init__(self, skin: Union[dict, OrderedDict, 'Namespace']) -> None:
        self._skin: Namespace = None
        self._cliprect_stack: List['Rectangle'] = []
        self._invalidated: List[pg.Rect] = []
        self._render_methods: Dict[str, str] = {
            'PushButton': 'PushButton',
            'CheckBox': 'CheckBox',
            'RadioButton': 'RadioButton',
            'ButtonGroup': 'ButtonGroup',
            'Panel': 'Panel',
        }
        if isinstance(skin, (dict, OrderedDict)):
            self._skin = Namespace(**skin)
        elif isinstance(skin, str):
            self._skin = Namespace.load(skin)
        elif isinstance(skin, Namespace):
            self._skin = skin
        else:
            raise TypeError("Unsupported value type: {cls}".format(cls=skin.__class__.__name__))

        self._guifont: Namespace = Namespace()
        self._textfont: Namespace = Namespace()
        self._codefont: Namespace = Namespace()
        self._images: List[pg.Surface] = []

        if len(self._skin.metrics.image.skin.filenames) != 0:
            for filename in self._skin.metrics.image.skin.filenames:
                image: pg.Surface = pg.image.load(filename)
                self._images.append(image)

        self._icons: pg.Surface = None
        if self._skin.metrics.image.iconset.using:
            self._icons = pg.image.load(self._skin.metrics.image.iconset.filename)

        for sizename in self._skin.metrics.font.size:
            size = self._skin.metrics.font.size[sizename]
            if self._skin.metrics.font.gui.is_sysfont:
                self._guifont[sizename] = pg.font.SysFont(self._skin.metrics.font.gui.name, size)
            else:
                self._guifont[sizename] = pg.font.Font(self._skin.metrics.font.gui.path, size)

            if self._skin.metrics.font.text.is_sysfont:
                self._textfont[sizename] = pg.font.SysFont(self._skin.metrics.font.text.name, size)
            else:
                self._textfont[sizename] = pg.font.Font(self._skin.metrics.font.text.path, size)

            if self._skin.metrics.font.code.is_sysfont:
                self._codefont[sizename] = pg.font.SysFont(self._skin.metrics.font.code.name, size)
            else:
                self._codefont[sizename] = pg.font.Font(self._skin.metrics.font.code.path, size)

    @property
    def gui_font(self) -> 'Namespace':
        return self._guifont

    @property
    def text_font(self) -> 'Namespace':
        return self._textfont

    @property
    def code_font(self) -> 'Namespace':
        return self._codefont

    @property
    def erase_color(self) -> 'Color':
        return Color(*self._skin.metrics.default.erase_color)

    @property
    def default(self) -> 'Namespace':
        return self._skin.metrics.default

    @erase_color.setter
    def erase_color(self, value: Union['Color', Tuple[int, int, int]]) -> None:
        self._skin.metrics.default.erase_color = value[0], value[1], value[2]

    def get_element(self, control: 'Control') -> Optional['Namespace']:
        clsname = control.__class__.__name__
        if clsname in self._render_methods:
            return self._skin[clsname]
        return None

    def get_render_layers(self, control: 'Control') -> RenderLayer:
        layers: RenderLayer = RL_NONE
        element: Optional[Namespace] = self.get_element(control)
        if element:
            for layer_flag in element.render_layers:
                layers |= RenderLayer[layer_flag]
        return layers

    def measure_text(self, control: 'Control', text: str, **kwargs) -> 'Size':
        element: Namespace = self.get_element(control)
        fontkey: str = kwargs.get('kind', 'gui')
        font: pg.font.Font = {
            'gui': self._guifont,
            'text': self._textfont,
            'code': self._codefont
        }.get(fontkey, self._guifont)[element.style.size]
        font.set_bold(element.style.bold)
        font.set_italic(element.style.italic)
        font.set_underline(element.style.underline)
        return Size(*font.size(text))

    def add_renderer(self, cls_name: str, element: str) -> None:
        if cls not in self._render_methods:
            self._render_methods[cls] = element

    def clear(self, color: 'Color') -> None:
        pg.display.get_surface().fill(color)

    def add_invalidated_rect(self, rect: 'Rectangle') -> None:
        self._invalidated.append(pg.Rect(*rect))

    def flip(self) -> None:
        self._invalidated.clear()
        pg.display.flip()

    def update(self) -> None:
        if self._invalidated:
            pg.display.update(self._invalidated)
            self._invalidated.clear()

    def get_render_target(self) -> Any:
        return pg.display.get_surface()

    def render(self, control: 'Control', render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
        cls: Type = control.__class__.__name__
        if cls not in self._render_methods:
            this = GrUsInRendererError("No render key defined for {} class.".format(control.__class__.__name__))
            raise this
        render_key: str = self._render_methods[cls]
        if cls not in self._skin:
            this = GrUsInRendererError("No render data defined for {} class in {} skin.".format(
                control.__class__.__name__,
                self._skin.meta.name
            ))
            raise this
        element: Namespace = self._skin[render_key]
        renderer: Callable[['Control', 'Namespace', ...], None] = getattr(self, element.method, self.fallback)
        renderer(control, element, self.get_render_target(), render_bounds, bounds, layer)

    def fallback(self, *args, **kwargs) -> None:
        print("fallback render method.")

    def get_display_size(self) -> 'Size':
        return pg.display.get_surface().get_size()

    def push_cliprect(self, rect: 'Rectangle'=None) -> None:
        if not rect:
            w, h = self.get_display_size()
            rect = Rectangle(0, 0, w, h)
        self._cliprect_stack.append(rect)
        pg.display.get_surface().set_clip(rect)

    def get_cliprect(self) -> 'Rectangle':
        if self._cliprect_stack:
            return self._cliprect_stack[-1].copy()
        w, h = self.get_display_size()
        return Rectangle(0, 0, w, h)

    def pop_cliprect(self) -> None:
        if self._cliprect_stack:
            self._cliprect_stack.pop()
            if self._cliprect_stack:
                pg.display.get_surface().set_clip(self._cliprect_stack[-1])
            else:
                w, h = self.get_display_size()
                pg.display.get_surface().set_clip([0, 0, w, h])

    #renderfuncs
    def render_pushbutton(self, control: 'PushButton', element: 'Namespace', surface: pg.Surface,
                          render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
        state: str = control.get_state()
        button: Namespace = element[state]
        
        if layer is RL_ABOVE_BACKGROUND or layer is RL_BELOW_FOREGROUND:
            font: pg.font.Font = self.gui_font[element.style.size]
            alignment: Alignment = Alignment[element.style.valign] | Alignment[element.style.halign]
            font.set_bold(element.style.bold)
            font.set_italic(element.style.italic)
            font.set_underline(element.style.underline)
            width, height = font.size(control.text)
            rect: Rectangle = Rectangle(bounds.left, bounds.top, width, height).align_to(bounds, alignment)
            s: pg.Surface = font.render(control.text, True, button.color)

            surface.blit(s, rect.location)

        if layer is RL_BACKGROUND:
            pg.draw.rect(surface, button.backcolor, bounds, 0)
        if layer is RL_FOREGROUND:
            pg.draw.rect(surface, button.bordercolor, bounds, 1)

    def render_buttongroup(self, control: 'ButtonGroup', element: 'Namespace', surface: pg.Surface,
                          render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
        state: str = control.get_state()
        button: Namespace = element[state]
        
        if layer is RL_ABOVE_BACKGROUND or layer is RL_BELOW_FOREGROUND:
            left: int = 0
            for item in control.items:
                if control.display is BGD_ICON or control.display is BGD_BOTH:
                    # do not forget to render the actual icon image!
                    icon_rect: Rectangle = Rectangle.join(bounds.location + control.padding.top_left, Size(*element.icon_size))

                    pg.draw.rect(surface, RED, icon_rect)

                if control.display is BGD_TEXT or control.display is BGD_BOTH:
                    font: pg.font.Font = self.gui_font[element.style.size]
                    alignment: Alignment = Alignment[element.style.valign] | Alignment[element.style.halign]
                    font.set_bold(element.style.bold)
                    font.set_italic(element.style.italic)
                    font.set_underline(element.style.underline)
                    width, height = font.size(control.text)
                    text_rect: Rectangle = Rectangle.join(bounds.location + control.padding.top_left, width, height)
                    if control.display is BGD_BOTH:
                        text_rect.left += element.icon_size[0] + control.padding.left
                    s: pg.Surface = font.render(item.text, True, button.color)

                    surface.blit(s, text_rect.location)

        if layer is RL_BACKGROUND:
            pg.draw.rect(surface, button.backcolor, bounds, 0)
        if layer is RL_FOREGROUND:
            pg.draw.rect(surface, button.bordercolor, bounds, 1)

    def render_panel(self, control: 'Panel', element: 'Namespace', surface: pg.Surface,
                     render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
        state: str = control.get_state()
        panel: Namespace = element[state]
        if layer is RL_BACKGROUND:
            pg.draw.rect(surface, panel.backcolor, bounds, 0)
        if layer is RL_FOREGROUND:
            pg.draw.rect(surface, panel.bordercolor, bounds, 1)

    def render_checkbox(self, control: 'CheckBox', element: 'Namespace', surface: pg.Surface,
                        render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
        if layer is RL_ABOVE_BACKGROUND or layer is RL_BELOW_FOREGROUND:
            state: str = control.get_state()
            checkbox: Namespace = element[state]
            font: pg.font.Font = self.gui_font[element.style.size]

            font.set_bold(element.style.bold)
            font.set_italic(element.style.italic)
            font.set_underline(element.style.underline)

            width, height = font.size(control.text)
            s: pg.Surface = font.render(control.text, True, checkbox.color)
            box_rect: Rectangle = Rectangle.join(bounds.location + control.padding.top_left, Size(height, height))
            text_pos: Point = box_rect.location + Point(box_rect.width, 0) + control.padding.top_left

            pg.draw.rect(surface, checkbox.backcolor, box_rect, 0)
            pg.draw.rect(surface, checkbox.bordercolor, box_rect, 1)
            if control.checked:
                pg.draw.rect(surface, checkbox.checkmark.color, box_rect.shrink(3), 0)

            # pg.draw.rect(surface, RED, bounds, 1)
            surface.blit(s, text_pos)

    def render_radiobutton(self, control: 'RadioButton', element: 'Namespace', surface: pg.Surface,
                           render_bounds: 'Rectangle', bounds: 'Rectangle', layer: RenderLayer) -> None:
            state: str = control.get_state()
            radiobutton: Namespace = element[state]
            font: pg.font.Font = self.gui_font[element.style.size]

            font.set_bold(element.style.bold)
            font.set_italic(element.style.italic)
            font.set_underline(element.style.underline)

            width, height = font.size(control.text)
            s: pg.Surface = font.render(control.text, True, radiobutton.color)
            box_rect: Rectangle = Rectangle.join(bounds.location + control.padding.top_left, Size(height, height))
            text_pos: Point = box_rect.location + Point(box_rect.width, 0) + control.padding.top_left

            pg.draw.ellipse(surface, radiobutton.backcolor, box_rect, 0)
            pg.draw.ellipse(surface, radiobutton.bordercolor, box_rect, 1)
            if control.checked:
                pg.draw.ellipse(surface, radiobutton.checkmark.color, box_rect.shrink(3), 0)

            pg.draw.rect(surface, RED, bounds, 1)
            surface.blit(s, text_pos)

class VecBase:

    def __add__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] + other), int(self[1] + other))
        return self.__class__(int(self[0] + other[0]), int(self[1] + other[1]))

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] - other), int(self[1] - other))
        return self.__class__(int(self[0] - other[0]), int(self[1] - other[1]))

    def __floordiv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] // other), int(self[1] // other))
        return self.__class__(int(self[0] // other[0]), int(self[1] // other[1]))

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] / other), int(self[1] / other))
        return self.__class__(int(self[0] / other[0]), int(self[1] / other[1]))

    def __mod__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] % other), int(self[1] % other))
        return self.__class__(int(self[0] % other[0]), int(self[1] % other[1]))

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] * other), int(self[1] * other))
        return self.__class__(int(self[0] * other[0]), int(self[1] * other[1]))


    def __radd__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] + other), int(self[1] + other))
        return self.__class__(int(self[0] + other[0]), int(self[1] + other[1]))

    def __rsub__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] - other), int(self[1] - other))
        return self.__class__(int(self[0] - other[0]), int(self[1] - other[1]))

    def __rfloordiv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] // other), int(self[1] // other))
        return self.__class__(int(self[0] // other[0]), int(self[1] // other[1]))

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] / other), int(self[1] / other))
        return self.__class__(int(self[0] / other[0]), int(self[1] / other[1]))

    def __rmod__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] % other), int(self[1] % other))
        return self.__class__(int(self[0] % other[0]), int(self[1] % other[1]))

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(int(self[0] * other), int(self[1] * other))
        return self.__class__(int(self[0] * other[0]), int(self[1] * other[1]))

    def __iadd__(self, other):
        if isinstance(other, (int, float)):
            self[0] += other
            self[1] += other
        else:
            self[0] += other[0]
            self[1] += other[1]
        return self

    def __isub__(self, other):
        if isinstance(other, (int, float)):
            self[0] -= other
            self[1] -= other
        else:
            self[0] -= other[0]
            self[1] -= other[1]
        return self

    def __ifloordiv__(self, other):
        if isinstance(other, (int, float)):
            self[0] //= other
            self[1] //= other
        else:
            self[0] //= other[0]
            self[1] //= other[1]
        return self

    def __itruediv__(self, other):
        if isinstance(other, (int, float)):
            self[0] /= other
            self[1] /= other
        else:
            self[0] /= other[0]
            self[1] /= other[1]
        return self

    def __imod__(self, other):
        if isinstance(other, (int, float)):
            self[0] %= other
            self[1] %= other
        else:
            self[0] %= other[0]
            self[1] %= other[1]
        return self

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            self[0] *= other
            self[1] *= other
        else:
            self[0] *= other[0]
            self[1] *= other[1]
        return self


# clsPoint
class Point(VecBase):
    __slots__ = '_x', '_y'

    def __init__(self, x: int=0, y: int=0) -> None:
        """Constructor."""
        self._x = int(x)
        self._y = int(y)

    def __len__(self) -> int:
        """Num. of elements."""
        return 2

    def __getitem__(self, key: int) -> int:
        assert isinstance(key, int), "int key expected, not {key_type}.".format(
            key_type=key.__class__.__name__)
        if 0 <= key < 2:
            return (self._x, self._y)[key]
        else:
            raise IndexError("Index out of bounds.")

    def __setitem__(self, key: int, value: int) -> None:
        assert isinstance(key, int), "int key expected, not {key_type}.".format(
            key_type=key.__class__.__name__)
        if 0 <= key < 2:
            if key == 0:
                self._x = int(value)
            else:
                self._y = int(value)
        else:
            raise IndexError("Index out of bounds.")

    def __iter__(self):
        return (self._x, self._y).__iter__()

    def __str__(self) -> str:
        return "({x}, {y})".format(x=self._x, y=self._y)

    def __repr__(self) -> str:
        return "{name}({x}, {y})".format(
            name=self.__class__.__qualname__, x=self._x, y=self._y)

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = int(value)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = int(value)

    def copy(self) -> 'Point':
        return self.__class__(self._x, self._y)

    def snap(self, width: int, height: int) -> 'Point':
        return self.__class__((self._x // width) * width, (self._y // height) * height)


# clsSize
class Size(VecBase):
    __slots__ = '_width', '_height'

    def __init__(self, width: int=0, height: int=0) -> None:
        """Constructor."""
        self._width = int(width)
        self._height = int(height)

    def __len__(self) -> int:
        """Num. of elements."""
        return 2

    def __getitem__(self, key: int) -> int:
        assert isinstance(key, int), "int key ewidthpected, not {key_type}.".format(
            key_type=key.__class__.__name__)
        if 0 <= key < 2:
            return (self._width, self._height)[key]
        else:
            raise IndexError("Indewidth out of bounds.")

    def __setitem__(self, key: int, value: int) -> None:
        assert isinstance(key, int), "int key ewidthpected, not {key_type}.".format(
            key_type=key.__class__.__name__)
        if 0 <= key < 2:
            if key == 0:
                self._width = int(value)
            else:
                self._height = int(value)
        else:
            raise IndexError("Indewidth out of bounds.")

    def __iter__(self):
        return (self._width, self._height).__iter__()

    def __str__(self) -> str:
        return "({width}, {height})".format(width=self._width, height=self._height)

    def __repr__(self) -> str:
        return "{name}({width}, {height})".format(
            name=self.__class__.__qualname__, width=self._width, height=self._height)

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = int(max(0, value))

    @property
    def height(self) -> int:
        return self._height

    @property
    def empty(self):
        return self._width == 0 or self._height == 0

    @height.setter
    def height(self, value: int) -> None:
        self._height = int(max(0, value))

    def copy(self) -> 'Size':
        return self.__class__(self._width, self._height)


class Spacing:
    __slots__ = 'left', 'top', 'right', 'bottom'

    @classmethod
    def all(cls, value: int) -> 'Spacing':
        return cls(value, value, value, value)

    def __init__(self, left: int=2, top: int=2, right: int=2, bottom: int=2) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @property
    def hor(self) -> int:
        return self.left + self.right

    @property
    def ver(self) -> int:
        return self.top + self.bottom

    @property
    def top_left(self) -> 'Point':
        return Point(self.left, self.top)

    @property
    def top_right(self) -> 'Point':
        return Point(self.right, self.top)

    @property
    def bottom_left(self) -> 'Point':
        return Point(self.left, self.bottom)

    @property
    def bottom_right(self) -> 'Point':
        return Point(self.right, self.bottom)


# clsColor
class Color:
    __slots__ = '_rgb'

    def __init__(self, r: int, g: int, b: int) -> None:
        self._rgb = bytearray((r, g, b))

    def __getitem__(self, key) -> int:
        assert isinstance(key, int), "int key expected."
        return self._rgb.__getitem__(key)

    def __setitem__(self, key, value) -> int:
        assert isinstance(key, int), "int key expected."
        assert 0 <= value <= 255, "value outside (0 .. 255) range."
        return self._rgb.__setitem__(key, value)

    def __len__(self) -> int:
        return 3

    @property
    def rgb(self) -> tuple:
        return self[0], self[1], self[2]

    @property
    def r(self):
        return self._rgb[0]

    @r.setter
    def r(self, value):
        self._rgb[0] = value

    @property
    def g(self):
        return self._rgb[1]

    @g.setter
    def g(self, value):
        self._rgb[1] = value

    @property
    def b(self):
        return self._rgb[2]

    @b.setter
    def b(self, value):
        self._rgb[2] = value

    def inverse(self) -> 'Color':
        return self.__class__(255 - self.r, 255 - self.g, 255 - self.b)

    def mix(self, other, ratio: float) -> 'Color':
        r, g, b = other
        return self.__class__(
            int(self.r + (r - self.r) * ratio),
            int(self.g + (g - self.g) * ratio),
            int(self.b + (b - self.b) * ratio)
        )


BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
YELLOW = Color(255, 255, 0)
GREEN = Color(0, 255, 0)
GRAY = Color(127, 127, 127)
CIAN = Color(0, 255, 255)
BLUE = Color(0, 0, 255)
MAGENTA = Color(255, 0, 255)
WHITE = Color(255, 255, 255)


class Rectangle:

    @classmethod
    def join(cls, point: 'Point', size: 'Size') -> 'Rectangle':
        return cls(point.x, point.y, size.width, size.height)

    __slots__ = '_left', '_top', '_width', '_height'

    def __init__(self, left: int, top: int, width: int, height: int) -> None:
        self._left: int = int(left)
        self._top: int = int(top)
        self._width: int = int(width)
        self._height: int = int(height)

    def __str__(self) -> str:
        return "({0.left}x, {0.top}y, {0.width}w, {0.height}h)".format(self)

    def __len__(self) -> int:
        return 4

    def __getitem__(self, key) -> Any:
        return (self._left, self._top, self._width, self._height)[key]

    def __iter__(self) -> Any:
        return (self._left, self._top, self._width, self._height).__iter__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            try:
                l, t, w, h = other
            except (TypeError, ValueError, KeyError, IndexError):
                return False
            return l == self._left and t == self._top and w == self._width and h == self._height
        else:
            return (other.left == self._left and other.top == self._top and
                    other.width == self._width and other.height == self._height)

    def __ne__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            try:
                l, t, w, h = other
            except (TypeError, ValueError, KeyError, IndexError):
                return False
            return l != self._left or t != self._top or w != self._width or h != self._height
        else:
            return (other.left != self._left or other.top != self._top or
                    other.width != self._width or other.height != self._height)

    @property
    def empty(self) -> bool:
        return self._width == 0 or self._height == 0

    @property
    def left(self) -> int:
        return self._left

    @left.setter
    def left(self, value: int) -> None:
        self._left = int(value)

    @property
    def top(self) -> int:
        return self._top

    @top.setter
    def top(self, value: int) -> None:
        self._top = int(value)

    @property
    def location(self) -> Point:
        return Point(self._left, self._top)

    @location.setter
    def location(self, value: Point) -> None:
        self._left, self._top = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = max(0, int(value))

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = max(0, int(value))

    @property
    def size(self) -> Size:
        return Size(self._width, self._height)

    @size.setter
    def size(self, value: Size) -> None:
        self.width, self.height = value

    @property
    def right(self) -> int:
        return self._left + self._width

    @right.setter
    def right(self, value: int) -> None:
        self._left = int(value - self._width)

    @property
    def bottom(self) -> int:
        return self._top + self._height

    @bottom.setter
    def bottom(self, value: int) -> None:
        self._top = int(value - self._height)

    def contains(self, other: Union[Point, Size, 'Rectangle']) -> bool:
        if isinstance(other, Point):
            return self._left <= other.x < self.right and self._top <= other.y < self.bottom

        elif isinstance(other, Size):
            return self._width >= other.width and self._height >= other.height

        elif isinstance(other, Rectangle):
            return (self._left <= other.left and self._top <= other.top and
                    self.right >= other.right and self.bottom >= other.bottom)

        else:
            try:
                n = len(other)
            except (TypeError, ValueError, KeyError, IndexError):
                return False
            if n == 2:
                x, y = other
                return self._left <= x < self.right and self._top <= y < self.bottom
            elif n == 4:
                x, y, w, h
                return self._left <= x and self._top <= y and self.right >= x + w and self.bottom >= y + h
            else:
                raise TypeError("Not rect/point like.")

    def intersects(self, other: 'Rectangle') -> bool:
        sl, st, sw, sh = self
        ol, ot, ow, oh = other

        if sl > ol + ow or ol > sl + sw or st > ot + oh or ot > st + sh:
            return False
        return True

    def intersection(self, other: 'Rectangle') -> Optional['Rectangle']:
        if not self.intersects(other):
            return Rectangle(0, 0, 0, 0)

        sl, st, sw, sh = self
        ol, ot, ow, oh = other

        return Rectangle(
            max(sl, ol),
            max(st, ot),
            min(sl + sw, ol + ow),
            min(st + sh, ot + oh)
        )

    def to_local(self, point: Point) -> Point:
        return point - self.location

    def to_global(self, point: Point) -> Point:
        return point + self.location

    def copy(self) -> 'Rectangle':
        return Rectangle(self._left, self._top, self._width, self._height)

    def scale(self, factor: float, origin: Point) -> 'Rectangle':
        if factor <= 0:
            raise ValueError("factor argument must be larger than zero.")

        offset = (origin - self.location) * factor

        self.location = origin - offset
        self.size *= factor

        return self

    def move(self, offset: Point) -> 'Rectangle':
        self.location += offset

    def set_bounds(self, left: int, top: int, right: int, bottom: int, changed: BoundsChange) -> 'Rectangle':
        if (changed & BC_LEFT) == BC_LEFT and left != self.left:
            self.width = self.right - left
            self.left = left

        if (changed & BC_RIGHT) == BC_RIGHT and right != self.right:
            self.width = right - self.left
            self.right = right

        if (changed & BC_TOP) == BC_TOP and top != self.top:
            self.height = self.bottom - top
            self.top = top

        if (changed & BC_BOTTOM) == BC_BOTTOM and bottom != self.bottom:
            self.height = bottom - self.top
            self.bottom = bottom

        return self

    def clamp(self, smaller: 'Rectangle', larger: 'Rectangle') -> 'Rectangle':
        if not larger.contains(smaller):
            raise ValueError("smaller rectangle must be contained in larger.")

        return self.set_bounds(
            max(smaller.left, min(self.left, larger.left)),
            max(smaller.top, min(self.top, larger.top)),
            max(smaller.right, min(self.right, larger.right)),
            max(smaller.bottom, min(self.bottom, larger.bottom)),
            BC_ALL
        )

    def expand(self, spacing: Spacing) -> 'Rectangle':
        self.left -= spacing.left
        self.width += spacing.hor
        self.top -= spacing.top
        self.height += spacing.ver

        return self

    def reduce(self, spacing: Spacing) -> 'Rectangle':
        self.left += spacing.left
        self.width -= spacing.hor
        self.top += spacing.top
        self.height -= spacing.ver

        return self

    def grow(self, amount: int) -> 'Rectangle':
        self.left -= amount
        self.width += amount * 2
        self.top -= amount
        self.height += amount * 2

        return self

    def shrink(self, amount: int) -> 'Rectangle':
        self.left += amount
        self.width -= amount * 2
        self.top += amount
        self.height -= amount * 2

        return self

    def split_v(self, y: Union[int, float]) -> Tuple['Rectangle', 'Rectangle']:
        if isinstance(y, float):
            y = self._top + int(self._height * (y % 1))

        if y <= self.top:
            return Rectangle(self._left, self._top, self._width, 0), self.copy()
        elif y >= self.right:
            return self.copy(), Rectangle(self._left, self._top, self._width, 0)
        else:
            return (
                Rectangle(self._left, self._top, self._width, y - self._top),
                Rectangle(self._left, y, self._width, self.bottom - y)
            )

    def split_h(self, x: Union[int, float]) -> Tuple['Rectangle', 'Rectangle']:
        if isinstance(x, float):
            x = self._left + int(self._width * (x % 1))

        if x <= self.left:
            return Rectangle(self._left, self._top, 0, self._height), self.copy()
        elif x >= self.right:
            return self.copy(), Rectangle(self._left, self._top, 0, self._height)
        else:
            return (
                Rectangle(self._left, self._top, x - self._left, self._height),
                Rectangle(x, self._top, self.right - x, self._height)
            )

    def align_to(self, other: 'Rectangle', alignment: Alignment) -> 'Rectangle':
        if alignment & AL_CENTER == AL_CENTER:
            cx = other.left + (other.width // 2)
            self.left = cx - (self.width // 2)
        elif alignment & AL_LEFT == AL_LEFT:
            self.left = other.left
        elif alignment & AL_RIGHT == AL_RIGHT:
            self.right = other.right

        if alignment & AL_MIDDLE == AL_MIDDLE:
            cy = other.top + (other.height // 2)
            self.top = cy - (self.height // 2)
        elif alignment & AL_TOP == AL_TOP:
            self.top == other.top
        elif alignment & AL_BOTTOM == AL_BOTTOM:
            self.bottom = other.bottom

        return self


class Namespace(object):

    _indent = 0

    @classmethod
    def load(cls, fname):
        # type: (str) -> Namespace
        if isinstance(fname, io.TextIOWrapper):
            with fname as ns:
                code = "".join(ns.readlines())
        else:
            with open(fname) as ns:
                code = "".join(ns.readlines())
        subdat = ast.literal_eval(code)
        return cls(**subdat)

    @classmethod
    def items(cls, ns):
        # type: (Namespace) -> tuple
        assert ns.__class__ is cls, "'ns' is not a Namespace object."
        return ns._dict.items()

    @classmethod
    def keys(cls, ns):
        # type: (Namespace) -> tuple
        assert ns.__class__ is cls, "'ns' is not a Namespace object."
        return ns._dict.keys()

    @classmethod
    def values(cls, ns):
        # type: (Namespace) -> tuple
        assert ns.__class__ is cls, "'ns' is not a Namespace object."
        return ns._dict.values()

    def __init__(self, **kwargs):
        self._dict = OrderedDict()
        for key in kwargs:
            value = kwargs[key]
            if isinstance(value, (dict, OrderedDict)):
                self[key] = Namespace(**value)
            else:
                setattr(self, key, value)

    def __getattr__(self, name):
        if name != '_dict':
            if name in getattr(self, '_dict'):
                return getattr(self, '_dict')[name]
            else:
                raise AttributeError("Namespace object has no '{}' attribute.".format(name))
        else:
            return self._dict

    def __setattr__(self, name, value):
        if name != '_dict':
            if isinstance(value, (dict, OrderedDict)):
                getattr(self, '_dict')[name] = Namespace(**value)
            else:
                getattr(self, '_dict')[name] = value
        else:
            getattr(self, '__dict__')[name] = value

    def __delattr__(self, name):
        if name == '_dict':
            raise AttributeError("Could not delete the attribute.")
        else:
            if name in getattr(self, '_dict'):
                del getattr(self, '_dict')[name]
            else:
                raise AttributeError("Namespace object has no '{}' attribute.".format(name))

    def __str__(self):
        Namespace._indent += 1
        indents = " " * (Namespace._indent * 4)
        _items = ""
        for key in self._dict:
            _items += "{}'{}': {},\n".format(indents, key, repr(self._dict[key]))
        Namespace._indent -= 1
        return "{{\n{}{}}}".format(_items, ' ' * (Namespace._indent * 4))

    __repr__ = __str__

    def __getitem__(self, key):
        return self._dict.__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            self._dict.__setitem__(key, Namespace(**value))
        else:
            self._dict.__setitem__(key, value)

    def __delitem__(self, key):
        self._dict.__delitem__(key)

    def __len__(self):
        return self._dict.__len__()

    def __iter__(self):
        return self._dict.__iter__()

    def __contains__(self, name):
        return name in self._dict


#clsapp
class Application(metaclass=SingletonMeta):

    def __init__(self):
        self._running: bool = False
        self._display: pg.Surface = None
        self._clock: pg.time.Clock = pg.time.Clock()
        self._renderer: RendererBase = None

    def get_renderer(self) -> RendererBase:
        return self._renderer

    @contextmanager
    def start(self, **kwargs) -> None:
        global this
        pg.init()

        self._display = pg.display.set_mode((960, 540))
        self._renderer = RendererBase.initialize_display(Size(960, 540), "GrUsIn - v0.1.0.a0", skin=DEFAULT_SKIN)
        self._display.fill(WHITE)
        self._renderer.clear(WHITE)
        self._renderer.flip()
        runtime: UIRuntime = UIRuntime()

        this = None
        yield
        runtime.layout_topmost()
        del this
        self._running = True
        main_form = kwargs.get('main_form')
        if isinstance(main_form, str):
            active = runtime.find_by_name(main_form)
            if active:
                runtime._active = active
                runtime.bring_to_front(active)
                active.process_message(Message.ACTIVATED)
        while True:
            runtime.process_events(pg.event.get())
            runtime.validate()
            self._clock.tick(60)


#uirt
class UIRuntime(metaclass=SingletonMeta):

    def __init__(self) -> None:
        self._initialized: bool = False
        self._sentinel: object = object()
        self._init_stack: List['Control'] = [self._sentinel]
        self._controls: List['Control'] = []
        self._to_activate: 'Control' = None
        self._instance_counter: Dict[Type, int] = {}
        self._font: pg.font.SysFont = pg.font.SysFont("Arial", 32)
        self._cursor_stack: List[LayoutCursor] = [LayoutCursor()]

        # mouse input
        self._mbuttons: bytearray = bytearray(4)
        self._last_mbuttons: bytearray = bytearray(4)
        self._press_time: List[int] = [0, 0, 0, 0]
        self._release_time: List[int] = [0, 0, 0, 0]
        self._drag_pos: List[Point] = [None, Point(0, 0), Point(0, 0), Point(0, 0)]
        self._drag_delta: int = 4
        self._drag_button: int = MB_NONE
        self._drag_accept: bool = False
        self._drag_receiver: Optional['Control'] = None
        self._captured: Optional['Control'] = None
        self._hovered: Optional['Control'] = None
        self._focused: Optional['Control'] = None
        self._hittest: HitTest = HT_NONE
        self._last_motion: 0   # pg.time.get_ticks()

        # topmost
        self._active: 'Control' = None

        # invalidated areas
        self._invalidated: List[pg.Rect] = []

    @property
    def initializing(self) -> bool:
        return (self._initialized is False and len(self._init_stack) > 0 and
            self._init_stack[0] is self._sentinel)

    @property
    def context(self) -> Optional['Control']:
        if not self.initializing:
            return None
        if self._init_stack[-1] is not self._sentinel:
            return self._init_stack[-1]

        return None

    def get_cursor(self) -> Optional[LayoutCursor]:
        if self._cursor_stack:
            return self._cursor_stack[-1]
        return None

    def get_index(self, control: 'Control') -> int:
        if control in self._controls:
            return self._controls.index(control)
        return -1

    def find_by_name(self, name: str) -> Optional['Control']:
        for control in self._controls:
            if control.name == name:
                return control
        return None

    def gen_name(self, control: 'Control') -> str:
        if not isinstance(control, Control):
            raise TypeError("{cls} is not subclass of Control.".format(cls=control.__class__.__name__))
        basename = control.__class__.__name__.lower()
        if control.__class__ not in self._instance_counter:
            self._instance_counter[control.__class__] = 1
            return basename
        else:
            name = "{}{}".format(basename, self._instance_counter[control.__class__])
            self._instance_counter[control.__class__] += 1
            return name

    def enter_context(self, control: 'Control') -> None:
        global this
        self._init_stack.append(control)
        self._cursor_stack.append(LayoutCursor())
        this = control

    def exit_context(self) -> None:
        global this
        if this:
            self.context.process_message(Message.LAYOUT_CHILDREN, self.get_cursor())
        self._init_stack.pop()
        self._cursor_stack.pop()
        if self._init_stack:
            this = self._init_stack[-1]

    def layout_topmost(self) -> None:
        cursor: Optional[LayoutCursor] = self.get_cursor()
        renderer: RendererBase = Application().get_renderer()
        left: int = renderer.default.padding[0]     # left
        top: int = renderer.default.padding[1]      # top
        bottom: int = top
        previous: Control = None
        for child, layout in cursor:
            if child not in self._controls:
                continue

            if previous is None:
                child.location = Point(left + child.margin.left, top + child.margin.top)
                if bottom < child.bounds.bottom + child.margin.bottom:
                    bottom = child.bounds.bottom + child.margin.bottom
            else:
                if layout is LON_SAMELINE:
                    child.bounds.left = previous.bounds.right + previous.margin.right + child.margin.left
                    child.bounds.top = top + child.margin.top
                    if bottom < child.bounds.bottom + child.margin.bottom:
                        bottom = child.bounds.bottom + child.margin.bottom

                elif layout is LON_BELOW:
                    child.bounds.left = previous.bounds.left - previous.margin.left + child.margin.left
                    child.bounds.top = previous.bounds.bottom + previous.margin.bottom + child.margin.top
                    if bottom < child.bounds.bottom + child.margin.bottom:
                        bottom = child.bounds.bottom + child.margin.bottom

                elif layout is LON_NEWLINE:
                    child.bounds.left = left + child.margin.left
                    child.bounds.top = bottom + child.margin.top
                    bottom = child.bounds.bottom + child.margin.bottom

                elif layout is LON_CASCADE:
                    child.bounds.left = previous.bounds.left + 32
                    child.bounds.top = previous.bounds.top + 32
                    if bottom < child.bounds.bottom + child.margin.bottom:
                        bottom = child.bounds.bottom + child.margin.bottom

                elif layout is LON_MANUAL:
                    pass        # do nothing...

            previous = child

    def set_parent(self, child: 'Control') -> bool:
        if self.context:
            parent = self.context
            return parent.process_message(Message.ADD_CHILD, child)

        self._controls.append(child)
        return False

    def add_control(self, control: 'Control') -> None:
        if control not in self._controls:
            self._controls.append(control)

    def is_topmost(self, control: 'Control') -> bool:
        return control in self._controls

    def bring_to_front(self, control: 'Control') -> None:
        self._controls.remove(control)
        self._controls.append(control)

    @staticmethod
    def set_invalidated_rectangle(self, rectangle: Rectangle) -> None:
        Application().get_renderer().add_invalidated_rect(rectangle)

    #refresher
    def validate(self) -> None:
        renderer: RendererBase = Application().get_renderer()
        for control in self._controls:
            if control.visible:
                control.process_message(Message.RENDER_BACKGROUND, renderer.get_cliprect())
                control.process_message(Message.RENDER, renderer.get_cliprect())
                control.process_message(Message.RENDER_FOREGROUND, renderer.get_cliprect())

        renderer.update()

    def erase(self,control: 'Control', erase_rectangle: 'Rectangle') -> None:
        renderer: RendererBase = Application().get_renderer()
        renderer.push_cliprect(erase_rectangle)
        renderer.clear(renderer.erase_color)
        renderer.pop_cliprect()

        for topmost in self._controls:
            if topmost.bounds.intersects(erase_rectangle):
                topmost.process_message(Message.RENDER, erase_rectangle)

    def _is_mbutton(self, index: int) -> bool:
        return index == MB_LEFT or index == MB_RIGHT or index == MB_RIGHT

    def _is_mwheel(self, index: int) -> bool:
        return index == MB_WHEEL_DOWN or index == MB_WHEEL_UP

    #procevt
    def process_events(self, evs: List[pg.event.Event]) -> None:
        pressed_now: List[bool] = [0, False, False, False]
        current_time: int = pg.time.get_ticks()

        for event in evs:
            if event.type == pg.QUIT:
                sys.exit()

            elif event.type == pg.ACTIVEEVENT:
                pass

            elif event.type == pg.KEYDOWN:
                pass

            elif event.type == pg.KEYUP:
                pass

            elif event.type == pg.MOUSEMOTION:
                self._last_motion = pg.time.get_ticks()
                hovered = None
                hittest = HT_NONE
                for control in self._controls:
                    hov, hit = control.process_message(Message.HIT_TEST, Point(*event.pos), Point(*event.rel))
                    if hov:
                        hovered = hov
                        hittest = hit       # no utlilty to this ATM

                if self._captured is None:
                    if hovered is not self._hovered:
                        if self._hovered:
                            self._hovered.process_message(Message.MOUSE_LEAVE)

                        if hovered:
                            hovered.process_message(Message.MOUSE_ENTER)
                        self._hovered = hovered

                    elif self._hovered:
                        self._hovered.process_message(Message.MOUSE_MOVE)
                else:
                    if self._drag_button == MB_NONE:
                        for button in (MB_LEFT, MB_MIDDLE, MB_RIGHT):
                            if self._mbuttons[button]:
                                start: Point = self._drag_pos[button]
                                if abs(event.pos[0] - start.x) > self._drag_delta or abs(event.pos[1] > self._drag_delta):
                                    self._drag_button = button
                                    self._captured.process_message(Message.MOUSE_STARTDRAG, button, start)
                    else:
                        if hovered:
                            if hovered is not self._captured:
                                self._captured.process_message(Message.MOUSE_DRAGMOVE,
                                                               self._drag_button,
                                                               self._drag_pos[self._drag_button],
                                                               Point(*event.pos))
                                self._drag_accept = hovered.process_message(Message.DRAG_ACCEPT, self._captured)
                                if self._drag_accept:
                                    self._drag_receiver = hovered
                                else:
                                    self._drag_receiver = None

            elif event.type == pg.MOUSEBUTTONUP:
                if self._is_mbutton(event.button):
                    self._release_time[event.button] = current_time

                if self._drag_button == event.button and self._captured:
                    self._captured.process_message(
                        Message.MOUSE_STOPDRAG, self._drag_button, self._drag_pos[self._drag_button], Point(*event.pos))

                    if self._drag_accept:
                        package: Any = self._captured.process_message(Message.DRAG_SENDDATA)
                        self._drag_receiver.process_message(Message.DRAG_RECVDATA, package)
                        self._drag_accept = False
                        self._drag_receiver = None
                        self._drag_button = MB_NONE
                        self._drag_pos = Point(0, 0)

                if event.button == MB_LEFT:
                    self._mbuttons[MB_LEFT] = 0
                    if self._press_time[MB_LEFT] - current_time < 200:
                        if self._hovered:
                            self._hovered.process_message(Message.MOUSE_CLICK)

                    is_hovering: bool = False
                    if self._captured:
                        hov, hit = self._captured.process_message(Message.HIT_TEST, Point(*event.pos), Point(0, 0))
                        is_hovering = hov is self._captured
                        self._captured.process_message(Message.MOUSE_RELEASE, is_hovering)
                        self._captured = None

                    if not is_hovering:
                        hovered = self._hovered
                        hittest = self._hittest
                        for control in self._controls:
                            hov, hit = control.process_message(Message.HIT_TEST, Point(*event.pos), Point(0, 0))
                            if hov:
                                hovered = hov
                                hittest = hit

                        if hovered is not self._hovered:
                            if self._hovered:
                                self._hovered.process_message(Message.MOUSE_LEAVE)

                            if hovered:
                                self._hovered.process_message(Message.MOUSE_ENTER)
                            self._hovered = hovered

            elif event.type == pg.MOUSEBUTTONDOWN:
                if self._is_mbutton(event.button):
                    self._drag_pos[event.button] = Point(*event.pos)
                    self._press_time[event.button] = pg.time.get_ticks()
                    pressed_now[event.button] = True

                if event.button == MB_LEFT:
                    self._mbuttons[MB_LEFT] = 1

                    if self._hovered:
                        topmost: Control = self._hovered.get_topmost()
                        if self._active:
                            if self._active is not topmost:
                                modal: bool = self._active.behavior & BE_MODAL == BE_MODAL
                                modeless: bool = self._active.behavior & BE_MODELESS == BE_MODELESS
                                if not modal and not modeless:
                                    self.bring_to_front(topmost)
                                    deactivated = self._active
                                    self._active = topmost
                                    deactivated.process_message(Message.DEACTIVATED)
                                    self._active.process_message(Message.ACTIVATED)
                                elif modal and not modeless:
                                    # can't do SHIT!!
                                    pass
                                elif not modal and modeless:
                                    self.bring_to_front(topmost)
                                else:
                                    deactivated = self._active
                                    self._active = topmost
                                    deactivated.process_message(Message.DEACTIVATED)
                                    self._active.process_message(Message.ACTIVATED)

                    if self._active:
                        to_focus = self._active.selected_child
                    else:
                        to_focus = None
                    if self._focused != to_focus:
                        if self._focused:
                            self._focused.process_message(Message.DEFOCUSED)

                        if to_focus:
                            to_focus.process_message(Message.FOCUSED)
                        self._focused = to_focus

                    self._captured = self._hovered
                    if self._captured:
                        self._captured.process_message(Message.SELECTED)
                    if self._hovered:
                        self._hovered.process_message(Message.MOUSE_PRESS)

            elif event.type == pg.VIDEORESIZE:
                pass

            elif event.type == pg.VIDEOEXPOSE:
                pass


        if self._mbuttons[MB_LEFT] and not pressed_now[MB_LEFT]:
            if self._hovered:
                self._hovered.process_message(Message.MOUSE_DOWN, MB_LEFT, Point(*pg.mouse.get_pos()))

        if self._mbuttons[MB_MIDDLE] and not pressed_now[MB_MIDDLE]:
            if self._hovered:
                self._hovered.process_message(Message.MOUSE_DOWN, MB_MIDDLE, Point(*pg.mouse.get_pos()))

        if self._mbuttons[MB_RIGHT] and not pressed_now[MB_RIGHT]:
            if self._hovered:
                self._hovered.process_message(Message.MOUSE_DOWN, MB_RIGHT, Point(*pg.mouse.get_pos()))


class EventBase:

    @classmethod
    def handler(cls, handler: Callable[['Control', 'EventArgs'], Any]) -> None:
        context = UIRuntime().context
        if context:
            if not hasattr(context, cls.get_handler_name()):
                setattr(context, cls.get_handler_name(), cls())
            getattr(context, cls.get_handler_name()).attach(handler)

    @classmethod
    def get_handler_name(cls) -> str:
        return "_on_{event}".format(event=cls.__name__.replace('Event', '').lower())

    def __init__(self):
        self._handlers: List[Callable[['Control', 'Control'], Any]] = []

    def __call__(self, sender: 'Control', evargs: 'EventArgs') -> None:
        for handler in self._handlers:
            handler(sender, evargs)

    def attach(self, handler_method) -> None:
        self._handlers.append(handler_method)

    @property
    def handler_name(self) -> str:
        return self.get_handler_name


class EventArgs:

    def __init__(self, **kwargs) -> None:
        self._keys = []
        for kw in kwargs:
            self._keys.append(kw)
            setattr(self, kw, kwargs[kw])

    def copy(self) -> 'EventArgs':
        kwargs = {kw: getattr(self, kw) for kw in self._keys}
        return EventArgs(**kwargs)


#ctrlcls
class Control:

    class MouseEnterEvent(EventBase):
        pass

    class MousePressEvent(EventBase):
        pass

    class MouseDownEvent(EventBase):
        pass

    class MouseReleaseEvent(EventBase):
        pass

    class MouseLeaveEvent(EventBase):
        pass

    class FocusedEvent(EventBase):
        pass

    class DefocusedEvent(EventBase):
        pass

    _behavior: Behavior = BE_SELECTABLE

    def __init__(self, parent: 'Control'=DEFAULT, name: str=DEFAULT, **kwargs):
        rt = UIRuntime()
        renderer: RendererBase = Application().get_renderer()
        element: Namespace = renderer.get_element(self)
        cursor: LayoutCursor = rt.get_cursor()
        if isinstance(cursor, LayoutCursor):
            cursor(self, kwargs.get('layout', LON_NEWLINE))

        self._parent: 'Control' = None
        self._name: str = rt.gen_name(self) if name is DEFAULT else name

        # text
        self._tooltip: str = ""

        # spacing
        self._margin: Spacing = Spacing(*element.layout.margin)
        self._padding: Spacing = Spacing(*element.layout.padding)
        self._render_margin: Spacing = Spacing.all(0)

        # bounds
        w, h = element.layout.size

        self._client_bounds: Rectangle = Rectangle(0, 0, w, h)
        self._client_alignment: Alignment = AL_CENTER | AL_MIDDLE
        self._bounds: Rectangle = Rectangle(0, 0, w, h)

        # state
        self._visible: bool = True
        self._enabled: bool = True
        self._validated: bool = False
        self._validating: bool = False

        if parent is DEFAULT:
            if rt.context:
                self.parent = rt.context
            else:
                self.parent = None
                rt.add_control(self)
        else:
            # ownership is for non-clients, parentship is for clients
            # if ownership is defined, the owner is totaly responsible
            # for the owned initialization, message processing, layout etc.
            if kwargs.get('owner') is not None:
                # prevent ADD_CHILD to be sent to parent
                self._parent = owner
            else:
                self.parent = parent
        self._get_events()
        # self._auto_layout()       # remove this later

    def __str__(self) -> str:
        return "[{name}:{cls} - {bounds} {visible} {enabled} {index}]".format(
            name=self._name,
            cls=self.__class__.__name__,
            bounds=self._bounds,
            enabled=self.enabled,
            visible=self.visible,
            index=self.depth_order
        )

    def __enter__(self):
        UIRuntime().enter_context(self)

    def __exit__(self, exc_type, exc_value, traceback):
        UIRuntime().exit_context()

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> Optional['Control']:
        return self._parent

    @parent.setter
    def parent(self, value: 'Control') -> None:
        if self._parent is not value:
            if self._parent:
                self.send_message(self, Message.REMOVE_CHILD, self)

            if value:
                if self.send_message(value, Message.ADD_CHILD, self):
                    self._parent = value
            else:
                self._parent = None

    @property
    def selected_child(self) -> Optional['Control']:
        if self.behavior & BE_SELECTABLE == BE_SELECTABLE:
            return self
        return None

    @property
    def behavior(self) -> Behavior:
        return self._behavior

    @property
    def depth_order(self) -> int:
        if self.is_topmost:
            return UIRuntime().get_index(self)
        elif self._parent:
            return self.send_message(self.parent, Message.CHILD_INDEX, self)
        return -1

    @property
    def bounds(self) -> Rectangle:
        return self._bounds

    @property
    def margin(self) -> Spacing:
        return self._margin

    @property
    def padding(self) -> Spacing:
        return self._padding

    @property
    def is_topmost(self) -> bool:
        return UIRuntime().is_topmost(self)

    @property
    def visible(self) -> bool:
        if self.parent:
            if self.parent.visible:
                return self._visible
        elif self.is_topmost:
            return self._visible
        return False

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    @property
    def enabled(self) -> bool:
        if self.parent:
            if self.parent.enabled:
                return self._enabled
        elif self.is_topmost:
            return self._enabled
        return False

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def location(self) -> Point:
        return self._bounds.location

    @location.setter
    def location(self, value: Point) -> None:
        self._bounds.location = value

    @property
    def position(self) -> Point:
        if self._parent:
            return self.parent.position + self._bounds.location
        return self._bounds.location

    @position.setter
    def position(self, value: Point) -> None:
        if self._parent:
            self._bounds.location = value - self.parent.position
        else:
            self._bounds.location = value

    @property
    def size(self) -> Size:
        return self._bounds.size

    @size.setter
    def size(self, value: Size) -> None:
        width, height = value
        changed: bool = False
        if (self.behavior & BE_FIXED_WIDTH != BE_FIXED_WIDTH) and value != self._bounds.width:
            self._bounds.width = width
            changed = True
        if (self.behavior & BE_FIXED_HEIGHT != BE_FIXED_HEIGHT) and value != self._bounds.height:
            self._bounds.height = height
            changed = True
        if changed:
            self.process_message(Message.SIZECHANGED, Size(width, height))

    @property
    def rectangle(self) -> Rectangle:
        return self._bounds

    @property
    def render_rectangle(self) -> Rectangle:
        return self._bounds.expand(self._render_margin)

    @property
    def is_validating(self) -> bool:
        if self._parent:
            return self._parent.is_validating or self._validating
        elif self.is_topmost:
            return self._validating
        return False

    # remove this later
    # def _auto_layout(self) -> None:
    #     cursor: LayoutCursor = UIRuntime().get_cursor()
    #     if cursor:
    #         lnx: LayoutNext = cursor.next
    #         if cursor.ref:
    #             if lnx is LON_SAMELINE:
    #                 self._bounds.location = Point(
    #                     cursor.ref.bounds.left + self.margin.left, cursor.ref.bounds.top + self.margin.top)
    #                 if cursor.row_bottom < self.bounds.bottom + self.margin.bottom:
    #                     cursor.row_bottom = self.bounds.bottom + self.margin.bottom
    #             elif lnx is LON_BELOW:
    #                 self._bounds.location = Point(
    #                     cursor.ref.bounds.left + self.margin.left, cursor.ref.bounds.bottom + self.margin.top)
    #                 if cursor.row_bottom < self.bounds.bottom + self.margin.bottom:
    #                     cursor.row_bottom = self.bounds.bottom + self.margin.bottom
    #             elif lnx is LON_NEWLINE:
    #                 self._bounds.location = Point(
    #                     self.margin.left, cursor.row_bottom + self.margin.top)
    #                 cursor.row_bottom = self.bounds.bottom + self.margin.bottom
    #         else:
    #             self._bounds.location = self.margin.top_left
    #             cursor.row_bottom = self.bounds.bottom + self.margin.bottom
    #         cursor.ref = self
    #     else:

    def _get_events(self):
        for name in self.__class__.__dict__:
            event = self.__class__.__dict__[name]
            if name != "EventBase" and name.endswith("Event"):
                setattr(self, event.get_handler_name(), event())

        try:
            super()._get_events()
        except AttributeError:
            pass

    def get_state(self) -> str:
        return 'normal'

    def get_topmost(self) -> 'Control':
        if self._parent:
            return self._parent.get_topmost()
        return self

    def client_to_screen_rect(self, rect: Rectangle) -> Rectangle:
        rect: Rectangle = rect.copy()
        rect.location = self.client_to_screen(rect.location)
        return rect

    def local_to_screen_rect(self, rect: Rectangle) -> Rectangle:
        rect: Rectangle = rect.copy()
        rect.location = self.local_to_screen(rect.location)
        return rect

    def client_to_screen(self, point: Point) -> Point:
        if self.parent:
            return self.parent.client_to_screen(self.location) + point
        return self.location + point

    def screen_to_client(self, point: Point) -> Point:
        if self.parent:
            return point - self.parent.client_to_screen(self.location)
        return point - self.location

    def local_to_screen(self, point: Point) -> Point:
        if self.parent:
            return self.parent.client_to_screen(point - self.location)
        return point

    def screen_to_local(self, point: Point) -> Point:
        if self.parent:
            return point - self.parent.client_to_screen(Point(0, 0))
        return point

    def get_bounds(self) -> 'Rectangle':
        return Rectangle.join(self.position, self.size)

    def get_render_bounds(self) -> 'Rectangle':
        return self.get_bounds().expand(self._margin)

    def send_message(self, receiver: 'Control', message: Message, *params) -> Any:
        return receiver.process_message(message, *params)

    def invalidate(self) -> None:
        pass

    #ctrlmsg
    def process_message(self, message: Message, *params) -> Any:
        if message is Message.CREATED:
            handler = getattr(self, '_on_created', lambda sender, evargs: None)
            handler(self, None)

        elif message is Message.HIT_TEST:
            position: Point = params[0]
            if self.get_bounds().contains(position) and self._visible:
                return self, HT_CLIENT
            return None, HT_NONE

        elif message is Message.MOUSE_ENTER:
            # self._on_mouseenter(self, None)
            handler = getattr(self, '_on_mouseenter', lambda sender, evargs: None)
            handler(self, None)
            return True

        elif message is Message.MOUSE_PRESS:
            # self._on_mouseenter(self, None)
            handler = getattr(self, '_on_mousepress', lambda sender, evargs: None)
            handler(self, None)
            return True

        elif message is Message.MOUSE_DOWN:
            # self._on_mouseenter(self, None)
            handler = getattr(self, '_on_mousedown', lambda sender, evargs: None)
            handler(self, None)
            return True

        elif message is Message.MOUSE_RELEASE:
            # self._on_mouseenter(self, None)
            handler = getattr(self, '_on_mouserelease', lambda sender, evargs: None)
            handler(self, None)
            return True

        elif message is Message.MOUSE_LEAVE:
            # self._on_mouseenter(self, None)
            handler = getattr(self, '_on_mouseleave', lambda sender, evargs: None)
            handler(self, None)
            return True

        elif message is Message.MOUSE_HOVER:
            return self._tooltip

        elif message is Message.SELECTED:
            # the control was clicked: whether it can receive focus or not, depends on this message return value
            # return None if it can't (or makes no sense to) receive focus, or a child than can.
            if self.behavior & BE_SELECTABLE == BE_SELECTABLE:
                return self
            return None

        elif message is Message.ERASE_CHILD:
            # this is a child's request for its parent to:
            # a) erase the child's bounds with a erase_color,
            # b) repaint any other child bellow this one that got partially erased
            # c) repaint the child
            # if the control is a topmost, then simply erase itself and repaint
            if self._is_topmost:
                region: Rectangle = params[0]   # not in screen
                region = self.local_to_screen_rect(region)
                renderer: RendererBase = Application().get_renderer()
                erase_color: Color = renderer.erase_color
                renderer.erase(self, region, erase_color)
            elif self.parent:
                self.parent.process_message(Message.ERASE_CHILD, child*params)

        if message is Message.RENDER_BACKGROUND:
            renderer: RendererBase = Application().get_renderer()
            if not renderer.get_render_layers(self) & RL_BACKGROUND == RL_BACKGROUND:
                return True
            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            renderer.render(self, render_bounds, bounds, RL_BACKGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True

        elif message is Message.RENDER:
            renderer: RendererBase = Application().get_renderer()
            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)
            rendered: bool = False
            layer: RenderLayer = renderer.get_render_layers(self)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            if layer & RL_ABOVE_BACKGROUND == RL_ABOVE_BACKGROUND:
                renderer.render(self, render_bounds, bounds, RL_ABOVE_BACKGROUND)
                rendered = True
            if layer & RL_BELOW_FOREGROUND == RL_BELOW_FOREGROUND:
                if rendered:
                    this = GrUsInRendererError(
                        "RenderLayer: {cls} rendering must occur only ABOVE_BACKGROUND or BELOW_FOREGROUND.".format(
                            cls=self.__class__.__name__))
                    raise this
                renderer.render(self, render_bounds, bounds, RL_BELOW_FOREGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True

        elif message is Message.RENDER_FOREGROUND:
            renderer: RendererBase = Application().get_renderer()
            if not renderer.get_render_layers(self) & RL_FOREGROUND == RL_FOREGROUND:
                return True

            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            renderer.render(self, render_bounds, bounds, RL_FOREGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True


class ButtonBase(Control):

    _behavior = BE_SELECTABLE

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super(ButtonBase, self).__init__(parent, name, **kwargs)

        self._pressed_state: ButtonPressedState = BPS_NORMAL
        self._toggle_state: ButtonToggleState = BTS_OFF
        self._text: str = self._name

    @property
    def text(self) -> str:
        return self._text

    @property
    def pressed_state(self) -> ButtonPressedState:
        return self._pressed_state

    def get_state(self) -> str:
        if self.enabled:
            return {
                BPS_NORMAL: 'normal',
                BPS_HILIGHTED: 'hilighted',
                BPS_PRESSED: 'pressed',
            }.get(self._pressed_state, 'normal')
        else:
            return 'disabled'

    def process_message(self, message: Message, *params) -> Any:

        if message is Message.MOUSE_ENTER:
            if self.enabled:
                self._pressed_state = BPS_HILIGHTED

        elif message is Message.MOUSE_PRESS:
            if self.enabled:
                self._pressed_state = BPS_PRESSED

        elif message is Message.MOUSE_RELEASE:
            if self.enabled:
                is_hovering: bool = params[0]
                if is_hovering:
                    self._pressed_state = BPS_HILIGHTED
                else:
                    self._pressed_state = BPS_NORMAL

        elif message is Message.MOUSE_LEAVE:
            if self.enabled:
                self._pressed_state = BPS_NORMAL

        return super().process_message(message, *params)


# pbtn
class PushButton(ButtonBase):

    class PressedEvent(EventBase):
        pass

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super(PushButton, self).__init__(parent, name, **kwargs)
        renderer: RendererBase = Application().get_renderer()
        self._padding = Spacing(*renderer.get_element(self).layout.padding)
        size: Size = renderer.measure_text(self, self.text)
        self._bounds.size = size
        self._bounds.expand(self._padding)

    def process_message(self, message: Message, *params) -> Any:

        if message is Message.MOUSE_RELEASE:
            if self.enabled:
                is_hovering: bool = params[0]
                if is_hovering:
                    self._pressed_state = BPS_HILIGHTED
                    self._on_pressed(self, None)
                else:
                    self._pressed_state = BPS_NORMAL

        return super().process_message(message, *params)


# cbx
class CheckBox(ButtonBase):

    class CheckedEvent(EventBase):
        pass

    class UncheckedEvent(EventBase):
        pass

    class CheckChangedEvent(EventBase):
        pass

    _behavior = Control._behavior | BE_FIXED_HEIGHT

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super().__init__(parent, name, **kwargs)

        self.checked = False

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self.process_message(Message.TEXTCHANGED, value)

    @property
    def check_state(self) -> CheckBoxState:
        return {
            BTS_OFF: CBS_UNCHECKED,
            BTS_ON: CBS_CHECKED,
            BTS_UNDEFINED: CBS_UNDFINED
        }.get(self._toggle_state, CBS_UNDFINED)

    @property
    def checked(self) -> bool:
        return self.check_state is CBS_CHECKED

    @checked.setter
    def checked(self, value: bool) -> None:
        if value:
            self._toggle_state = BTS_ON
        else:
            self._toggle_state = BTS_OFF

    def check(self) -> None:
        if self.check_state is not CBS_CHECKED:
            self._toggle_state = BTS_ON
            self._on_checked(self, None)

    def uncheck(self) -> None:
        if self.check_state is not CBS_UNCHECKED:
            self._toggle_state = BTS_OFF
            self._on_unchecked(self, None)

    def _get_base_size(self, text: str) -> Size:
        renderer: RendererBase = Application().get_renderer()
        size: Size = renderer.measure_text(self, text)
        size.width += self._padding.hor
        size.height += self._padding.ver
        size.width += size.height
        return size

    def process_message(self, message: Message, *params) -> Any:
        if message is Message.MOUSE_RELEASE:
            if self.enabled:
                is_hovering: bool = params[0]
                if is_hovering:
                    self._pressed_state = BPS_HILIGHTED
                    if self._toggle_state is BTS_ON:
                        self._toggle_state = BTS_OFF
                        self._on_unchecked(self, None)
                    else:
                        self._toggle_state = BTS_ON
                        self._on_checked(self, None)
                    self._on_checkchanged(self, EventArgs(check_state=CBS_CHECKED))
                else:
                    self._pressed_state = BPS_NORMAL

        elif message is Message.TEXTCHANGED:
            text: str = params[0]
            self.size = self._get_base_size(text)

        elif message is Message.SIZECHANGED:
            size: Size = params[0]
            if self.is_topmost:
                UIRuntime().erase(self, Rectangle.join(self.location, size))
            elif self._parent:
                self.parent.process_message(Message.ERASE_CHILD, self, size)
            base_size: Size = self._get_base_size(self._text)
            if size.height != base_size.height:
                size.height = base_size.height
            if size.width < base_size.width:
                size.width = base_size.width
            self._bounds.size = size

        else:
            return super().process_message(message, *params)


# rbtn
class RadioButton(ButtonBase):

    class CheckedEvent(EventBase):
        pass

    class UncheckedEvent(EventBase):
        pass

    class CheckChangedEvent(EventBase):
        pass

    _behavior = Control._behavior | BE_FIXED_HEIGHT

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super().__init__(parent, name, **kwargs)

        self.checked = False

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            self.process_message(Message.TEXTCHANGED, value)

    @property
    def check_state(self) -> CheckBoxState:
        return {
            BTS_OFF: CBS_UNCHECKED,
            BTS_ON: CBS_CHECKED,
            BTS_UNDEFINED: CBS_UNDFINED
        }.get(self._toggle_state, CBS_UNDFINED)

    @property
    def checked(self) -> bool:
        return self.check_state is CBS_CHECKED

    @checked.setter
    def checked(self, value: bool) -> None:
        if value:
            self._toggle_state = BTS_ON
        else:
            self._toggle_state = BTS_OFF

    def check(self) -> None:
        if self.check_state is not CBS_CHECKED:
            self._toggle_state = BTS_ON
            self._on_checked(self, None)

    def uncheck(self) -> None:
        if self.check_state is not CBS_UNCHECKED:
            self._toggle_state = BTS_OFF
            self._on_unchecked(self, None)

    def _get_base_size(self, text: str) -> Size:
        renderer: RendererBase = Application().get_renderer()
        size: Size = renderer.measure_text(self, text)
        size.width += self._padding.hor
        size.height += self._padding.ver
        size.width += size.height
        return size

    def process_message(self, message: Message, *params) -> Any:
        if message is Message.MOUSE_RELEASE:
            if self.enabled:
                is_hovering: bool = params[0]
                if is_hovering:
                    self._pressed_state = BPS_HILIGHTED
                    if self._toggle_state is BTS_OFF:
                        self._toggle_state = BTS_ON
                        self._on_checked(self, None)
                    # self._on_checkchanged(self, EventArgs(check_state=CBS_CHECKED))
                else:
                    self._pressed_state = BPS_NORMAL

        elif message is Message.TEXTCHANGED:
            text: str = params[0]
            self.size = self._get_base_size(text)

        elif message is Message.SIZECHANGED:
            size: Size = params[0]
            if self.is_topmost:
                UIRuntime().erase(self, Rectangle.join(self.location, size))
            elif self._parent:
                self.parent.process_message(Message.ERASE_CHILD, self, size)
            base_size: Size = self._get_base_size(self._text)
            if size.height != base_size.height:
                size.height = base_size.height
            if size.width < base_size.width:
                size.width = base_size.width
            self._bounds.size = size

        else:
            return super().process_message(message, *params)


class BarBase(Control):
    # serve as base for scrollbars, sliderbar, progressbar

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super().__init__(parent, name, **kwargs)
        self._minimum: int = 0
        self._maximum: int = 0
        self._value: int = 0
        self._small_value: int = 25
        self._large_value: int = 100
        self._increment: int = 1


    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        self._value = value

    @property
    def minimum(self) -> int:
        return self._minimum

    @minimum.setter
    def minimum(self, value: int) -> None:
        if value > self._maximum:
            raise ValueError("Minimum value must be smaller than maximum.")
        self._minimum = value

    @property
    def maximum(self) -> int:
        return self._maximum

    @maximum.setter
    def maximum(self, value: int) -> None:
        if value < self._minimum:
            raise ValueError("Maximum value must be larger than minimum.")
        self._maximum = value

    @property
    def length(self) -> int:
        return self._maximum - self._minimum

    @property
    def scroll_length(self) -> int:
        return self._large_value - self._small_value

    @property
    def scroll_pos(self) -> int:
        return int((self._value / self.length) * self.scroll_length)

    @scroll_pos.setter
    def scroll_pos(self, value: Union[int, float]) -> None:
        pos = max(0, min(value, self.scroll_length))
        self._value = (pos / self.scroll_length) * self.length


class VScrollBar(BarBase):

    _behavior: Behavior = Control._behavior |= BE_NON_CLIENT

    class VSUpButton(ButtonBase):

        def __init__(self, owner: 'VScrollbar'=None, name: str=DEFAULT, **kwargs) -> None:
            super().__init__(None, name)
            self._owner: VScrollbar = owner

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        super().__init__(parent, name, **kwargs)
        self._up_button: VScrollbar.VSUpButton = 


class ContainerControl(Control):
    # can be parent of (can contain) other controls (client and non-client)

    _behavior: Behavior = BE_SELECTABLE

    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        # client controls (children)
        self._children: List[Control] = []
        self._selected: int = -1    # index of the child with
        super().__init__(parent, name, **kwargs)

    def __getattr__(self, name: str) -> 'Control':
        child = self.find_by_name(name)
        if not child:
            raise AttributeError(
                "{cls} object has no attribute {name}".format(cls=self.__class__.__name__, name=name))
        return child

    @property
    def selected_child(self) -> Optional['Control']:
        if len(self._children):
            if 0 <= self._selected < len(self._children):
                child: Optional['Control'] = self._children[self._selected]
                if child:
                    return child.selected_child
        self._selected = -1
        return super(ContainerControl, self).selected_child

    def find_by_name(self, name: str) -> Optional['Control']:
        for control in self._children:
            if control.name == name:
                return control
        return None

    # ctnrmsg
    def process_message(self, message: Message, *params):

        if message is Message.HIT_TEST:
            position: Point = params[0]
            ht_object: Optional[Control] = None
            ht_result: HitTest = HT_NONE
            if self.get_bounds().contains(position) and self._visible:
                ht_object = self
                ht_result = HT_CLIENT
                for child in self._children:
                    hit, hittest = child.process_message(message, *params)
                    if hit:
                        ht_object = hit
                        ht_result = hittest

            return ht_object, ht_result

        elif message is Message.CHILD_INDEX:
            child: 'Control' = params[0]
            if child in self._children:
                return self._children.index(child)
            else:
                return -1

        elif message is Message.ADD_CHILD:
            child: 'Control' = params[0]
            if child not in self._children:
                self._children.append(child)
            return True

        elif message is Message.REMOVE_CHILD:
            child: 'Control' = params[0]
            if child in self._children:
                if self._selected >= 0 and self._children.index(child) <= self._selected:
                    self._selected -= 1
                self._children.remove(child)

        elif message is Message.REMOVE_CHILDREN:
            self._children.clear()
            self._selected = -1
            # self.invalidate()

        elif message is Message.LAYOUT_CHILDREN:
            cursor: Optional[LayoutCursor] = params[0]
            left: int = self.padding.left
            top: int = self.padding.top
            bottom: int = self.padding.top
            previous: Control = None
            for child, layout in cursor:
                if child not in self._children:
                    continue

                if not previous:
                    child.location = Point(left + child.margin.left, top + child.margin.top)
                    if bottom < child.bounds.bottom + child.margin.bottom:
                        bottom = child.bounds.bottom + child.margin.bottom
                else:
                    if layout is LON_SAMELINE:
                        child.bounds.left = previous.bounds.right + previous.margin.right + child.margin.left
                        child.bounds.top = top + child.margin.top
                        if bottom < child.bounds.bottom + child.margin.bottom:
                            bottom = child.bounds.bottom + child.margin.bottom

                    elif layout is LON_BELOW:
                        child.bounds.left = previous.bounds.left - previous.margin.left + child.margin.left
                        child.bounds.top = previous.bounds.bottom + previous.margin.bottom + child.margin.top
                        if bottom < child.bounds.bottom + child.margin.bottom:
                            bottom = child.bounds.bottom + child.margin.bottom

                    elif layout is LON_CASCADE:
                        child.bounds.left = previous.bounds.left + 32
                        child.bounds.top = previous.bounds.top + 32
                        if bottom < child.bounds.bottom + child.margin.bottom:
                            bottom = child.bounds.bottom + child.margin.bottom

                    elif layout is LON_NEWLINE:
                        child.bounds.left = left + child.margin.left
                        child.bounds.top = bottom + child.margin.top
                        bottom = child.bounds.bottom + child.margin.bottom

                    elif layout is LON_MANUAL:
                        pass        # do nothing...

                # child.process_message(Message.LAYOUT_POS, left, top)
                previous = child

        elif message is Message.SELECT:
            child: 'Control' = params[0]
            if child in self._children:
                self._selected = self._children.index(child)
                return True
            else:
                return False
        elif message is Message.ERASE_CHILD:
            # this is a child's request for its parent to:
            # a) erase the child's bounds with a erase_color,
            # b) repaint any other child bellow this one that got partially erased
            # c) repaint the child
            # raise NotImplementedError("It is about time to implement this.")
            child_to_erase: Control = params[0]
            size: Size = params[1]
            erase_rect: Rectangle = Rectangle.join(child_to_erase.position, size)
            erase_region: Rectangle = erase_rect.intersection(self.get_bounds())

            self.process_message(Message.RENDER_BACKGROUND, erase_region)
            self.process_message(Message.RENDER, erase_region)
            self.process_message(Message.RENDER_FOREGROUND, erase_region)

        elif message is Message.SELECTED:
            # the control was clicked: whether it can receive focus or not, depends on this message return value
            # return None if it can't (or makes no sense to) receive focus, or a child than can.
            if self.behavior & BE_SELECTABLE == BE_SELECTABLE:
                return self
            else:
                selected: Optional['Control'] = None
                for child in self._children:
                    sel = child.process_message(message)
                    if sel:
                        selected = sel
                        break
                return selected

        elif message is Message.RENDER_BACKGROUND:
            renderer: RendererBase = Application().get_renderer()
            if not renderer.get_render_layers(self) & RL_BACKGROUND == RL_BACKGROUND:
                return True
            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            renderer.render(self, render_bounds, bounds, RL_BACKGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True

        elif message is Message.RENDER:
            renderer: RendererBase = Application().get_renderer()
            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)
            rendered: bool = False
            layer: RenderLayer = renderer.get_render_layers(self)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            if layer & RL_ABOVE_BACKGROUND == RL_ABOVE_BACKGROUND:
                renderer.render(self, render_bounds, bounds, RL_ABOVE_BACKGROUND)
                rendered = True
            for child in self._children:
                child_render_bounds: Rectangle = child.get_bounds().expand(child.padding)
                if render_bounds.intersects(child_render_bounds) and child.visible:
                    child.process_message(message.RENDER_BACKGROUND, render_bounds)
                    child.process_message(message.RENDER, render_bounds)
                    child.process_message(message.RENDER_FOREGROUND, render_bounds)
                else:
                    raise RuntimeError()
            if layer & RL_BELOW_FOREGROUND == RL_BELOW_FOREGROUND:
                if rendered:
                    this = GrUsInRendererError(
                        "RenderLayer: {cls} rendering must occur only ABOVE_BACKGROUND or BELOW_FOREGROUND.".format(
                            cls=self.__class__.__name__))
                    raise this
                renderer.render(self, render_bounds, bounds, RL_BELOW_FOREGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True

        elif message is Message.RENDER_FOREGROUND:
            renderer: RendererBase = Application().get_renderer()
            if not renderer.get_render_layers(self) & RL_FOREGROUND == RL_FOREGROUND:
                return True

            clip_area: Rectangle = params[0]  # received from the parent
            render_bounds: Rectangle = self.get_render_bounds()
            bounds: Rectangle = self.get_bounds()
            invalidated: Rectangle = clip_area.intersection(render_bounds)

            if invalidated.empty:
                return True
            renderer.add_invalidated_rect(invalidated)

            renderer.push_cliprect(invalidated) # ensure it is in screen coordinates!
            # render code begins here
            renderer.render(self, render_bounds, bounds, RL_FOREGROUND)
            # render code ends here
            renderer.pop_cliprect()

            return True

        else:
            return super().process_message(message, *params)


# pnl
class Panel(ContainerControl):

    _behavior: Behavior = ContainerControl._behavior

    # def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
    #     super().__init__(parent, name, **kwargs)

    def get_state(self) -> str:
        return 'normal' if not self.enabled else 'disabled'


class ScrollableControl(ContainerControl):
    # has display_bounds, scroll_position, scrollbars (non-clients)
    # not necessarily a container
    def __init__(self, parent: 'ContainerControl'=DEFAULT, name: str=DEFAULT, **kwargs) -> None:
        # client/display bounds and scrolling
        self._display_bounds: Rectangle = Rectangle(0, 0, 32, 32)
        # non-client controls
        self._scrollbars: Scrollbars = SB_AUTO
        self._vscrollbar: 'VScrollbar' = None
        self._hscrollbar: 'HScrollbar' = None

        super(ScrollableControl, self).__init__(parent, name, **kwargs)


if __name__ == '__main__':
    with Application().start(main_form='form1'):

        # WARNING: the `this` global variable is valid only during
        #          the initialization context of controls and is
        #          meant only for reading.
        #          Assigning any value to it may cause unexpected
        #          results.
        with Panel(name="form1"):
            this.location = Point(50, 30)
            this.size = Point(500, 300)
            this.visible = True

            @Panel.MouseEnterEvent.handler
            def mouse_enter(sender: Panel, evargs: EventArgs) -> None:
                pass

            @Panel.MouseLeaveEvent.handler
            def mouse_leave(sender: Panel, evargs: EventArgs) -> None:
                pass

            with CheckBox(layout=LON_BELOW):
                # this.location = Point(10, 130)
                this.text = "A checkbox control."

                @CheckBox.CheckedEvent.handler
                def mouse_enter(sender: CheckBox, evargs: EventArgs) -> None:
                    pass

            with PushButton():
                # this.location = Point(10, 20)
                # this.size = Size(110, 20)

                @PushButton.MouseEnterEvent.handler
                def mouse_enter_again(sender: PushButton, evargs: EventArgs) -> None:
                    pass

        with Panel(layout=LON_CASCADE):
            # this.location = Point(250, 150)
            this.size = Point(500, 300)
            # this.enabled = False

            @Panel.MouseEnterEvent.handler
            def mouse_enter(sender: Panel, evargs: EventArgs) -> None:
                pass

            @Panel.MouseLeaveEvent.handler
            def mouse_leave(sender: Panel, evargs: EventArgs) -> None:
                pass

            with PushButton():
                # this.location = Point(10, 20)
                # this.size = Size(110, 20)

                @PushButton.PressedEvent.handler
                def mouse_enter_again(sender: PushButton, evargs: EventArgs) -> None:
                    sys.exit()

            with PushButton(layout=LON_BELOW):
                # this.location = Point(10, 20)
                # this.size = Size(110, 20)

                @PushButton.PressedEvent.handler
                def mouse_leave_again(sender: PushButton, evargs: EventArgs) -> None:
                    sender.parent.pushbutton1.enabled = False

            with CheckBox(layout=LON_SAMELINE):
                # this.location = Point(10, 130)
                this.text = "This is a checkbox control"

                @CheckBox.CheckChangedEvent.handler
                def mouse_enter(sender: CheckBox, evargs: EventArgs) -> None:
                    # sender.text = repr(pg.time.get_ticks())
                    sender.parent.pushbutton2.enabled = sender.checked

            with RadioButton(layout=LON_NEWLINE):
                # this.location = Point(10, 130)
                this.text = "This is {}".format(this.name)

                @RadioButton.CheckChangedEvent.handler
                def mouse_enter(sender: RadioButton, evargs: EventArgs) -> None:
                    # sender.text = repr(pg.time.get_ticks())
                    #sender.parent.pushbutton2.enabled = sender.checked
                    pass

            with RadioButton(layout=LON_BELOW):
                # this.location = Point(10, 130)
                this.text = "This is {}".format(this.name)

                @RadioButton.CheckChangedEvent.handler
                def mouse_enter(sender: RadioButton, evargs: EventArgs) -> None:
                    # sender.text = repr(pg.time.get_ticks())
                    #sender.parent.pushbutton2.enabled = sender.checked
                    pass

            with RadioButton(layout=LON_BELOW):
                # this.location = Point(10, 130)
                this.text = "This is {}".format(this.name)

                @RadioButton.CheckChangedEvent.handler
                def mouse_enter(sender: RadioButton, evargs: EventArgs) -> None:
                    # sender.text = repr(pg.time.get_ticks())
                    #sender.parent.pushbutton2.enabled = sender.checked
                    pass

