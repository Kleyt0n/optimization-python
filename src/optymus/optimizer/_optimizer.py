# Full path: optymus/optymus/optimizer/_optimize.py

import dash
import dash_bootstrap_components as dbc
import jax
import pandas as pd
from dash import dcc, html
from optymus.methods import (
    adagrad,
    adam,
    adamax,
    bfgs,
    conjugate_gradient,
    gradient_descent,
    newton_raphson,
    powell,
    rmsprop,
    univariant,
)
from optymus.plots import plot_optim

jax.config.update("jax_enable_x64", True)

METHODS = {
    "univariant": univariant,
    "powell": powell,
    "gradient_descent": gradient_descent,
    "conjugate_gradient": conjugate_gradient,
    "bfgs": bfgs,
    "newton_raphson": newton_raphson,
    "adagrad": adagrad,
    "rmsprop": rmsprop,
    "adam": adam,
    "adamax": adamax
}


class Optimizer:
    def __init__(self, f_obj=None, f_constr=None, x0=None, method='gradient_descent', tol=1e-5, max_iter=100, **kwargs):
        """
        Initializes the Optimizer class.

        Args:
            f_obj (function): The objective function to be minimized.
            x0 (np.ndarray): The initial guess for the minimum.
            method (str, optional): The optimization method to use. Defaults to 'gradient_descent'.
            tol (float, optional): The tolerance for convergence. Defaults to 1e-5.
            max_iter (int, optional): The maximum number of iterations. Defaults to 100.
        """
        self.f_obj = f_obj
        self.f_constr = f_constr
        self.x0 = x0
        self.method = method
        self.tol = tol
        self.max_iter = max_iter

        if self.method not in METHODS:
            msg = f"Method '{method}' not available. Available methods: {list(METHODS.keys())}"
            raise ValueError(msg)

        if self.f_obj is None:
            msg = "Objective function is required."
            raise ValueError(msg)

        if self.x0 is None:
            msg = "Initial guess is required."
            raise ValueError(msg)

        # Run the optimization and store results
        self.opt = METHODS[self.method](f_obj=self.f_obj,
                                        f_constr=self.f_constr,
                                        x0=self.x0,
                                        tol=self.tol,
                                        max_iter=self.max_iter,
                                        **kwargs)

    def check_dimension(self):
        """Returns the dimension of the problem."""
        return len(self.x0)

    def get_results(self):
        """Returns the optimization results dictionary."""
        return self.opt

    def print_report(self):
        """Prints a formatted summary of the optimization results."""
        table_data = {
            "Method": [self.method],
            "Initial Guess": [self.x0],
            "Optimal Solution": [self.opt.get('xopt', 'N/A')],
            "Objective Function Value": [self.opt.get('fmin', 'N/A')],
            "Number of Iterations": [self.opt.get('num_iter', 'N/A')],
        }

        return pd.DataFrame(table_data, index=['Optimization Results'])

    def plot_results(self, **kwargs):
        """Plots the optimization path and function surface."""
        plot_optim(self.f_obj, self.x0, self.opt, **kwargs)

    def create_dashboard(self, port=8050):
        """Generates a Dash dashboard with optimization results."""

        app = dash.Dash(__name__, title="optymus", external_stylesheets=[dbc.themes.FLATLY])

        if self.f_constr is not None:
            self.method = f"{self.method} with constraints"

        self.path = self.opt.get('path', None)
        fig = plot_optim(self.f_obj, self.x0, self.opt, path=True, show=False)

        navbar = html.H4(
            "Optymus Dashboard", className="bg-primary text-white p-2 mb-2 text-left"
        )

        # Create Dash layout
        app.layout = html.Div(children=[
            navbar,

            dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Function surface and countour", className="card-title"),
                                dcc.Graph(id='contour-plot', figure=fig),
                            ]
                        )
                    )
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Optimization Details", className="card-title"),
                                dbc.Table(
                                    [
                                        html.Tr([html.Th("Parameter"), html.Th("Value")]),
                                        html.Tr([html.Td("Method"), html.Td(str(self.method))]),
                                        html.Tr([html.Td("Final Solution"), html.Td(str(self.opt.get('xopt', 'N/A')))]),
                                        html.Tr([html.Td("Objective Function Value"), html.Td(str(self.opt.get('fmin', 'N/A')))]),
                                        html.Tr([html.Td("Number of Iterations"), html.Td(str(self.opt.get('num_iter', 'N/A')))]),
                                        html.Tr([html.Td("Initial Guess"), html.Td(str(self.x0))]),
                                    ],
                                    bordered=True,
                                )
                            ]
                        )
                    )
                ),
            ],
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            dcc.Markdown(
                                id='pseudocode',
                                children=f"""
                                ```python
                                def {self.method.lower()}(f_obj, x0):
                                    # Pseudocode for {self.method}
                                    # ...
                                ```
                                """
                            )
                        )
                    ),
                ],
            ),
        ])

        # Run the Dash app
        app.run_server(port=port, debug=False, use_reloader=False)

        # open the browser
        import webbrowser
        webbrowser.open(f'http://localhost:{port}')

