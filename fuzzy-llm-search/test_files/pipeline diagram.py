# # pipeline_diagram.py

# from graphviz import Digraph

# def create_pipeline_diagram():
#     dot = Digraph(comment='Organization Names Processing Pipeline', format='png')

#     # Define nodes for each stage with brief descriptions
#     dot.node('S1', 'Stage 1:\nLoad and Preprocess Data')
#     dot.node('S2', 'Stage 2:\nVectorize Names')
#     dot.node('S3', 'Stage 3:\nGroup Similar Names \nUsing K-Nearest Neighbours')
#     dot.node('S4', 'Stage 4:\nFilter Groups with LLM')
#     dot.node('S5', 'Stage 5:\nCombine Groups With Overlapping Data')
#     dot.node('S6', 'Stage 6:\nProcess Combined Groups with LLM')
#     dot.node('S7', 'Stage 7:\nFurther Process Groups with LLM\n(Using Web Search)')

#     # Add edges between stages to represent the flow
#     dot.edges([('S1', 'S2'), ('S2', 'S3'), ('S3', 'S4'), ('S4', 'S5'), ('S5', 'S6'), ('S6', 'S7')])

#     # Customize appearance: top-to-bottom layout and higher resolution for better clarity
#     dot.attr(rankdir='TB')  # Set layout to top-to-bottom
#     dot.attr('node', shape='rectangle', style='filled', fillcolor='lightblue')
    
#     # Render with higher DPI to improve image clarity
#     dot.render(filename='pipeline_diagram', format='png', view=False)

# if __name__ == '__main__':
#     create_pipeline_diagram()

import plotly.graph_objects as go

fig = go.Figure()

# Define nodes
nodes = ["Load and Preprocess Data", "Vectorize Names", "Group Similar Names",
         "Filter Groups with LLM", "Combine Overlapping Data", "Process with LLM", "Further Processing with Web Search"]

# Add nodes
for i, node in enumerate(nodes):
    fig.add_trace(go.Scatter(
        x=[i],
        y=[0],
        mode='markers+text',
        marker=dict(size=20, color='lightblue'),
        text=[node],
        textposition="bottom center"
    ))

# Add edges
for i in range(len(nodes)-1):
    fig.add_shape(type="line",
                  x0=i, y0=0, x1=i+1, y1=0,
                  line=dict(color="gray", width=2))

fig.update_layout(showlegend=False,
                  xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                  yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                  title="Organization Names Processing Pipeline")

fig.write_image("pipeline_diagram.png")

