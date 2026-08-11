"""
core/hand_tracking.py  —  thin re-export so qt_app imports work cleanly.
Delegates to the existing air_canvas_pro implementation.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from air_canvas_pro.core.hand_tracking import HandTracker, OneEuroFilter

__all__ = ["HandTracker", "OneEuroFilter"]
