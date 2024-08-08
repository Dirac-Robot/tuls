import streamlit as st
from beacon.adict import ADict
import plotly.express as px
import pandas as pd


class Plot:
    PAIRED_AXIS_CHART_TYPES = (
        'SCATTER',
    )
    MULTI_AXIS_CHART_TYPES = (
        'PARALLEL',
        'HISTOGRAM'
    )

    def __init__(self):
        self.data_columns = dict()
        self.chart_type = None
        self.chart_kwargs = dict()
        self._figure = None

    def set_data_columns(self, data_columns):
        self.data_columns = data_columns
        self._figure = None

    def set_chart(self, chart_type, **chart_kwargs):
        self.chart_type = chart_type
        self.chart_kwargs = chart_kwargs
        self._figure = None

    @property
    def figure(self):
        if self._figure is None:
            df = pd.DataFrame.from_dict(self.data_columns)
            if self.chart_type == 'SCATTER':
                new_figure = px.scatter(df, **self.chart_kwargs)
            elif self.chart_type == 'HISTOGRAM':
                new_figure = px.histogram(
                    df,
                    histfunc='count',
                    **self.chart_kwargs
                )
                self._figure = new_figure
            elif self.chart_type == 'PARALLEL':
                new_figure = px.parallel_coordinates(df, **self.chart_kwargs)
                new_figure.update_layout(margin=dict(l=50, r=50))
            else:
                raise ValueError(f'{self.chart_type} type chart is not supported.')
            self._figure = new_figure
        return self._figure


class Dashboard:
    DEFAULT_CONFIG = ADict(
        plot=ADict(
            histogram=ADict(min_value=10, max_value=1000, step=1)
        )
    )

    def __init__(self, config=None):
        self.config = config or self.DEFAULT_CONFIG.clone()
        self.data = ADict()
        self.plots = dict()
        self.index = 0
        self.selected_indices = dict()

    def stack_data_points(self, data_points):
        self.data.update(data_points)

    def add_empty_plot(self):
        self.plots[self.index] = Plot()
        self.selected_indices[self.index] = []
        self.index += 1

    def remove_plot(self, index=-1):
        self.plots.pop(index)
        self.selected_indices.pop(index)

    def draw_plot(self, index):
        plot_container = st.container(border=True)
        plot = None
        with plot_container:
            select_col, chart_col = st.columns([0.25, 0.75])
            with select_col:
                height = st.slider('Chart Height:', 400, 1200, key=f'chart-height-{index}')
                plot_types = Plot.PAIRED_AXIS_CHART_TYPES+Plot.MULTI_AXIS_CHART_TYPES
                chart_type = st.selectbox('Chart Type:', plot_types, key=f'chart-type-{index}')
                chart_kwargs = ADict(height=height)
                data_keys = list(self.data.keys())
                if chart_type in Plot.PAIRED_AXIS_CHART_TYPES:
                    max_selections = 2
                else:
                    max_selections = None
                selections = st.multiselect(
                    f'Axes:',
                    data_keys,
                    max_selections=max_selections,
                    key=f'selections-{index}'
                )
                if chart_type == 'HISTOGRAM':
                    num_bins = st.slider(
                        'Number of Bins:',
                        **self.config.plot.histogram,
                        key=f'slider-{index}',
                    )
                    chart_kwargs['nbins'] = num_bins
                elif chart_type in Plot.PAIRED_AXIS_CHART_TYPES:
                    if selections:
                        chart_kwargs.x = self.data[selections][0]
                        if len(selections) == 2:
                            chart_kwargs.y = self.data[selections[1]]
                    chart_kwargs.labels = selections
                plot = self.plots[index]
                plot.set_data_columns({selection: self.data[selection] for selection in selections})
                plot.set_chart(chart_type, **chart_kwargs)
                st.button(
                    'Remove',
                    use_container_width=True,
                    key=f'remove-this-plot-{index}',
                    on_click=lambda: self.remove_plot(index)
                )
            with chart_col:
                if plot is not None and plot.figure is not None:
                    selected_items = st.plotly_chart(plot.figure, key=f'chart-{index}', on_select='rerun')['selection']
                    self.selected_indices[index] = selected_items['point_indices']

    def render(self):
        side_area, plot_area = st.columns([0.2, 0.8])
        with side_area:
            add_new_plot = st.button('Add New Plot', use_container_width=True)
            open_viewer = st.button('Open Viewer', use_container_width=True)
            if add_new_plot:
                self.add_empty_plot()
            if open_viewer:
                self.open_viewer_from_selections()
        with plot_area:
            for index in self.plots:
                self.draw_plot(index)

    @st.dialog('Media Viewer')
    def open_viewer_from_selections(self):
        widget_type = st.selectbox('Select Widget:', ('VIDEO', 'IMAGE'))
        selected_only = st.checkbox('Use Selected Data Only', value=False)
        if selected_only:
            selected_indices = set()
            for indices in self.selected_indices.values():
                selected_indices.union(set(indices))
            selected_indices = list(selected_indices)
            selected_ids = [self.data.data_id[index] for index in selected_indices]
        else:
            selected_ids = self.data.data_id
        if widget_type == 'VIDEO':
            video_path = st.selectbox(
                'ID:',
                [
                    self.data[selected_id].video_path
                    for selected_id in selected_ids
                    if 'video_path' in self.data[selected_id]
                ]
            )
            st.video(video_path)
        else:
            image_path = st.selectbox(
                'ID:',
                [
                    self.data[selected_id].image_path
                    for selected_id in selected_ids
                    if 'image_path' in self.data[selected_id]
                ]
            )
            st.image(image_path)

    @classmethod
    def generate_dashboard(cls):
        if 'dashboard' not in st.session_state:
            st.session_state.dashboard = cls()
        return st.session_state.dashboard


if __name__ == '__main__':
    import numpy as np
    dashboard = Dashboard.generate_dashboard()
    st.set_page_config(layout="wide")
    ids = [str(index) for index in range(100)]
    x = np.linspace(0, 10, 100)
    y = np.linspace(0, 1, 100)
    z = np.logspace(0, 10, 100)
    dashboard.stack_data_points({'d1': x, 'd2': y, 'd3': z})
    dashboard.render()
