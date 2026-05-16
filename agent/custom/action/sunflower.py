import random
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size


VK = {
    "ESC": 0x1B,
    "TAB": 0x09,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "D": 0x44,
    "F2": 0x71,
    "M": 0x4D,
    "R": 0x52,
    "S": 0x53,
    "W": 0x57,
    "X": 0x58,
}


def _sleep_ms(min_ms, max_ms=None):
    if max_ms is None:
        max_ms = min_ms
    time.sleep(random.randint(int(min_ms), int(max_ms)) / 1000.0)


def _press_key(ic, key, hold_min=80, hold_max=120):
    vk = VK[key]
    ic.key_down(vk)
    _sleep_ms(hold_min, hold_max)
    ic.key_up(vk)


def _click_left(ic, hold_min=80, hold_max=120):
    ic.left_down(delay=0)
    _sleep_ms(hold_min, hold_max)
    ic.left_up(delay=0)


def _refresh_image_size(context):
    ctrl = context.tasker.controller
    ctrl.post_screencap().wait()
    _update_image_size(ctrl)
    return get_controller().image_width, get_controller().image_height


def _click_point(ic, x, y):
    ic.click(int(round(x)), int(round(y)))


def _click_percent(ic, width, height, min_x, max_x, min_y, max_y):
    x = random.uniform(min_x, max_x) * width
    y = random.uniform(min_y, max_y) * height
    _click_point(ic, x, y)


def _random_mouse_jitter(ic):
    dx = random.randint(-20, 20)
    dy = random.randint(-20, 20)
    ic.move_relative(dx, dy, delay=random.uniform(0.02, 0.05))


@AgentServer.custom_action("SunflowerCycleAct")
class SunflowerCycleAct(CustomAction):
    """Runs one sunflower farming cycle ported from luoke_mode2.ahk."""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        node_obj = context.get_node_object("Sunflower_Entry")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        mode = attach.get("mode", "full")

        ic = get_controller()
        width, height = _refresh_image_size(context)

        print(f"[Sunflower] start cycle, mode={mode}, image={width}x{height}")

        if mode == "full":
            self._run_prelude(context, ic, width, height)
        else:
            _sleep_ms(150, 250)

        self._run_bow_cycle(ic)
        return True

    def _run_prelude(self, context, ic, width, height):
        print("[Sunflower] prelude: press M")
        _press_key(ic, "M")
        _sleep_ms(1300, 1500)

        width, height = _refresh_image_size(context)
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        print("[Sunflower] prelude: click center")
        _click_point(ic, width / 2 + offset_x, height / 2 + offset_y)
        _sleep_ms(500, 700)

        print("[Sunflower] prelude: click bottom-right teleport area")
        _click_percent(ic, width, height, 0.66875, 0.92375, 0.9255, 0.9600)
        _sleep_ms(10000)

        for key in ("1", "3", "4", "5", "6"):
            print(f"[Sunflower] prelude: summon/interact key {key}")
            _press_key(ic, key)
            _sleep_ms(1000, 1200)
            _click_left(ic)
            _sleep_ms(1000, 1200)

    def _run_bow_cycle(self, ic):
        print("[Sunflower] bow: initial key 2")
        _press_key(ic, "2", 180, 240)
        _sleep_ms(3800, 4200)

        loop_count = random.randint(5, 8)
        print(f"[Sunflower] bow: loop {loop_count} times")

        for _ in range(loop_count):
            _press_key(ic, "TAB", 80, 240)
            _sleep_ms(900, 1100)

            _press_key(ic, "2", 180, 240)
            _sleep_ms(3800, 4200)

            _press_key(ic, "ESC", 80, 120)
            _sleep_ms(450, 850)

            self._press_random_repeat(ic, "R")
            _sleep_ms(10500, 18000)

            if random.randint(1, 100) <= 18:
                print("[Sunflower] bow: idle pause")
                _sleep_ms(25000, 55000)

            if random.randint(1, 100) <= 8:
                print("[Sunflower] bow: mouse jitter")
                _random_mouse_jitter(ic)

            self._run_optional_groups(ic)

            self._press_random_repeat(ic, "X", rand_min=36, rand_max=100)
            _sleep_ms(400, 1400)

        if random.randint(1, 100) <= 33:
            print("[Sunflower] bow: extra group 4")
            self._extra_group_4(ic)
            _sleep_ms(2000, 3000)

        if random.randint(1, 100) <= 32:
            print("[Sunflower] bow: long rest")
            _sleep_ms(15000, 30000)
        else:
            print("[Sunflower] bow: short rest")
            _sleep_ms(5000, 15000)

    def _press_random_repeat(self, ic, key, rand_min=1, rand_max=100):
        roll = random.randint(rand_min, rand_max)
        presses = 2 if roll <= 25 else (3 if roll <= 35 else 1)
        print(f"[Sunflower] key {key} x{presses}")
        for index in range(presses):
            _press_key(ic, key)
            if index < presses - 1:
                _sleep_ms(200, 700)

    def _run_optional_groups(self, ic):
        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 1: M wait M")
            _press_key(ic, "M")
            _sleep_ms(2000, 3000)
            _press_key(ic, "M")
            _sleep_ms(2000, 3000)

        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 2: Esc wait Esc")
            _press_key(ic, "ESC", 70, 170)
            _sleep_ms(2000, 3000)
            _press_key(ic, "ESC", 70, 170)
            _sleep_ms(2000, 3000)

        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 3: F2 wait Esc")
            _press_key(ic, "F2", 70, 170)
            _sleep_ms(2000)
            _press_key(ic, "ESC", 70, 170)
            _sleep_ms(2000, 3000)

    def _extra_group_4(self, ic):
        _press_key(ic, "D", 0, 0)
        _sleep_ms(80, 120)
        _press_key(ic, "S", 0, 0)
        _sleep_ms(80, 120)
        _press_key(ic, "W", 0, 0)
