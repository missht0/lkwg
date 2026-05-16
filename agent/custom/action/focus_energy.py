"""自动聚能任务流程。

1. Pipeline 默认先识别战斗界面的聚能图标。
2. 点击方式命中后调用 FocusEnergyAct，刷新截图尺寸并点击固定聚能坐标。
3. 如果用户选择“按键 x”，pipeline 会改用通用 InterceptionInput 发送 x 键。
4. 执行后等待一小段时间，再回到入口持续检测。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from ..interception_controller import get_controller
from .general import _update_image_size


@AgentServer.custom_action("FocusEnergyAct")
class FocusEnergyAct(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 点击方式使用截图坐标，先同步图片尺寸以适配窗口缩放。
        x, y = 62, 633
        ctrl = context.tasker.controller
        _update_image_size(ctrl)
        get_controller().click(x, y)
        return True
