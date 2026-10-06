import asyncio
import json
import os
from contextlib import AsyncExitStack
from pathlib import Path

from dotenv import load_dotenv
from groq import AsyncGroq
from mcp import Client

from catalog import GROUPS, LOAD_GROUP_TOOL

load_dotenv(Path(__file__).parent / ".env")

old_no_proxy = os.getenv("NO_PROXY", "")
os.environ["NO_PROXY"] = f"127.0.0.1,localhost,{old_no_proxy}"


async def main():
    task = input("Задача: ")

    # Initially, the model can only request a tool group
    tools = [LOAD_GROUP_TOOL]
    routes = {}
    loaded_groups = set()

    group_descriptions = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in GROUPS.items()
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ты помощник учебного CAD-приложения. "
                "Для вычислений и оформления используй инструменты. "
                "Сначала загрузи нужную группу через load_tool_group. "
                "Если понадобятся другие возможности, загрузи другую группу. "
                "Для зависимых действий сначала получи предыдущий результат. "
                "Не придумывай отсутствующие параметры. "
                "Отвечай по-русски. Оформление только готовит данные надписи, "
                "а не создаёт чертёж.\n\n"
                f"Каталог групп:\n{group_descriptions}"
            ),
        },
        {"role": "user", "content": task},
    ]

    # Keep dynamically opened connections alive until the task ends
    async with AsyncExitStack() as stack:
        ai = await stack.enter_async_context(
            AsyncGroq(timeout=30.0, max_retries=0)
        )

        for step in range(8):
            print(f"\nШаг {step + 1}: запрос к модели…", flush=True)

            response = await ai.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_completion_tokens=2048,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                print("\nОтвет:", message.content or "Пустой ответ модели.")
                break

            messages.append(message.model_dump(exclude_none=True))

            for call in message.tool_calls:
                name = call.function.name
                print("Инструмент:", name)

                try:
                    args = json.loads(call.function.arguments)
                    if not isinstance(args, dict):
                        raise ValueError("Arguments must be an object.")
                except ValueError as error:
                    data = {"ok": False, "error": str(error)}
                else:
                    print("Аргументы:", args)

                    if name == "load_tool_group":
                        group = args.get("group")

                        if not isinstance(group, str) or group not in GROUPS:
                            data = {"ok": False, "error": "Unknown group."}
                        elif group in loaded_groups:
                            data = {
                                "ok": True,
                                "message": "Group is already loaded.",
                            }
                        else:
                            client = await stack.enter_async_context(
                                Client(GROUPS[group]["url"])
                            )

                            catalog = await client.list_tools()
                            names = []

                            for tool in catalog.tools:
                                full_name = f"{group}__{tool.name}"

                                tools.append({
                                    "type": "function",
                                    "function": {
                                        "name": full_name,
                                        "description": tool.description or "",
                                        "parameters": tool.input_schema,
                                    },
                                })

                                routes[full_name] = (client, tool.name)
                                names.append(full_name)

                            loaded_groups.add(group)
                            data = {
                                "ok": True,
                                "group": group,
                                "loaded_tools": names,
                            }

                    elif name in routes:
                        client, tool_name = routes[name]
                        result = await client.call_tool(tool_name, args)

                        if result.is_error:
                            data = {
                                "ok": False,
                                "error": str(result.content),
                            }
                        elif result.structured_content is None:
                            data = {
                                "ok": False,
                                "error": "Structured result is missing.",
                            }
                        else:
                            data = result.structured_content
                    else:
                        data = {
                            "ok": False,
                            "error": "Tool is unavailable. Load its group first.",
                        }

                print("Результат:", data)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(data, ensure_ascii=False),
                })
        else:
            print("\nДостигнут лимит шагов. Задача могла остаться незавершённой.")


asyncio.run(main())