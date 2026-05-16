"""传说精灵自动战斗任务流程。

1. AutoBattle_Reset 清空技能游标和回合计数。
2. AutoBattle_WaitReady 持续截图，先判断战斗是否结束，再等待技能 1 出现。
3. AutoBattleAct 按用户配置的技能顺序执行一次动作；支持 1-4 技能、x 聚能、q/r 背包开关。
4. Pipeline 回到等待节点，等下一轮技能可用后继续执行。
5. 如启用印记，战斗结束后会尝试打开印记、确认并选择目标。
"""

import re
import time

import numpy as np

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size

_INFINITE_REPEAT = 200

_BACKPACK_ITEM_LABELS = {"1": "进化之力", "2": "能量瓶"}
_CHAR_LABELS = {
    "1": "技能1", "2": "技能2", "3": "技能3", "4": "技能4",
    "x": "聚能", "X": "聚能",
    "q": "打开背包", "Q": "打开背包",
    "r": "关闭背包", "R": "关闭背包",
}

CHAR_TO_VK = {
    "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "x": 0x58, "X": 0x58,
    "q": 0x51, "Q": 0x51,
    "r": 0x52, "R": 0x52,
}

BACKPACK_ITEMS = {"1": 0x31, "2": 0x32}
MAIN_ACTIONS = {"1", "2", "3", "4", "x", "X"}

_MARK_ICON_POS = (690, 372)
_MARK_COLOR_ROI = [675, 331, 38, 7]
_MARK_COLOR_LOWER = np.array([0, 115, 210], dtype=np.uint8)
_MARK_COLOR_UPPER = np.array([0, 127, 218], dtype=np.uint8)

_MARK_CONFIRM_ROI = [719, 582, 44, 21]
_SKILL1_ROI = [152, 259, 10, 13]
_BATTLE_END_ROI = [719, 582, 44, 21]

_WAIT_TIMEOUT = 30


def _expand_skill_order(s):
    # 把 |1x|3、||1x、|1x|a 这类简写展开为可逐字符执行的技能队列。
    s = re.sub(r'\|([^|]+)\|a', lambda m: m.group(1) * _INFINITE_REPEAT, s)
    s = re.sub(r'\|\|([^|]+)', lambda m: m.group(1) * _INFINITE_REPEAT, s)
    s = re.sub(r'\|([^|]+)\|(\d+)', lambda m: m.group(1) * int(m.group(2)), s)
    return s


def _check_mark_color(image):
    # 点击印记后用固定区域颜色做二次确认，避免误点后继续走确认流程。
    bgr = np.asarray(image, dtype=np.uint8)
    x, y, w, h = _MARK_COLOR_ROI
    roi = bgr[y:y + h, x:x + w]
    lower = np.all(roi >= _MARK_COLOR_LOWER, axis=2)
    upper = np.all(roi <= _MARK_COLOR_UPPER, axis=2)
    return np.any(lower & upper)


