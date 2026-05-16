"""刷向阳花任务流程。

1. 激活洛克王国窗口并刷新截图尺寸，用于把资源坐标映射到屏幕坐标。
2. 完整前置模式先打开地图、点击中心和传送区域，再依次按 1/3/4/5/6 并左键交互。
3. 进入鞠躬循环：按 2 等待动作完成，循环执行 TAB -> 2 -> ESC -> R -> 可选随机停顿/鼠标微动 -> X。
4. 每个等待和按键动作都会检查任务停止标记，保证点击“停止任务”时能尽快退出。
"""

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


def _should_stop(context):
    return bool(getattr(context.tasker, "stopping", False))


def _sleep_ms(context, min_ms, max_ms=None):
    # 长等待拆成 50ms 小片段，这样停止任务时不用等完整随机延迟结束。
    if max_ms is None:
        max_ms = min_ms
    total_ms = random.randint(int(min_ms), int(max_ms))
    end_time = time.monotonic() + total_ms / 1000.0
    while time.monotonic() < end_time:
        if _should_stop(context):
            return False
        remaining = max(0.0, end_time - time.monotonic())
        time.sleep(min(0.05, remaining))
    return True


def _press_key(context, ic, key, hold_min=80, hold_max=120):
    # Interception 发送真实键盘事件：按下、保持随机时长、松开。
    if _should_stop(context):
        return False
    vk = VK[key]
    if not ic.key_down(vk):
        print(f"[Sunflower] key_down failed: {key}")
        return False
    if not _sleep_ms(context, hold_min, hold_max):
        ic.key_up(vk)
        return False
    if not ic.key_up(vk):
        print(f"[Sunflower] key_up failed: {key}")
        return False
    return True


def _click_left(context, ic, hold_min=80, hold_max=120):
    # 鼠标左键同样拆成 down/up，便于模拟 AHK 里的随机按住时间。
    if _should_stop(context):
        return False
    if not ic.left_down(delay=0):
        print("[Sunflower] left_down failed")
        return False
    if not _sleep_ms(context, hold_min, hold_max):
        ic.left_up(delay=0)
        return False
    if not ic.left_up(delay=0):
        print("[Sunflower] left_up failed")
        return False
    return True


def _refresh_image_size(context):
    # 每轮关键点击前刷新截图尺寸，防止窗口缩放后坐标映射漂移。
    ctrl = context.tasker.controller
    ctrl.post_screencap().wait()
    _update_image_size(ctrl)
    return get_controller().image_width, get_controller().image_height


def _click_point(context, ic, x, y):
    if _should_stop(context):
        return False
    if not ic.click(int(round(x)), int(round(y))):
        print(f"[Sunflower] click failed: ({x}, {y})")
        return False
    return True


def _click_percent(context, ic, width, height, min_x, max_x, min_y, max_y):
    x = random.uniform(min_x, max_x) * width
    y = random.uniform(min_y, max_y) * height
    return _click_point(context, ic, x, y)


def _random_mouse_jitter(context, ic):
    if _should_stop(context):
        return False
    dx = random.randint(-20, 20)
    dy = random.randint(-20, 20)
    return ic.move_relative(dx, dy, delay=random.uniform(0.02, 0.05))


