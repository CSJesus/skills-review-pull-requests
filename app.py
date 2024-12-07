from dash import Dash, html, dcc, Input, Output, State, ALL, callback_context
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging
import dash

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def load_and_process_data():
    """Load and process price data with proper date handling"""
    try:
        df = pd.read_csv('Average_Prices_By_Day.csv')
        if df.empty:
            return pd.DataFrame()

        # Convert and sort dates properly
        date_cols = df.columns[1:].tolist()
        dates_dict = {col: pd.to_datetime(col, format='mixed', errors='coerce') for col in date_cols}
        sorted_dates = sorted(dates_dict.items(), key=lambda x: x[1])
        sorted_date_cols = [date[0] for date in sorted_dates]

        # Reorder columns with sorted dates
        df = df[[df.columns[0]] + sorted_date_cols]

        return df
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return pd.DataFrame()


def create_line_chart(df, product_name, compare_with=None):
    """Create enhanced line chart with optional comparison"""
    fig = go.Figure()
    dates = df.columns[1:].tolist()

    # Main product line
    prices = df[df[df.columns[0]] == product_name].iloc[0, 1:].astype(float).fillna(method='ffill')
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        name=product_name,
        line=dict(color='#4C9AFF', width=3),
        mode='lines+markers'
    ))

    # Add comparison lines if requested
    if compare_with:
        colors = ['#10B981', '#F59E0B', '#EF4444']
        for idx, comp_product in enumerate(compare_with):
            if comp_product in df[df.columns[0]].values:
                comp_prices = df[df[df.columns[0]] == comp_product].iloc[0, 1:].astype(float).fillna(method='ffill')
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=comp_prices,
                    name=comp_product,
                    line=dict(color=colors[idx % len(colors)], width=2),
                    mode='lines+markers'
                ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#1E293B',
        plot_bgcolor='#1E293B',
        title=dict(
            text='Price History Comparison' if compare_with else 'Price History',
            font=dict(size=20, color='white')
        ),
        xaxis=dict(
            title='Date',
            gridcolor='rgba(255, 255, 255, 0.1)',
            title_font=dict(size=14, color='white'),
            tickfont=dict(size=12, color='white'),
            tickangle=45
        ),
        yaxis=dict(
            title='Price ($)',
            gridcolor='rgba(255, 255, 255, 0.1)',
            title_font=dict(size=14, color='white'),
            tickfont=dict(size=12, color='white'),
            tickprefix='$'
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=True if compare_with else False,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)'
        )
    )

    return fig


def create_candlestick_chart(df, product_name):
    """Create candlestick-style chart for price ranges"""
    prices = df[df[df.columns[0]] == product_name].iloc[0, 1:].astype(float).fillna(method='ffill')
    dates = df.columns[1:].tolist()

    # Calculate weekly ranges
    weekly_high = prices.rolling(7, min_periods=1).max()
    weekly_low = prices.rolling(7, min_periods=1).min()
    weekly_open = prices.rolling(7, min_periods=1).apply(lambda x: x[0])
    weekly_close = prices.rolling(7, min_periods=1).apply(lambda x: x[-1])

    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=weekly_open,
        high=weekly_high,
        low=weekly_low,
        close=weekly_close,
        increasing_line_color='#10B981',
        decreasing_line_color='#EF4444'
    )])

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#1E293B',
        plot_bgcolor='#1E293B',
        title='Weekly Price Ranges',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        height=300
    )

    return fig


