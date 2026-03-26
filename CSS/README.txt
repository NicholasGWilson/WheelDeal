The CSS module (style.py) is a custom styling system for Streamlit applications. It reads TOML configuration files
and converts them into CSS stylesheets that are injected into the Streamlit app. This allows for extensive customization 
of Streamlit UI elements beyond the default styling options. See _EXAMPLE.toml for all the options.

Streamlit Features It Touches
Buttons: Custom colors, hover effects, click states, transitions
Tables: Background colors, text colors, borders, column-specific styling
Expanders: Header styling, content area colors
Input Fields: Text inputs, number inputs, text areas
Dropdowns/Selectboxes: Option styling, hover states
General Elements: Fonts, colors, borders, transitions

How to Tag a Specific Element
To apply custom styles to a specific Streamlit element, use the LabelElement method:
style_config.LabelElement('my_custom_button', container=st)
st.button('My Button')  # This button will now have custom styling