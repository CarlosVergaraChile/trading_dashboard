# Streamlit Trading Desk Skin

A presentation-only skin for Streamlit dashboards. It turns the standard Streamlit canvas into a dark trading-terminal style without adding widgets or changing application state.

## Use it in any Streamlit app

Copy `src/streamlit_skin.py` into your project and call this after `st.set_page_config()`:

```python
import streamlit as st
from streamlit_skin import apply_skin

st.set_page_config(page_title="My dashboard", layout="wide")
apply_skin()
```

The skin only injects CSS. Your existing widgets, callbacks, charts, session state, and data logic remain yours.

## Design goals

- Premium terminal-style header and canvas
- Persistent control-rail sidebar
- High-contrast metric cards
- Analytical panels for charts and tables
- Responsive behavior for smaller screens
- No JavaScript, no external assets, and no runtime service

The dashboard in this repository installs the skin automatically through `src.__init__`, while `apply_skin()` is provided for explicit use in community projects.

## License

MIT. See `LICENSE` if this component is distributed independently.
