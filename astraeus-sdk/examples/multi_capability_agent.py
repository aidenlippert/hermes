"""
Multi-Capability Data Agent Example

This example shows how to create an agent with multiple capabilities,
allowing it to offer different services at different price points.
"""

from astraeus import Agent
import json


agent = Agent(
    name="DataProcessorBot",
    description="Data processing agent with analysis, cleaning, and visualization capabilities",
    api_key="astraeus_demo_key_12345",
    owner="demo@example.com"
)


@agent.capability(
    "clean_data",
    cost=0.05,
    description="Clean and normalize data"
)
async def clean_data(data: list) -> dict:
    """
    Clean and normalize data

    Args:
        data: List of data items to clean

    Returns:
        Cleaned data with statistics
    """
    cleaned = []
    removed_count = 0

    for item in data:
        if item and isinstance(item, (str, int, float, dict)):
            cleaned.append(item)
        else:
            removed_count += 1

    return {
        "success": True,
        "cleaned_data": cleaned,
        "original_count": len(data),
        "cleaned_count": len(cleaned),
        "removed_count": removed_count
    }


@agent.capability(
    "analyze_data",
    cost=0.10,
    description="Perform statistical analysis on data"
)
async def analyze_data(data: list) -> dict:
    """
    Analyze numerical data

    Args:
        data: List of numbers to analyze

    Returns:
        Statistical analysis results
    """
    numeric_data = [x for x in data if isinstance(x, (int, float))]

    if not numeric_data:
        return {"error": "No numeric data provided"}

    return {
        "success": True,
        "count": len(numeric_data),
        "min": min(numeric_data),
        "max": max(numeric_data),
        "mean": sum(numeric_data) / len(numeric_data),
        "sum": sum(numeric_data)
    }


@agent.capability(
    "visualize_data",
    cost=0.08,
    description="Generate data visualization metadata"
)
async def visualize_data(data: list, chart_type: str = "bar") -> dict:
    """
    Generate visualization metadata for data

    Args:
        data: Data to visualize
        chart_type: Type of chart (bar, line, pie)

    Returns:
        Visualization configuration
    """
    if chart_type not in ["bar", "line", "pie"]:
        return {"error": f"Invalid chart type: {chart_type}"}

    return {
        "success": True,
        "chart_type": chart_type,
        "data_points": len(data),
        "visualization": {
            "type": chart_type,
            "data": data[:10],
            "config": {
                "responsive": True,
                "animation": True
            }
        }
    }


@agent.capability(
    "transform_data",
    cost=0.03,
    description="Transform data format (JSON, CSV, etc.)"
)
async def transform_data(data: list, output_format: str = "json") -> dict:
    """
    Transform data between formats

    Args:
        data: Data to transform
        output_format: Target format (json, csv)

    Returns:
        Transformed data
    """
    if output_format == "json":
        return {
            "success": True,
            "format": "json",
            "data": json.dumps(data, indent=2)
        }
    elif output_format == "csv":
        csv_data = "\n".join([str(item) for item in data])
        return {
            "success": True,
            "format": "csv",
            "data": csv_data
        }
    else:
        return {"error": f"Unsupported format: {output_format}"}


if __name__ == "__main__":
    print("\n📊 Multi-Capability Data Agent")
    print("=" * 50)
    print("Available capabilities:")
    print("  1. clean_data ($0.05) - Clean and normalize data")
    print("  2. analyze_data ($0.10) - Statistical analysis")
    print("  3. visualize_data ($0.08) - Generate visualizations")
    print("  4. transform_data ($0.03) - Format transformation")
    print("=" * 50)
    print()

    agent.serve(host="0.0.0.0", port=8001, register=True)
