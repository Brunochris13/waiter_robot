from enum import Enum, auto

from ..actions import Action
from .abstract_state import State

class EndOrder(State):
    class _SubState(Enum):
        GOTO_TABLE = auto()
        ASK_IF_FINISHED = auto()
    

    def __init__(self):
        self.substate = self._SubState.GOTO_TABLE
    

    def update(self, robot):
        if self.substate is self._SubState.GOTO_TABLE:
            self.substate = self.goto_table(robot, robot.active_order.table)
        elif self.substate is self._SubState.ASK_IF_FINISHED:
            self.substate = self.ask_if_finished(robot)


    def ask_if_finished(self, robot):
        # Ask if the customers are ready to pay bill
        question = "Are you ready to pay the bill?"
        action, voice_data = robot.communication.ask(question, binary=True)

        order_id = robot.active_order.id

        if self._cancel_if_repeat(action, robot):
            # Cancel order if people play around
            return self._SubState.GOTO_TABLE
        
        if voice_data:
            price = sum([content[1] for content in robot.active_order.contents])
            robot.communication.say(f"The total price is {price} pounds.")
            robot.communication.say("Payment received. Have a nice day.")
            robot.end_order()
        else:
            robot.communication.say("Okay. I will come back later")
            robot.restaurant.request_waiting(order_id, False)
        
        robot.change_state(Action.FLOW.WANDER)
        robot.restaurant.order_ids_ready.remove((order_id, False))

        return self.prev(self.substate)

