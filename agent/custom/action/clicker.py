"""随机连点器任务流程。

1. 每次进入 RandomClicker_Entry 时激活游戏窗口。
2. 在当前鼠标位置按下左键，随机保持 30-60ms 后松开。
3. 随机等待 800-1200ms，再由 pipeline 回到入口继续下一次点击。
4. 等待过程中持续检查停止标记，避免点击“停止任务”后还继续连点。
"""

import random
import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller


def _should_stop(context):
    return bool(getattr(context.tasker, "stopping", False))


def _sleep_ms(context, min_ms, max_ms=None):
    # 把随机间隔拆短，停止任务时可以在下一小段等待前退出。
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


@AgentServer.custom_action("RandomClickerAct")
class RandomClickerAct(CustomAction):
    """Random left clicker ported from luoke_clicker.ahk."""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 参数默认来自 clicker pipeline 的 attach，后续如果开放 UI 配置也会走这里。
        node_obj = context.get_node_object("RandomClicker_Entry")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}

        hold_min = int(attach.get("hold_min", 30))
        hold_max = int(attach.get("hold_max", 60))
        interval_min = int(attach.get("interval_min", 800))
        interval_max = int(attach.get("interval_max", 1200))

        ic = get_controller()
        ic.activate_window()

        print(
            "[RandomClicker] click "
            f"hold={hold_min}-{hold_max}ms interval={interval_min}-{interval_max}ms"
        )

        if _should_stop(context):
            return False

        # 左键点击拆成 down/hold/up，和普通 Click 相比更容易控制按住时长。
        if not ic.left_down(delay=0):
            print("[RandomClicker] left_down failed")
            return False

        if not _sleep_ms(context, hold_min, hold_max):
            ic.left_up(delay=0)
            return False

        if not ic.left_up(delay=0):
            print("[RandomClicker] left_up failed")
            return False

        return _sleep_ms(context, interval_min, interval_max)
