from pydantic import BaseModel

from mcp.server import MCPServer

mcp = MCPServer("Geometry")


class AreaResult(BaseModel):
    ok: bool
    area: float | None = None
    error: str | None = None


class PerimeterResult(BaseModel):
    ok: bool
    perimeter: float | None = None
    error: str | None = None


@mcp.tool(structured_output=True)
def rectangle_area(width: float, height: float) -> AreaResult:
    """Calculate rectangle area. Both sides must be positive."""
    if width <= 0 or height <= 0:
        return AreaResult(
            ok=False,
            error="Width and height must be positive.",
        )

    return AreaResult(ok=True, area=width * height)


@mcp.tool(structured_output=True)
def rectangle_perimeter(width: float, height: float) -> PerimeterResult:
    """Calculate rectangle perimeter. Both sides must be positive."""
    if width <= 0 or height <= 0:
        return PerimeterResult(
            ok=False,
            error="Width and height must be positive.",
        )

    return PerimeterResult(
        ok=True,
        perimeter=2 * (width + height),
    )