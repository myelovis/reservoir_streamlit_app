"""Plotly figures for weather, correlation and forecasting."""
import plotly.graph_objects as go


def weather_plot(result, title, unit):
    fig = go.Figure(go.Scatter(x=result.index, y=result.value, name='Observed', line_color='#247a91'))
    if 'lower' in result:
        for column in ['lower','upper']:
            fig.add_trace(go.Scatter(x=result.index, y=result[column], name=column.title()+' limit', line=dict(color='#d9932c',dash='dash')))
    outliers = result.loc[result.flag]
    fig.add_trace(go.Scatter(x=outliers.index,y=outliers.value,mode='markers',name='Flagged',marker=dict(color='#d94453',size=5)))
    return fig.update_layout(title=title,xaxis_title='Time (UTC)',yaxis_title=unit,height=430)


def correlation_plot(result):
    fig = go.Figure(go.Scatter(x=result.index,y=result.correlation,name='Rolling correlation',line_color='#247a91'))
    fig.add_hline(y=0,line_dash='dot')
    return fig.update_layout(xaxis_title='Week',yaxis_title='Pearson correlation',yaxis_range=[-1,1],height=380)


def forecast_animation(history, forecast, title):
    fig = go.Figure(go.Scatter(x=history.index,y=history,name='Training filling',line_color='#247a91'))
    fig.add_trace(go.Scatter(x=forecast.index,y=forecast.forecast,name='Recursive forecast',line_color='#dc7534'))
    if 'lower' in forecast:
        fig.add_trace(go.Scatter(x=forecast.index,y=forecast.lower,mode='lines',line_width=0,showlegend=False))
        fig.add_trace(go.Scatter(x=forecast.index,y=forecast.upper,mode='lines',line_width=0,fill='tonexty',fillcolor='rgba(220,117,52,.15)',name='Conditional interval'))
    frames = []
    for stop in range(1,len(forecast)+1):
        part = forecast.iloc[:stop]
        data = [go.Scatter(x=part.index,y=part.forecast)]
        if 'lower' in forecast:
            data += [go.Scatter(x=part.index,y=part.lower),go.Scatter(x=part.index,y=part.upper)]
        frames.append(go.Frame(name=str(stop),data=data,traces=list(range(1,1+len(data)))))
    fig.frames = frames
    fig.update_layout(title=title,xaxis_title='Week',yaxis_title='Filling (%)',height=470,
        xaxis_range=[history.index[0],forecast.index[-1]],
        updatemenus=[dict(type='buttons',buttons=[
            dict(label='Play forecast',method='animate',args=[None,{'frame':{'duration':200,'redraw':True},'fromcurrent':True}]),
            dict(label='Pause',method='animate',args=[[None],{'mode':'immediate','frame':{'duration':0}}])])],
        sliders=[dict(steps=[dict(label=str(i),method='animate',args=[[str(i)],{'mode':'immediate','frame':{'duration':0,'redraw':True}}]) for i in range(1,len(forecast)+1)],currentvalue={'prefix':'Forecast week: '})])
    return fig
