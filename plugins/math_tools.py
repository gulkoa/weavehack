#!/usr/bin/env python3
"""
Math Plugin for Modular MCP Server

This plugin provides mathematical calculation functionality.
Demonstrates how easy it is to add new capabilities to the MCP server.
"""

import math
from typing import List, Union


def calculate_basic(operation: str, a: float, b: float) -> float:
    """
    Perform basic mathematical operations.
    
    Args:
        operation (str): Operation to perform (+, -, *, /, %, ^)
        a (float): First number
        b (float): Second number
        
    Returns:
        float: Result of the calculation
        
    Example:
        >>> calculate_basic("+", 5, 3)
        8.0
    """
    operations = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y if y != 0 else float('inf'),
        "%": lambda x, y: x % y if y != 0 else float('inf'),
        "^": lambda x, y: x ** y,
        "**": lambda x, y: x ** y
    }
    
    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")
    
    return operations[operation](a, b)


def calculate_statistics(numbers: List[float]) -> dict:
    """
    Calculate statistical measures for a list of numbers.
    
    Args:
        numbers (list): List of numbers to analyze
        
    Returns:
        dict: Statistical measures including mean, median, mode, std dev, etc.
        
    Example:
        >>> calculate_statistics([1, 2, 3, 4, 5])
        {'mean': 3.0, 'median': 3.0, ...}
    """
    if not numbers:
        raise ValueError("Cannot calculate statistics for empty list")
    
    sorted_nums = sorted(numbers)
    n = len(numbers)
    
    # Mean
    mean = sum(numbers) / n
    
    # Median
    if n % 2 == 0:
        median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    else:
        median = sorted_nums[n//2]
    
    # Standard deviation
    variance = sum((x - mean) ** 2 for x in numbers) / n
    std_dev = math.sqrt(variance)
    
    return {
        "count": n,
        "sum": sum(numbers),
        "mean": mean,
        "median": median,
        "min": min(numbers),
        "max": max(numbers),
        "range": max(numbers) - min(numbers),
        "variance": variance,
        "std_dev": std_dev
    }


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between different units of measurement.
    
    Supports temperature, length, weight, and volume conversions.
    
    Args:
        value (float): Value to convert
        from_unit (str): Source unit (e.g., 'celsius', 'meter', 'kg')
        to_unit (str): Target unit (e.g., 'fahrenheit', 'feet', 'lb')
        
    Returns:
        float: Converted value
        
    Example:
        >>> convert_units(0, 'celsius', 'fahrenheit')
        32.0
    """
    # Temperature conversions
    temp_conversions = {
        ('celsius', 'fahrenheit'): lambda c: (c * 9/5) + 32,
        ('fahrenheit', 'celsius'): lambda f: (f - 32) * 5/9,
        ('celsius', 'kelvin'): lambda c: c + 273.15,
        ('kelvin', 'celsius'): lambda k: k - 273.15,
        ('fahrenheit', 'kelvin'): lambda f: (f - 32) * 5/9 + 273.15,
        ('kelvin', 'fahrenheit'): lambda k: (k - 273.15) * 9/5 + 32
    }
    
    # Length conversions (to meters)
    length_to_meters = {
        'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
        'inch': 0.0254, 'ft': 0.3048, 'yard': 0.9144, 'mile': 1609.34
    }
    
    # Weight conversions (to grams)
    weight_to_grams = {
        'mg': 0.001, 'g': 1, 'kg': 1000,
        'oz': 28.3495, 'lb': 453.592
    }
    
    conversion_key = (from_unit.lower(), to_unit.lower())
    
    # Handle temperature
    if conversion_key in temp_conversions:
        return temp_conversions[conversion_key](value)
    
    # Handle length
    if from_unit.lower() in length_to_meters and to_unit.lower() in length_to_meters:
        meters = value * length_to_meters[from_unit.lower()]
        return meters / length_to_meters[to_unit.lower()]
    
    # Handle weight
    if from_unit.lower() in weight_to_grams and to_unit.lower() in weight_to_grams:
        grams = value * weight_to_grams[from_unit.lower()]
        return grams / weight_to_grams[to_unit.lower()]
    
    raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")


def solve_quadratic(a: float, b: float, c: float) -> dict:
    """
    Solve quadratic equation ax² + bx + c = 0.
    
    Args:
        a (float): Coefficient of x²
        b (float): Coefficient of x
        c (float): Constant term
        
    Returns:
        dict: Solutions and discriminant information
        
    Example:
        >>> solve_quadratic(1, -5, 6)
        {'discriminant': 1.0, 'solutions': [3.0, 2.0]}
    """
    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero for quadratic equation")
    
    discriminant = b**2 - 4*a*c
    
    if discriminant > 0:
        x1 = (-b + math.sqrt(discriminant)) / (2*a)
        x2 = (-b - math.sqrt(discriminant)) / (2*a)
        return {
            "discriminant": discriminant,
            "solutions": [x1, x2],
            "type": "two_real_solutions"
        }
    elif discriminant == 0:
        x = -b / (2*a)
        return {
            "discriminant": discriminant,
            "solutions": [x],
            "type": "one_real_solution"
        }
    else:
        real_part = -b / (2*a)
        imaginary_part = math.sqrt(-discriminant) / (2*a)
        return {
            "discriminant": discriminant,
            "solutions": [
                f"{real_part} + {imaginary_part}i",
                f"{real_part} - {imaginary_part}i"
            ],
            "type": "complex_solutions"
        }
