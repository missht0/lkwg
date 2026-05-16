"""通用 Interception 输入动作流程。

主要服务于战斗脱离、自动聚能以及其他 pipeline 中的简单输入节点。

1. 从 custom_action_param 读取动作类型、按键、坐标或按住时长。
2. 根据 type 分发到真实键盘/鼠标输入：单击按键、长按、按下、松开、点击坐标、点击识别目标中心。
3. 坐标点击前刷新截图尺寸，保证资源坐标能映射到当前游戏窗口。
4. 参数不完整或动作类型未知时返回 False，让 pipeline 按失败逻辑处理。
"""

import json

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size


@AgentServer.custom_action("InterceptionInput")
class InterceptionInputAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # MaaFramework 可能传字符串 JSON，也可能直接传 dict，这里兼容两种格式。
        try:
            param = json.loads(argv.custom_action_param or "{}")
        except Exception:
            param = {}

        if isinstance(argv.custom_action_param, dict):
            param = argv.custom_action_param
        elif isinstance(argv.custom_action_param, str):
            try:
                param = json.loads(argv.custom_action_param)
            except Exception:
                param = {}

        action_type = param.get("type", "")
        key = param.get("key")
        target = param.get("target")
        duration = param.get("duration", 500)
        ctrl = get_controller()

        # 按动作类型分发到 Interception 控制器。这里不做业务判断，只负责“真实输入”。
        if action_type == "click_key":
            if key is not None:
                ctrl.click_key(key)
                return True

        elif action_type == "long_press_key":
            if key is not None:
                ctrl.long_press_key(key, duration_ms=duration)
                return True

        elif action_type == "key_down":
            if key is not None:
                ctrl.key_down(key)
                return True

        elif action_type == "key_up":
            if key is not None:
                ctrl.key_up(key)
                return True

        elif action_type == "click":
            if target is not None and isinstance(target, list) and len(target) >= 2:
                # 资源坐标点击前刷新截图尺寸，避免窗口尺寸变化导致落点不准。
                _update_image_size(context.tasker.controller)
                ctrl.click(target[0], target[1])
                return True

        elif action_type == "click_target":
            reco_detail = argv.reco_detail
            if reco_detail is not None and reco_detail.hit:
                # click_target 用上一节点的识别框中心作为点击位置，战斗脱离默认走这个分支。
                box = reco_detail.box
                if box:
                    x = box[0] + box[2] // 2
                    y = box[1] + box[3] // 2
                    _update_image_size(context.tasker.controller)
                    ctrl.click(x, y)
                    return True

        return False