@AgentServer.custom_action("AutoBattleReset")
class AutoBattleReset(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 新任务开始时重置静态游标，避免沿用上一次任务停下的位置。
        AutoBattleAct._skill_index = 0
        AutoBattleAct._round_count = 0
        print("[AutoBattle] 状态重置")
        return True


@AgentServer.custom_action("AutoBattleWaitAct")
class AutoBattleWaitAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 等待阶段有两个出口：发现确认按钮表示战斗结束；发现技能 1 表示可出手。
        ctrl = context.tasker.controller
        _update_image_size(ctrl)

        start_time = time.time()
        while time.time() - start_time < _WAIT_TIMEOUT:
            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                time.sleep(0.3)
                continue

            end_result = context.run_recognition(
                "AutoBattleEndDetect",
                image,
                pipeline_override={
                    "AutoBattleEndDetect": {
                        "recognition": "OCR",
                        "roi": _BATTLE_END_ROI,
                        "expected": ["确认"],
                    }
                },
            )
            if end_result is not None and end_result.hit:
                print("[AutoBattle] 检测到确认，战斗结束")
                return False

            skill1_result = context.run_recognition(
                "AutoBattleSkill1Detect",
                image,
                pipeline_override={
                    "AutoBattleSkill1Detect": {
                        "recognition": "OCR",
                        "roi": _SKILL1_ROI,
                        "expected": ["1"],
                    }
                },
            )
            if skill1_result is not None and skill1_result.hit:
                return True

            time.sleep(0.3)

        print("[AutoBattle] 等待超时，结束任务")
        return False


@AgentServer.custom_action("AutoBattleUseMarkAct")
class AutoBattleUseMarkAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 印记是可选后处理：没启用时直接跳过，不影响普通战斗。
        node_obj = context.get_node_object("AutoBattle_UseMark")
        print(node_obj.attach)
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        use_mark = str(attach.get("use_mark", "false")).lower() == "true"
        if not use_mark:
            print("[AutoBattle] 未启用印记，跳过")
            return True

        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        for attempt in range(2):
            # 点击印记后再截图校验颜色，最多试两次。
            print(f"[AutoBattle] >>> 点击印记图标 (尝试 {attempt + 1}/2)")
            ic.click(*_MARK_ICON_POS)
            time.sleep(0.5)

            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                print("[AutoBattle] 截图失败，跳过印记")
                return True

            if _check_mark_color(image):
                print("[AutoBattle] 印记颜色检测通过")
                break
            print(f"[AutoBattle] 印记颜色检测未通过 (尝试 {attempt + 1}/2)")
        else:
            print("[AutoBattle] 印记颜色检测未通过，跳过印记流程")
            return True

        confirm_result = context.run_recognition(
            # 只有确认按钮被识别到时才继续选择目标，减少误触。
            "MarkConfirmDetect",
            image,
            pipeline_override={"MarkConfirmDetect": {
                "recognition": "OCR",
                "roi": _MARK_CONFIRM_ROI,
                "expected": ["确认"],
            }},
        )
        if confirm_result is None or not confirm_result.hit:
            print("[AutoBattle] 未检测到确认按钮，跳过印记流程")
            return True

        box = confirm_result.box
        if box:
            cx = box[0] + box[2] // 2
            cy = box[1] + box[3] // 2
            print(f"[AutoBattle] >>> 点击确认 ({cx}, {cy})")
            ic.click(cx, cy)
        time.sleep(0.5)

        print("[AutoBattle] >>> 选择目标 (按1)")
        ic.click_key(CHAR_TO_VK["1"])
        time.sleep(0.3)

        print("[AutoBattle] >>> 确认选择 (空格)")
        ic.click_key(0x20)
        time.sleep(0.5)

        context.run_task("Battle_Esc")
        time.sleep(0.5)

        return True


@AgentServer.custom_action("AutoBattleAct")
class AutoBattleAct(CustomAction):

    _skill_index = 0
    _round_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 每次只执行技能队列中的一个主动作，然后把游标保存到类变量里等待下一轮。
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        node_obj = context.get_node_object("AutoBattle_WaitReady")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        skill_order = attach.get("skill_order", "||1x")
        skill_order = _expand_skill_order(skill_order.strip())

        if not skill_order:
            return False

        idx = AutoBattleAct._skill_index
        if idx >= len(skill_order):
            AutoBattleAct._skill_index = 0
            idx = 0
        AutoBattleAct._round_count += 1

        print(f"[AutoBattle] 回合{AutoBattleAct._round_count}, 技能序列: {skill_order}, 当前位置: {idx}")

        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in ("q", "Q"):
                # 背包段可能包含多个道具键，执行完成后等待 R 关闭背包并回到战斗。
                idx = self._exec_backpack(context, ic, skill_order, idx)
                continue
            if ch in MAIN_ACTIONS:
                label = _CHAR_LABELS.get(ch, ch)
                print(f"[AutoBattle] >>> {label} ({ch})")
                vk = CHAR_TO_VK.get(ch)
                if vk is not None:
                    ic.click_key(vk)
                    time.sleep(0.3)
                idx += 1
                AutoBattleAct._skill_index = idx
                return True
            print(f"[AutoBattle] 跳过未知字符: {ch}")
            idx += 1
            AutoBattleAct._skill_index = idx

        AutoBattleAct._skill_index = 0
        return False

    def _exec_backpack(self, context, ic, skill_order, start_idx):
        # 背包子流程：q 打开背包，连续使用道具键，遇到 r 或非法字符时关闭并回到战斗等待。
        print("[AutoBattle] >>> 打开背包 (q)")
        ic.click_key(CHAR_TO_VK["q"])
        time.sleep(0.8)

        idx = start_idx + 1
        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in BACKPACK_ITEMS:
                label = _BACKPACK_ITEM_LABELS.get(ch, ch)
                print(f"[AutoBattle] >>> 使用{label} ({ch})")
                vk = BACKPACK_ITEMS[ch]
                ic.click_key(vk)
                time.sleep(0.8)
                idx += 1
            elif ch in ("r", "R"):
                idx += 1
                AutoBattleAct._skill_index = idx
                print("[AutoBattle] >>> 等待R出现并关闭背包 (r)")
                context.run_task("AutoBattle_WaitBackpackR")
                context.run_task("AutoBattle_WaitReady")
                return idx
            elif ch in ("q", "Q"):
                AutoBattleAct._skill_index = idx
                print("[AutoBattle] >>> 关闭背包后重新打开 (未匹配r，自动关闭)")
                context.run_task("AutoBattle_WaitBackpackR")
                context.run_task("AutoBattle_WaitReady")
                return idx
            else:
                print(f"[AutoBattle] 背包内遇到非物品字符: {ch}，自动关闭背包")
                AutoBattleAct._skill_index = idx
                context.run_task("AutoBattle_WaitBackpackR")
                context.run_task("AutoBattle_WaitReady")
                return idx

        AutoBattleAct._skill_index = idx
        print("[AutoBattle] >>> 等待R出现并关闭背包 (r)")
        context.run_task("AutoBattle_WaitBackpackR")
        context.run_task("AutoBattle_WaitReady")
        return idx
