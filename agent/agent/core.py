import anthropic
import json
import traceback
from . import database, tools
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Je bent SysAgent, een autonome systeembeheer agent.
Je voert taken zelfstandig en methodisch uit.

Werkwijze:
1. Analyseer de taak zorgvuldig
2. Maak een concreet plan van aanpak
3. Voer stap voor stap uit met de beschikbare tools
4. Controleer of het resultaat correct is
5. Rapporteer duidelijk wat je gedaan hebt en wat het resultaat is

Communiceer altijd in het Nederlands. Wees beknopt maar volledig."""


def run_task(task_id: int):
    task = database.get_task(task_id)
    if not task:
        return

    database.update_task_status(task_id, 'running')
    database.add_log(task_id, 'info', f"Taak gestart: {task['title']}")

    messages = [
        {"role": "user", "content": f"Taak: {task['title']}\n\nBeschrijving:\n{task['description']}"}
    ]

    try:
        max_iterations = 25
        for iteration in range(max_iterations):
            database.add_log(task_id, 'info', f"Iteratie {iteration + 1}/{max_iterations}")

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools.TOOL_DEFINITIONS,
                messages=messages
            )

            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text' and block.text.strip():
                    database.add_log(task_id, 'agent', block.text)

            if response.stop_reason == 'end_turn':
                final_text = next(
                    (b.text for b in response.content if hasattr(b, 'type') and b.type == 'text'),
                    'Taak voltooid'
                )
                database.complete_task(task_id, final_text)
                database.add_log(task_id, 'info', 'Taak succesvol voltooid')
                return

            if response.stop_reason == 'tool_use':
                tool_results = []

                for block in response.content:
                    if not (hasattr(block, 'type') and block.type == 'tool_use'):
                        continue

                    tool_name = block.name
                    tool_input = block.input

                    database.add_log(
                        task_id, 'tool',
                        f"{tool_name}({json.dumps(tool_input, ensure_ascii=False)[:300]})"
                    )

                    result = tools.execute_tool(tool_name, tool_input)
                    result_preview = str(result)[:800]
                    database.add_log(task_id, 'result', result_preview)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                final_text = next(
                    (b.text for b in response.content if hasattr(b, 'type') and b.type == 'text'),
                    f'Gestopt: {response.stop_reason}'
                )
                database.complete_task(task_id, final_text)
                return

        database.fail_task(task_id, f"Maximum aantal iteraties ({max_iterations}) bereikt")
        database.add_log(task_id, 'error', "Taak gestopt: maximum iteraties bereikt")

    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        database.fail_task(task_id, error_msg)
        database.add_log(task_id, 'error', f"Fout: {error_msg}\n{trace}")