def create_product_page(df, product_name, compare_with=None):
    """Create enhanced product page with multiple visualizations"""
    if product_name not in df[df.columns[0]].values:
        return html.Div("Product not found", className='error-message')

    product_data = df[df[df.columns[0]] == product_name].iloc[0]
    prices = product_data.iloc[1:].astype(float).fillna(method='ffill')

    if len(prices) == 0:
        return html.Div("No price data available", className='error-message')

    current_price = prices.iloc[-1]
    prev_price = prices.iloc[-2] if len(prices) > 1 else prices.iloc[0]
    price_change = ((current_price - prev_price) / prev_price) * 100

    return html.Div([
        # Product Header with Current Price
        html.Div([
            html.Div([
                html.H1(product_name, className='product-title'),
                html.Div([
                    html.H3('Current Price', className='price-label'),
                    html.H2(f"${current_price:.2f}", className='current-price'),
                    html.P([
                        html.Span('↑' if price_change >= 0 else '↓', className='trend-arrow'),
                        f" {abs(price_change):.1f}% vs previous"
                    ], className=f"trend {'positive' if price_change >= 0 else 'negative'}")
                ], className='price-container')
            ], className='product-header-content')
        ], className='product-header'),

        # Statistics Section
        html.Div([
            html.Div([
                html.H3('30-Day Low', className='stat-title'),
                html.Div(f"${prices.tail(30).min():.2f}", className='stat-value'),
                html.Div('Last 30 days', className='stat-period')
            ], className='stat-card'),
            html.Div([
                html.H3('30-Day High', className='stat-title'),
                html.Div(f"${prices.tail(30).max():.2f}", className='stat-value'),
                html.Div('Last 30 days', className='stat-period')
            ], className='stat-card'),
            html.Div([
                html.H3('30-Day Average', className='stat-title'),
                html.Div(f"${prices.tail(30).mean():.2f}", className='stat-value'),
                html.Div('Last 30 days', className='stat-period')
            ], className='stat-card')
        ], className='stats-container'),

        # Comparison Section
        html.Div([
            html.H3("Compare with other products", className='section-title'),
            dcc.Dropdown(
                id={'type': 'comparison-dropdown', 'index': 0},
                options=[
                    {'label': p, 'value': p}
                    for p in df[df.columns[0]].unique()
                    if p != product_name
                ],
                value=compare_with,
                multi=True,
                placeholder="Select products to compare...",
                className='comparison-dropdown'
            )
        ], className='comparison-section'),

        # Charts Container
        html.Div([
            html.Div([
                dcc.Graph(figure=create_line_chart(df, product_name, compare_with)),
                dcc.Graph(figure=create_candlestick_chart(df, product_name))
            ], className='charts-grid')
        ], className='charts-container')
    ])


# Main Layout
app.layout = html.Div([
    # Navigation Bar
    html.Nav([
        html.Div([
            html.H1('Hardware Price Tracker', className='nav-title'),
            html.Div([
                dcc.Dropdown(
                    id='product-search',
                    options=[],
                    placeholder='Search for a product...',
                    className='search-input',
                    searchable=True,
                    clearable=True
                )
            ], className='search-container')
        ], className='nav-content')
    ], className='navbar'),

    # Main Content
    html.Main([
        html.Div(id='page-content', className='main-content')
    ]),

    # Store for comparison products
    dcc.Store(id='comparison-store')
])


@app.callback(
    [Output('product-search', 'options'),
     Output('page-content', 'children')],
    [Input('product-search', 'value'),
     Input('product-search', 'search_value'),
     Input({'type': 'comparison-dropdown', 'index': ALL}, 'value')]
)
def update_page(selected_product, search_value, comparison_values):
    ctx = callback_context
    df = load_and_process_data()

    if df.empty:
        return [], html.Div("No data available", className='error-message')

    # Handle product filtering for search
    all_products = sorted(df[df.columns[0]].unique())
    if search_value:
        filtered_products = [p for p in all_products if search_value.lower() in p.lower()]
    else:
        filtered_products = all_products

    options = [{'label': p, 'value': p} for p in filtered_products]

    if not selected_product:
        return options, html.Div([
            html.H2("Welcome to Hardware Price Tracker", className='welcome-title'),
            html.P("Select a product to view detailed price analysis and history.",
                   className='welcome-message'),
            html.Div([
                html.H3("Popular Products", className='section-title'),
                html.Div([
                    html.Button(
                        product,
                        id={'type': 'product-button', 'index': i},
                        className='popular-product'
                    ) for i, product in enumerate(all_products[:6])
                ], className='popular-products')
            ], className='welcome-section')
        ], className='welcome-container')

    compare_with = comparison_values[0] if comparison_values else None
    return options, create_product_page(df, selected_product, compare_with)


@app.callback(
    Output('product-search', 'value'),
    [Input({'type': 'product-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'product-button', 'index': ALL}, 'children')]
)
def handle_product_click(n_clicks, labels):
    if not n_clicks or not any(n_clicks):
        return dash.no_update

    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id']
    idx = int(eval(button_id.split('.')[0])['index'])
    return labels[idx]


if __name__ == '__main__':
    app.run_server(debug=True)