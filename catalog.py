GROUPS = {
    "geometry": {
        "description": "Вычисления площади и периметра геометрических фигур.",
        "url": "http://127.0.0.1:8000/mcp",
    },
    "formatting": {
        "description": "Подготовка названия чертежа и данных автора.",
        "url": "http://127.0.0.1:8001/mcp",
    },
}


LOAD_GROUP_TOOL = {
    "type": "function",
    "function": {
        "name": "load_tool_group",
        "description": (
            "Load tools from a group before using them. "
            "Several groups can be loaded during one task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "group": {
                    "type": "string",
                    "enum": list(GROUPS),
                    "description": "The group to load.",
                },
            },
            "required": ["group"],
            "additionalProperties": False,
        },
    },
}