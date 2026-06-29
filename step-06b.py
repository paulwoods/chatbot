import asyncio
import json
import logging
import time

import anthropic
from anthropic.types import MessageParam, ToolParam, ToolResultBlockParam
from anthropic.types.tool_param import InputSchemaTyped

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic()

# Guard against an unbounded tool-use loop
MAX_TURNS = 10


# Simulated Tool Implementations
def get_weather(city, units="fahrenheit"):
    """In Production, this calls a real weather API."""
    logger.info("getting the weather for %s", city)

    # sleep to prove this is being called asynchronously
    time.sleep(1)

    weather_data = {
        "San Francisco": {"temp_f": 62, "temp_c": 17, "conditions": "Foggy", "humidity": 78},
        "New York": {"temp_f": 45, "temp_c": 7, "conditions": "Cloudy", "humidity": 55},
        "Tokyo": {"temp_f": 72, "temp_c": 22, "conditions": "Sunny", "humidity": 40},
    }

    data = weather_data.get(city, {"temp_f": 70, "temp_c": 21, "conditions": "Unknown", "humidity": 50})

    temp = data["temp_c"] if units == "celsius" else data["temp_f"]

    logger.info("done getting the weather for %s", city)

    return {
        "city": city,
        "temperature": temp,
        "units": units,
        "conditions": data["conditions"],
        "humidity": data["humidity"],
    }


def convert_temperature(value, from_unit, to_unit):
    """Convert between celsius and fahrenheit."""
    logger.info("converting the temperature from %s to %s", from_unit, to_unit)

    # sleep to prove this is being called asynchronously
    time.sleep(1)

    if from_unit == to_unit:
        return {"value": value, "unit": to_unit}
    if from_unit == "celsius":
        result = (value * 9 / 5) + 32
    else:
        result = (value - 32) * 5 / 9

    return {"value": round(result, 1), "unit": to_unit}


# Tool definitions
tools = [
    ToolParam(name="get_weather",
              description="Get current weather for a city. Return temperature, conditions, and humidity.",
              input_schema=InputSchemaTyped(
                  type="object",
                  properties={
                      "city": {
                          "type": "string",
                          "description": "City name, e.g. 'San Francisco'"
                      },
                      "units": {
                          "type": "string",
                          "enum": ["celsius", "fahrenheit"],
                          "description": "Temperature units, e.g. 'celsius' or 'fahrenheit'"
                      }
                  },
                  required=["city"]
              )
              ),
    ToolParam(name="convert_temperature",
              description="Convert a temperature value between celsius and fahrenheit.",
              input_schema=InputSchemaTyped(
                  type="object",
                  properties={
                      "value": {
                          "type": "number",
                          "description": "The temperature value"
                      },
                      "from_unit": {
                          "type": "string",
                          "enum": ["celsius", "fahrenheit"],
                      },
                      "to_unit": {
                          "type": "string",
                          "enum": ["celsius", "fahrenheit"],
                      }
                  },
                  required=["value", "from_unit", "to_unit"]
              )
              )
]

# Tool dispatcher
TOOL_FUNCS = {
    "get_weather": get_weather,
    "convert_temperature": convert_temperature,
}


def execute_tool(name, arguments):
    func = TOOL_FUNCS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**arguments)
    except Exception as e:
        return {"error": f"{name} failed: {e}"}


async def execute_tool_parallel(tool_calls):
    """Execute multiple tool calls concurrently."""

    # find the tool use blocks, and execute them concurrently
    tool_uses = [b for b in tool_calls if b.type == "tool_use"]
    results = await asyncio.gather(
        *(asyncio.to_thread(execute_tool, b.name, b.input) for b in tool_uses)
    )

    # format the results, flagging errors back to the model
    return [
        ToolResultBlockParam(
            tool_use_id=block.id,
            type="tool_result",
            content=json.dumps(result),
            is_error="error" in result,
        )
        for block, result in zip(tool_uses, results)
    ]


# The universal tool use loop
async def chat_with_tools(user_message):
    messages = [MessageParam(role="user", content=user_message)]

    input_tokens = 0
    output_tokens = 0

    for _ in range(MAX_TURNS):

        try:
            response = await client.messages.create(
                # model="claude-fable-5",
                # model="claude-opus-4-8",
                # model="claude-sonnet-4-6",
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                tools=tools,
                messages=messages
            )

        except anthropic.APIStatusError as e:
            logger.error("API error %s: %s", e.status_code, e.message)
            return "An error occurred while processing your request."
        except anthropic.APIConnectionError as e:
            logger.error("Connection error: %s", e, exc_info=e)
            return "An error occurred while processing your request."

        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens

        # If Claude made no tool calls, it's done — return all text blocks
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            logger.info("Token usage: input=%d, output=%d", input_tokens, output_tokens)
            return "".join(b.text for b in response.content if b.type == "text")

        # Process tool calls
        tool_results = await execute_tool_parallel(response.content)

        # Append assistant response and tool results to conversation
        messages.append(MessageParam(role="assistant", content=response.content))
        messages.append(MessageParam(role="user", content=tool_results))

    logger.warning("Hit max turns (%d) without completion", MAX_TURNS)
    return "Could not complete the request within the turn limit."


print(asyncio.run(chat_with_tools("What is the weather like in Tokyo and San Francisco?")))
