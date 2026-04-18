import logging
import traceback
import typing as t
import webbrowser
from threading import Thread
import numpy as np  # noqa: F401 - pre-load before plotly uses it from callback threads
import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

from utils.dc.agent_stats import AgentStats
from .config import DashboardConfig
from utils.process_manager import ProcessManager

# (data_key, title, target_value)
# target_value=None -> cumulative count chart, no deviation
_METRICS = [
    ("win_rate",    "Win Rate (%)",       100),
    ("death_cum",   "Deaths (total)",     None),
    ("steps_pct",   "Steps (% of max)",    0),
    ("coins_pct",   "Coins (%)",          100),
    ("hp_pct",      "HP Lost (%)",          0),
    ("shields_pct", "Shields (%)",         100),
    ("epsilon",     "Epsilon",              0),
    ("reward_cum",  "Cumulative Reward",  None),
]

_COLORS = {
    "win_rate":    "#00d4ff",
    "death_cum":   "#ff6b6b",
    "steps_pct":   "#c77dff",
    "coins_pct":   "#00ff99",
    "hp_pct":      "#ff9f43",
    "shields_pct": "#ffd93d",
    "epsilon":     "#a8e6cf",
    "reward_cum":  "#7ee787",
}

_CARD_STYLE = {
    "backgroundColor": "#161b22",
    "borderRadius":    "8px",
    "border":          "1px solid #30363d",
    "padding":         "8px",
    "marginBottom":    "10px",
}

_BG = "#0d1117"

