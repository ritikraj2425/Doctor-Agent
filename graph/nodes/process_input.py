from graph.state import DoctorAgentState
from services.input import ProcessInput


class ProcessInputNode:

    def __init__(self, process_input: ProcessInput):
        self.process_input = process_input

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        result = await self.process_input.process(
            file=state.get("file"),
            prompt=state["prompt"],
            chat_id=state["chat_id"],
            prompt_type=state["prompt_type"],
            audio_file=state.get("audio_file"),
        )

        return result