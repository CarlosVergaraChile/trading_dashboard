import plotly.graph_objects as go
def plot_price_evolution(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines+markers', name='Precios'))
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
    return fig
