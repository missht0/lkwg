"""自动聚能后台轮询流程。

1. 后台持续检测模式下，Pipeline 每轮直接调用 FocusEnergyPollAct。
2. FocusEnergyPollAct 主动截图并检测聚能图标，不再依赖 TemplateMatch 节点决定任务寿命。
3. 检测到聚能图标后，根据 custom_action_param 点击识别框中心或发送 x 键。
4. 未检测到聚能图标时返回 True，Pipeline 会继续下一轮，直到用户主动停止任务。
"""

import json

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size

_ENERGY_TEMPLATE = "Battle/Energy.png"
_ENERGY_ROI = [11, 583, 102, 101]
_VK_X = 0x58


@AgentServer.custom_action("FocusEnergyPollAct")
class FocusEnergyPollAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 常驻轮询：没看到聚能图标也返回成功，让任务继续挂在后台。
        param = argv.custom_action_param
        if isinstance(param, str):
            try:
                param = json.loads(param)
            except Exception:
                param = {}
        if not isinstance(param, dict):
            param = {}

        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        ctrl.post_screencap().wait()
        image = ctrl.cached_image
        if image is None:
            return True

        result = context.run_recognition(
            "FocusEnergyDetect",
            image,
            pipeline_override={
                "FocusEnergyDetect": {
                    "recognition": "TemplateMatch",
                    "template": _ENERGY_TEMPLATE,
                    "roi": _ENERGY_ROI,
                    "threshold": 0.7,
                }
            },
        )
        if result is None or not result.hit:
            return True

        ic = get_controller()
        if param.get("type") == "click_key":
            # 按键模式：和普通 InterceptionInput 的 click_key 参数保持兼容。
            ic.click_key(param.get("key", _VK_X))
            return True

        # 点击模式：使用识别框中心，兼容窗口缩放。
        box = getattr(result, "box", None)
        if box:
            x = box[0] + box[2] // 2
            y = box[1] + box[3] // 2
            ic.click(x, y)
        return True
