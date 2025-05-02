import streamlit as st
from streamlit.components.v1 import declare_component
import json

def draggable(key, default_position=None, on_drag_end=None):
    if default_position is None:
        default_position = {"x": 0, "y": 0}
    
    # Serialize the callback
    callback_str = f"function(x,y){{parent.postMessage({{type:'streamlit:setComponentValue', key:'{key}', value:JSON.stringify({{x:x,y:y}})}}, '*');}}"
    
    # Create the component
    draggable_component = declare_component(
        "draggable",
        path="./draggable_component"
    )
    
    # Call the component
    result = draggable_component(
        key=key,
        defaultPosition=default_position,
        onDragEnd=callback_str
    )
    
    # Handle the result if there is one
    if result and on_drag_end:
        try:
            pos = json.loads(result)
            on_drag_end(pos["x"], pos["y"])
        except:
            pass
    
    return st.empty()  # Return an empty container
