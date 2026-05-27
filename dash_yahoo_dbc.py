import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc  # 新增：匯入 Bootstrap 元件庫
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 初始化 Dash 應用，並套用 Bootstrap 的 FLATLY 現代主題
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# 網頁版面配置 (改用 Bootstrap 網格與卡片設計)
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("📈 股市 K 線與均線分析系統", className="text-center my-4", style={'fontFamily': 'Microsoft JhengHei'}))
    ]),
    
    # 使用 Bootstrap 卡片 (Card) 讓控制面板更有質感
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # 股票代號輸入區
                dbc.Col([
                    dbc.Label("股票代號：", className="fw-bold"),
                    dbc.Input(
                        id='stock-id-input', 
                        type='text', 
                        value='2330.TW', 
                        className="text-center",
                        debounce=True  # 🌟 新增：設定為 True，按下 Enter 或失去焦點時才觸發 Callback
                    )
                ], md=4, sm=12, className="mb-3 mb-md-0"),
                
                # 獨立的起始日期 (使用 HTML5 原生美觀日期選擇器)
                dbc.Col([
                    dbc.Label("起始日期：", className="fw-bold"),
                    dbc.Input(id='start-date', type='date', value='2025-11-20')
                ], md=4, sm=12, className="mb-3 mb-md-0"),
                
                # 獨立的結束日期
                dbc.Col([
                    dbc.Label("結束日期：", className="fw-bold"),
                    dbc.Input(id='end-date', type='date', value='2026-05-22')
                ], md=4, sm=12)
            ], className="align-items-center")
        ])
    ], className="mb-4 shadow-sm"), # shadow-sm 增加淡淡的陰影質感
    
    # 互動式圖表容器
    dbc.Row([
        dbc.Col(dcc.Graph(id='stock-graph'))
    ])
], fluid=True, style={'padding': '20px', 'maxWidth': '1200px'})

# 設定 Callback：當股票代號或日期改變時，重新抓取資料並繪圖
@app.callback(
    Output('stock-graph', 'figure'),
    [Input('stock-id-input', 'value'),
     Input('start-date', 'value'),
     Input('end-date', 'value')]
)
def update_graph(stock_id, start_date, end_date):
    if not stock_id or not start_date or not end_date:
        return dash.no_update

    # 將字串格式的日期轉換為 datetime 物件 (HTML5 date input 傳回格式為 YYYY-MM-DD)
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    # 為了計算 SMA，資料抓取起始日需要提早 60 天
    fetch_start = start - timedelta(days=60)
    
    # 抓取 Yahoo Finance 資料 (加入 auto_adjust=False 以消除未來的警告)
    df = yf.download(stock_id, start=fetch_start, end=end, auto_adjust=False)

    if df.empty:
        # 如果選取的區間沒有資料或股票代號錯誤，回傳空圖表提示
        return go.Figure().update_layout(title=f"找不到 {stock_id} 的資料或該區間無資料，請重新確認", font=dict(family='Microsoft JhengHei'))

    # 展平欄位名稱 (應對 yfinance 新版 MultiIndex 格式)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 計算 SMA
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()

    # 裁切回使用者真正選擇的日期區間 (將前 60 天用於計算均線的資料切掉)
    # 注意：在 Plotly 中不需要像 Matplotlib 那樣把日期轉成字串，Plotly 能直接完美處理 datetime index
    df = df.loc[start:].copy()

    # 開始繪製 Plotly 圖表
    fig = go.Figure()

    # 1. 加入 K 線圖 (Candlestick)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線',
        increasing_line_color='red',  # 台灣股市習慣：上漲為紅色
        decreasing_line_color='green' # 台灣股市習慣：下跌為綠色
    ))

    # 2. 加入均線 (Scatter lines)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], mode='lines', name='5日均線', line=dict(color='blue', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_10'], mode='lines', name='10日均線', line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='20日均線', line=dict(color='purple', width=1.5)))

    # 3. 圖表版面與標題設定 (標題加入動態的 stock_id)
    fig.update_layout(
        title={
            'text': f"2026歡慶端午 {stock_id} 股市 K線與均線圖 ({start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')})",
            'y':0.9, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
            'font': dict(size=20)
        },
        xaxis_title='日期',
        yaxis_title='股價 (TWD)',
        xaxis_rangeslider_visible=False, # 隱藏底部的範圍滑桿 (因為已經有 DatePickerRange)
        template='plotly_white',
        height=600,
        font=dict(family='Microsoft JhengHei')
    )

    return fig

# 啟動 Server
if __name__ == '__main__':
    app.run(use_reloader=False, debug=True, port=5002)