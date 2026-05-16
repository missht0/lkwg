"""稀兽花种任务流程。

1. RareBeast_Reset 清空技能游标和回合计数。
2. RareBeastWaitAct 循环截图，等待技能 1 可用并继续战斗。
3. 如果检测到捕捉 W，则选择目标、按空格确认捕捉，等待奖励提示后按 ESC 关闭并结束任务。
4. RareBeastAct 按用户配置的技能顺序执行一次技能/聚能/背包操作，再回到等待节点。
"""

import time

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size
from .auto_battle import _expand_skill_order, CHAR_TO_VK, BACKPACK_ITEMS, _BACKPACK_ITEM_LABELS, MAIN_ACTIONS

_SKILL1_ROI = [152, 259, 10, 13]
_W_ROI = [1230, 673, 14, 11]

_REWARD_ROI = [148, 298, 82, 28]

_VK_SPACE = 0x20
_VK_ESC = 0x1B

_WAIT_TIMEOUT = 30

_MAIN_ACTION_LABELS = {
    "1": "技能1", "2": "技能2", "3": "技能3", "4": "技能4",
    "x": "聚能", "X": "聚能",
}


@AgentServer.custom_action("RareBeastReset")
class RareBeastReset(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 新任务开始时重置战斗技能游标。
        RareBeastAct._skill_index = 0
        RareBeastAct._round_count = 0
        print("[RareBeast] 状态重置")
        return True


@AgentServer.custom_action("RareBeastWaitAct")
class RareBeastWaitAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 等待阶段优先检测捕捉 W；没有 W 时再看技能 1 是否可用。
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        start_time = time.time()
        while time.time() - start_time < _WAIT_TIMEOUT:
            ctrl.post_screencap().wait()
            image = ctrl.cached_image
            if image is None:
                time.sleep(0.3)
                continue

            w_result = context.run_recognition(
                # W 出现代表进入捕捉阶段，后续不再继续普通战斗循环。
                "RareBeastWDetect",
                image,
                pipeline_override={
                    "RareBeastWDetect": {
                        "recognition": "OCR",
                        "roi": _W_ROI,
                        "expected": ["w", "W"],
                    }
                },
            )
            if w_result is not None and w_result.hit:
                print("[RareBeast] 检测到 W，进入捕捉")
                time.sleep(0.5)
                print("[RareBeast] >>> 选择目标 (按1)")
                ic.click_key(CHAR_TO_VK["1"])
                time.sleep(0.3)
                print("[RareBeast] >>> 确认选择 (空格)")
                ic.click_key(_VK_SPACE)
                time.sleep(0.5)

                print("[RareBeast] 等待获得奖励...")
                for reward_attempt in range(30):
                    # 捕捉后等待奖励提示，避免 ESC 太早导致奖励界面未完成。
                    ctrl.post_screencap().wait()
                    reward_image = ctrl.cached_image
                    if reward_image is None:
                        time.sleep(0.3)
                        continue
                    reward_result = context.run_recognition(
                        "RareBeastRewardDetect",
                        reward_image,
                        pipeline_override={
                            "RareBeastRewardDetect": {
                                "recognition": "OCR",
                                "roi": _REWARD_ROI,
                                "expected": ["获得奖励"],
                            }
                        },
                    )
                    if reward_result is not None and reward_result.hit:
                        print("[RareBeast] 检测到获得奖励")
                        break
                    time.sleep(0.3)

                print("[RareBeast] >>> 按 ESC 关闭捕捉界面")
                ic.click_key(_VK_ESC)
                time.sleep(0.5)
                return False

            skill1_result = context.run_recognition(
                # 技能 1 可见时交给 RareBeastAct 执行一轮技能。
                "RareBeastSkill1Detect",
                image,
                pipeline_override={
                    "RareBeastSkill1Detect": {
                        "recognition": "OCR",
                        "roi": _SKILL1_ROI,
                        "expected": ["1"],
                    }
                },
            )
            if skill1_result is not None and skill1_result.hit:
                return True

            time.sleep(0.3)

        print("[RareBeast] 等待超时，结束任务")
        return False


@AgentServer.custom_action("RareBeastAct")
class RareBeastAct(CustomAction):

    _skill_index = 0
    _round_count = 0

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 每次只消费技能队列中的一个主动作，下一轮继续从保存的游标执行。
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ic = get_controller()

        node_obj = context.get_node_object("RareBeast_WaitReady")
        attach = getattr(node_obj, "attach", {}) if node_obj else {}
        skill_order = attach.get("skill_order", "||1x")
        skill_order = _expand_skill_order(skill_order.strip())

        if not skill_order:
            return False

        idx = RareBeastAct._skill_index
        if idx >= len(skill_order):
            RareBeastAct._skill_index = 0
            idx = 0
        RareBeastAct._round_count += 1

        print(f"[RareBeast] 回合{RareBeastAct._round_count}, 技能序列: {skill_order}, 当前位置: {idx}")

        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in ("q", "Q"):
                # 背包段处理多个道具键，完成后回到等待技能 1 的节点。
                idx = self._exec_backpack(context, ic, skill_order, idx)
                continue
            if ch in MAIN_ACTIONS:
                label = _MAIN_ACTION_LABELS.get(ch, ch)
                print(f"[RareBeast] >>> {label} ({ch})")
                vk = CHAR_TO_VK.get(ch)
                if vk is not None:
                    ic.click_key(vk)
                    time.sleep(0.3)
                idx += 1
                RareBeastAct._skill_index = idx
                return True
            print(f"[RareBeast] 跳过未知字符: {ch}")
            idx += 1
            RareBeastAct._skill_index = idx

        RareBeastAct._skill_index = 0
        return False

    def _exec_backpack(self, context, ic, skill_order, start_idx):
        # 背包子流程：打开背包、按道具键、等待 r 关闭背包并恢复战斗检测。
        print("[RareBeast] >>> 打开背包 (q)")
        ic.click_key(CHAR_TO_VK["q"])
        time.sleep(0.8)

        idx = start_idx + 1
        while idx < len(skill_order):
            ch = skill_order[idx]
            if ch in BACKPACK_ITEMS:
                label = _BACKPACK_ITEM_LABELS.get(ch, ch)
                print(f"[RareBeast] >>> 使用{label} ({ch})")
                vk = BACKPACK_ITEMS[ch]
                ic.click_key(vk)
                time.sleep(0.8)
                idx += 1
            elif ch in ("r", "R"):
                idx += 1
                RareBeastAct._skill_index = idx
                print("[RareBeast] >>> 等待R出现并关闭背包 (r)")
                context.run_task("RareBeast_WaitBackpackR")
                context.run_task("RareBeast_WaitReady")
                return idx
            elif ch in ("q", "Q"):
                RareBeastAct._skill_index = idx
                print("[RareBeast] >>> 关闭背包后重新打开 (未匹配r，自动关闭)")
                context.run_task("RareBeast_WaitBackpackR")
                context.run_task("RareBeast_WaitReady")
                return idx
            else:
                print(f"[RareBeast] 背包内遇到非物品字符: {ch}，自动关闭背包")
                RareBeastAct._skill_index = idx
                context.run_task("RareBeast_WaitBackpackR")
                context.run_task("RareBeast_WaitReady")
                return idx

        RareBeastAct._skill_index = idx
        print("[RareBeast] >>> 等待R出现并关闭背包 (r)")
        context.run_task("RareBeast_WaitBackpackR")
        context.run_task("RareBeast_WaitReady")
        return idx