class Dashboard:

    process_manager: ProcessManager

    def __init__(self, config: DashboardConfig):

        self.config = config
        
        self.log = config.logger
        
        self.stats = config.agent_stats

        self.__file__ = __file__

        self.process_manager = ProcessManager(
            parent = self,
            agent = config.agent,
        )

    def __start(self) -> None:

        try:

            app = self._build_app()
            
            url = "http://%s:%d" % (self.config.host, self.config.port)
            
            webbrowser.open(url)
            
            app.run(
                host = self.config.host,
                port = self.config.port,
                debug = False,
                use_reloader = False,
            )

            self.log.info("Web Server Thread stopped!")

        except Exception:
            self.log.error(traceback.format_exc())

    def _start_dashboard(self) -> None:

        self.log.info("Run Dashboard Thread!")

        self.thread = Thread(name = "DashboardThread", target = self.__start, daemon = True)
        
        self.thread.start()

    def run(self, **kwargs) -> None:

        self.process_manager.start_main_process_loop()

    def _build_app(self) -> dash.Dash:

        app = dash.Dash(
            __name__,
            update_title = None,
            assets_ignore = ".*",
        )

        app.index_string = (
            "<!DOCTYPE html>"
            "<html><head>"
            "{%metas%}"
            "<title>Maze Agent - Live Statistics</title>"
            "{%favicon%}{%css%}"
            "<style>"
            "html,body{margin:0;padding:0;overflow-x:hidden;background:#0d1117;}"
            "#metric-toggle label{color:#58a6ff !important;}"
            "</style>"
            "</head><body>"
            "{%app_entry%}{%config%}{%scripts%}{%renderer%}"
            "</body></html>"
        )

        metric_cards = []

        for key, title, _ in _METRICS:

            color = _COLORS[key]

            metric_cards.append(
                html.Div(
                    id = "card-%s" % key,
                    style = _CARD_STYLE,
                    children = [
                        dcc.Graph(
                            id = "graph-%s" % key,
                            style  = {"height": "220px"},
                            config = {"displayModeBar": False},
                        ),
                    ],
                )
            )

        all_keys = [key for key, _, _ in _METRICS]

        checklist_options = [
            {"label": title, "value": key}
            for key, title, _ in _METRICS
        ]

        app.layout = html.Div(
            style = {
                "backgroundColor": _BG,
                "padding": "16px 24px",
                "minHeight": "100vh",
                "fontFamily": "monospace",
            },
            children = [

                # header row
                html.Div(
                    style = {
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "space-between",
                        "marginBottom": "12px",
                    },
                    children = [
                        html.H2(
                            "Maze Agent - Live Statistics",
                            style = {
                                "color": "#58a6ff",
                                "margin": "0",
                                "letterSpacing": "2px",
                            },
                        ),
                        html.Div(
                            id = "episode-counter",
                            style = {
                                "color": "#8b949e",
                                "fontSize": "14px",
                            },
                        ),
                    ],
                ),

                # toggle bar
                html.Div(
                    style = {
                        "backgroundColor": "#161b22",
                        "borderRadius": "8px",
                        "border": "1px solid #30363d",
                        "padding": "8px 16px",
                        "marginBottom": "16px",
                    },
                    children = [
                        dcc.Checklist(
                            id = "metric-toggle",
                            options = checklist_options,
                            value = all_keys,
                            inline = True,
                            style = {"color": "#58a6ff", "fontSize": "13px"},
                            inputStyle = {"marginRight": "4px"},
                            labelStyle = {
                                "marginRight": "18px",
                                "cursor": "pointer",
                            },
                        ),
                    ],
                ),

                # grid of cards
                html.Div(
                    id = "metrics-grid",
                    style = {
                        "display": "grid",
                        "gridTemplateColumns": "repeat(2, 1fr)",
                        "gap": "12px",
                    },
                    children = metric_cards,
                ),

                dcc.Interval(
                    id = "interval",
                    interval = self.config.update_ms,
                    n_intervals = 0,
                ),

                # hidden store for data
                dcc.Store(id = "stats-store"),
            ],
        )

        # callback: fetch data once per interval
        app.callback(
            Output("stats-store", "data"),
            Output("episode-counter", "children"),
            Input("interval", "n_intervals"))(self.__update_store)

        # callback per metric card: show/hide + update graph
        for key, title, target in _METRICS:

            color = _COLORS[key]

            app.callback(
                Output("card-%s" % key, "style"),
                Output("graph-%s" % key, "figure"),
                Input("stats-store", "data"),
                Input("metric-toggle", "value"))(self.__make_card_callback(key, title, target, color))

        return app

    def __update_store(self, _: int) -> tuple[dict, str]:

        data: dict = self.stats.snapshot()
        
        n: int = data.get("total", len(data.get("ids", [])))
        
        return data, "Episodes: %d" % n

    def __make_card_callback(self, key: str, title: str, target: t.Optional[int], color: str) -> t.Callable:

        def update_card(data: dict, visible: list[str]) -> tuple[dict, go.Figure]:

            hidden: dict = dict(_CARD_STYLE, display = "none")
            shown: dict  = dict(_CARD_STYLE, display = "block")

            if key not in visible:
                return hidden, go.Figure()

            fig = go.Figure()
            self.__apply_theme(fig, title)

            if not data or "ids" not in data:
                return shown, fig

            ids: list = data["ids"]
            values: list = data.get(key, [])
            avg: list = data.get(key + "_avg", [])

            if not values:
                return shown, fig

            if target is None:
                self.__add_area(fig, ids, values, avg, color)
                
            else:
                
                fig.add_trace(go.Scatter(
                    x = ids, y = values,
                    mode = "lines",
                    line = dict(color = color, width = 0.8),
                    opacity = 0.50,
                    name = "Value",
                    showlegend = False,
                ))

                if len(avg) > 0:
                    
                    fig.add_trace(go.Scatter(
                        x = ids, y = avg,
                        mode = "lines",
                        line = dict(color = color, width = 2),
                        name = "Avg",
                        showlegend = False,
                    ))

                fig.add_hline(
                    y = target,
                    line = dict(color = "#30363d", width = 1, dash = "dot"),
                )

            fig.update_layout(xaxis = dict(range = [ids[0], ids[-1]]))

            return shown, fig

        return update_card

    @staticmethod
    def __add_area(fig: go.Figure, ids: list, values: list, avg: list, color: str) -> None:

        fig.add_trace(go.Scatter(
            x = ids, y = values,
            mode = "lines",
            fill = "tozeroy",
            line = dict(color=color, width=0.8),
            opacity = 0.50,
            fillcolor = "rgba(255,107,107,0.10)",
            showlegend = False,
        ))

        if len(avg) > 0:
            
            fig.add_trace(go.Scatter(
                x = ids, y = avg,
                mode = "lines",
                line = dict(color = color, width = 2),
                showlegend = False,
            ))

        fig.update_layout(xaxis = dict(range = [ids[0], ids[-1]]))

    @staticmethod
    def __apply_theme(fig: go.Figure, title: str = "") -> None:

        fig.update_layout(
            template = "plotly_dark",
            paper_bgcolor = "#161b22",
            plot_bgcolor = "#161b22",
            margin = dict(t = 30, b = 25, l = 40, r = 12),
            font = dict(family = "monospace", size = 10, color ="#8b949e"),
            hoverlabel = dict(bgcolor = "#161b22", font_color = "#cdd9e5"),
            title = dict(
                text = title,
                font = dict(color = "#58a6ff", size = 12),
                x = 0.5,
                y = 0.97,
            ),
            xaxis = dict(showgrid = False, zeroline = False, color = "#8b949e"),
            yaxis = dict(showgrid = True, gridcolor = "#21262d", zeroline = False, color = "#8b949e"),
        )
