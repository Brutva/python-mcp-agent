from pydantic import BaseModel

from mcp.server import MCPServer

mcp = MCPServer("Formatting")


class TitleResult(BaseModel):
    ok: bool
    title: str | None = None
    author: str | None = None
    error: str | None = None


@mcp.tool(structured_output=True)
def prepare_title(title: str, author: str) -> TitleResult:
    """Prepare drawing title data. Title and author must not be empty."""
    title = title.strip()
    author = author.strip()

    if not title or not author:
        return TitleResult(
            ok=False,
            error="Title and author must not be empty.",
        )

    return TitleResult(
        ok=True,
        title=title,
        author=author,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)