@AgentServer.custom_action("SunflowerCycleAct")
class SunflowerCycleAct(CustomAction):
    """Runs one sunflower farming cycle ported from luoke_mode2.ahk."""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # Pipeline 每次命中 Sunflower_Entry 都执行一个完整周期，再由 next 回到自身循环。
        node_obj = context.get_node_object("Sunflower_Entry")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        mode = attach.get("mode", "full")

        ic = get_controller()
        ic.activate_window()
        width, height = _refresh_image_size(context)

        print(f"[Sunflower] start cycle, mode={mode}, image={width}x{height}")

        if mode == "full":
            if not self._run_prelude(context, ic, width, height):
                return False
        else:
            if not _sleep_ms(context, 150, 250):
                return False

        return self._run_bow_cycle(context, ic)

    def _run_prelude(self, context, ic, width, height):
        # 完整前置：打开地图、传送到刷花区域，并按宠物/交互键做准备动作。
        print("[Sunflower] prelude: press M")
        if not _press_key(context, ic, "M"):
            return False
        if not _sleep_ms(context, 1300, 1500):
            return False

        width, height = _refresh_image_size(context)
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-5, 5)
        print("[Sunflower] prelude: click center")
        if not _click_point(context, ic, width / 2 + offset_x, height / 2 + offset_y):
            return False
        if not _sleep_ms(context, 500, 700):
            return False

        print("[Sunflower] prelude: click bottom-right teleport area")
        if not _click_percent(context, ic, width, height, 0.66875, 0.92375, 0.9255, 0.9600):
            return False
        if not _sleep_ms(context, 10000):
            return False

        for key in ("1", "3", "4", "5", "6"):
            # 这些按键和左键点击来自原 AHK 的前置交互序列。
            print(f"[Sunflower] prelude: summon/interact key {key}")
            if not _press_key(context, ic, key):
                return False
            if not _sleep_ms(context, 1000, 1200):
                return False
            if not _click_left(context, ic):
                return False
            if not _sleep_ms(context, 1000, 1200):
                return False
        return True

    def _run_bow_cycle(self, context, ic):
        # 鞠躬主体：用随机循环次数和随机停顿降低固定节奏感。
        print("[Sunflower] bow: initial key 2")
        if not _press_key(context, ic, "2", 180, 240):
            return False
        if not _sleep_ms(context, 3800, 4200):
            return False

        loop_count = random.randint(5, 8)
        print(f"[Sunflower] bow: loop {loop_count} times")

        for _ in range(loop_count):
            # 单轮顺序：切目标/菜单 -> 鞠躬动作 -> 退出界面 -> 恢复/刷新 -> 可选扰动 -> 聚能键。
            if not _press_key(context, ic, "TAB", 80, 240):
                return False
            if not _sleep_ms(context, 900, 1100):
                return False

            if not _press_key(context, ic, "2", 180, 240):
                return False
            if not _sleep_ms(context, 3800, 4200):
                return False

            if not _press_key(context, ic, "ESC", 80, 120):
                return False
            if not _sleep_ms(context, 450, 850):
                return False

            if not self._press_random_repeat(context, ic, "R"):
                return False
            if not _sleep_ms(context, 10500, 18000):
                return False

            if random.randint(1, 100) <= 18:
                print("[Sunflower] bow: idle pause")
                if not _sleep_ms(context, 25000, 55000):
                    return False

            if random.randint(1, 100) <= 8:
                print("[Sunflower] bow: mouse jitter")
                if not _random_mouse_jitter(context, ic):
                    return False

            if not self._run_optional_groups(context, ic):
                return False

            if not self._press_random_repeat(context, ic, "X", rand_min=36, rand_max=100):
                return False
            if not _sleep_ms(context, 400, 1400):
                return False

        if random.randint(1, 100) <= 33:
            print("[Sunflower] bow: extra group 4")
            if not self._extra_group_4(context, ic):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False

        if random.randint(1, 100) <= 32:
            print("[Sunflower] bow: long rest")
            return _sleep_ms(context, 15000, 30000)
        else:
            print("[Sunflower] bow: short rest")
            return _sleep_ms(context, 5000, 15000)

    def _press_random_repeat(self, context, ic, key, rand_min=1, rand_max=100):
        # 少量概率连按 2-3 次，复刻原脚本里的随机补按。
        roll = random.randint(rand_min, rand_max)
        presses = 2 if roll <= 25 else (3 if roll <= 35 else 1)
        print(f"[Sunflower] key {key} x{presses}")
        for index in range(presses):
            if not _press_key(context, ic, key):
                return False
            if index < presses - 1:
                if not _sleep_ms(context, 200, 700):
                    return False
        return True

    def _run_optional_groups(self, context, ic):
        # 低概率插入额外操作组，让长时间刷花的动作节奏不完全固定。
        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 1: M wait M")
            if not _press_key(context, ic, "M"):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False
            if not _press_key(context, ic, "M"):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False

        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 2: Esc wait Esc")
            if not _press_key(context, ic, "ESC", 70, 170):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False
            if not _press_key(context, ic, "ESC", 70, 170):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False

        if random.randint(1, 100) <= 4:
            print("[Sunflower] extra group 3: F2 wait Esc")
            if not _press_key(context, ic, "F2", 70, 170):
                return False
            if not _sleep_ms(context, 2000):
                return False
            if not _press_key(context, ic, "ESC", 70, 170):
                return False
            if not _sleep_ms(context, 2000, 3000):
                return False
        return True

    def _extra_group_4(self, context, ic):
        # 短促移动键组合，用于偶尔调整角色朝向/站位。
        if not _press_key(context, ic, "D", 0, 0):
            return False
        if not _sleep_ms(context, 80, 120):
            return False
        if not _press_key(context, ic, "S", 0, 0):
            return False
        if not _sleep_ms(context, 80, 120):
            return False
        return _press_key(context, ic, "W", 0, 0)
