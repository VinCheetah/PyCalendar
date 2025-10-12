"""
Visualization tools for PyCalendar.

This package provides three HTML visualizers:
- HTMLVisualizer: Classic inline HTML view (single file)
- HTMLVisualizerPro: Enhanced premium inline HTML view (single file)
- HTMLVisualizerV2: Modern modular architecture (templates + components)
"""

from .statistics import Statistics
from .html_visualizer import HTMLVisualizer
from .html_visualizer_pro import HTMLVisualizerPro
from .html_visualizer_v2 import HTMLVisualizerV2

__all__ = ['Statistics', 'HTMLVisualizer', 'HTMLVisualizerPro', 'HTMLVisualizerV2']
