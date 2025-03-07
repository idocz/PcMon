from dash import Dash, html, dcc, Input, Output, callback, State, no_update, ctx
import dash_bootstrap_components as dbc
import os
import socket
import json
from ping3 import ping

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    cfg = json.load(config_file)

# Function to send a Wake-on-LAN Magic Packet
def send_wol(mac_address):
    mac_bytes = bytes.fromhex(mac_address.replace(":", ""))
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic_packet, ('<broadcast>', 9))

# Function to check if Windows PC is online
def is_pc_online():
    try:
        response = ping(cfg['TARGET_IP'], timeout=1)
        return response is not None
    except Exception:
        return False

# Helper function to run SSH commands
def run_ssh_command(command):
    try:
        ssh_command = f"ssh -i {cfg['SSH_KEY_PATH']} {cfg['SSH_USER']}@{cfg['SSH_HOST']} {command}"
        return os.system(ssh_command)
    except Exception:
        return 1

# Initialize Dash app
app = Dash(
    __name__, 
    title="PC Remote Control",
    update_title="Updating...",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'
    ]
)

# Define button style for consistency - making them bigger
button_style = {
    'padding': '16px 30px',  # Increased padding
    'fontSize': '20px',      # Larger font
    'width': '300px',        # Fixed width for all buttons
    'height': '60px',        # Fixed height for all buttons
    'border': 'none',
    'borderRadius': '8px',
    'backgroundColor': '#007BFF',
    'color': 'white',
    'cursor': 'pointer',
    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.2)'
}

# Style for square refresh button
refresh_button_style = {
    'width': '50px',
    'height': '50px',
    'padding': '8px',
    'fontSize': '24px',
    'border': 'none',
    'borderRadius': '8px',
    'backgroundColor': '#007BFF',
    'color': 'white',
    'cursor': 'pointer',
    'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.2)',
    'display': 'inline-block',
    'verticalAlign': 'middle',
    'marginLeft': '10px'
}

# Define output message style for consistency
success_style = {'color': 'green', 'marginTop': '5px', 'fontWeight': 'bold'}
error_style = {'color': 'red', 'marginTop': '5px', 'fontWeight': 'bold'}

# Define the layout with a vertical stack of buttons like the original Flask app
app.layout = html.Div([
    # Interval component for triggering status check on load (fires once)
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # in milliseconds
        n_intervals=0,
        max_intervals=1  # Only fire once
    ),
    
    # Stylish notification modal
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("PC Control Notification"), className="bg-primary text-white"),
            dbc.ModalBody(id="notification-body", className="text-center py-4 fs-5"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="notification-modal",
        is_open=False,
        centered=True,
    ),
    
    # Header
    html.H1("PC Remote Control", style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    # Simple vertical stack layout
    html.Div([
        # Status section with label and refresh button
        html.Div([
            # Container for status label and refresh button
            html.Div([
                dcc.Loading(
                    id="status-loading",
                    type="circle", 
                    color="#007BFF",
                    children=html.Div(id='status-output', style={
                        'display': 'inline-block',
                        'verticalAlign': 'middle',
                        'fontWeight': 'bold',
                        'fontSize': '22px',
                        'minWidth': '180px',
                        'height': '40px',
                        'padding': '5px 0',
                        'textAlign': 'right',
                        'marginRight': '10px'
                    })
                ),
                html.Button(
                    html.I(className="fa fa-refresh"), 
                    id='check-status-btn', 
                    n_clicks=0, 
                    style=refresh_button_style
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '5px auto', 'width': '300px'})
        ], style={'margin': '15px auto 25px auto', 'textAlign': 'center', 'width': '320px'}),
        
        # Wake PC
        html.Div([
            html.Button("Wake PC", id='wake-btn', n_clicks=0, style=button_style),
            html.Div(id='wake-output', style={'height': '10px'})
        ], style={'margin': '5px auto', 'textAlign': 'center', 'width': '320px'}),
        
        # Sleep
        html.Div([
            html.Button("Sleep", id='sleep-btn', n_clicks=0, style=button_style),
            html.Div(id='sleep-output', style={'height': '10px'})
        ], style={'margin': '5px auto', 'textAlign': 'center', 'width': '320px'}),
        
        # Hibernate
        html.Div([
            html.Button("Hibernate", id='hibernate-btn', n_clicks=0, style=button_style),
            html.Div(id='hibernate-output', style={'height': '10px'})
        ], style={'margin': '5px auto', 'textAlign': 'center', 'width': '320px'}),
        
        # Shutdown
        html.Div([
            html.Button("Shutdown", id='shutdown-btn', n_clicks=0, style=button_style),
            html.Div(id='shutdown-output', style={'height': '10px'})
        ], style={'margin': '5px auto', 'textAlign': 'center', 'width': '320px'}),
        
        # Restart
        html.Div([
            html.Button("Restart", id='restart-btn', n_clicks=0, style=button_style),
            html.Div(id='restart-output', style={'height': '10px'})
        ], style={'margin': '5px auto', 'textAlign': 'center', 'width': '320px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px', 'maxWidth': '400px', 'margin': '0 auto'}),
    
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '600px', 'padding': '20px'})

# Callback to close the notification modal
@callback(
    Output("notification-modal", "is_open", allow_duplicate=True),
    [Input("close-modal", "n_clicks")],
    [State("notification-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(n_close, is_open):
    if n_close:
        return False
    return is_open

# Callback to initialize status and check PC on page load
@callback(
    Output('status-output', 'children'),
    Input('interval-component', 'n_intervals')
)
def check_status_on_load(n_intervals):
    if n_intervals is None:
        return "Loading..."
    
    # Actually check the PC status when the app loads
    is_online = is_pc_online()
    status = "Online" if is_online else "Offline"
    color = "green" if is_online else "red"
    return html.Span(f"Status: {status}", style={'color': color})

# Combined callback for all button actions
@callback(
    [Output('status-output', 'children', allow_duplicate=True),
     Output('wake-output', 'children'),
     Output('sleep-output', 'children'),
     Output('hibernate-output', 'children'),
     Output('shutdown-output', 'children'),
     Output('restart-output', 'children'),
     Output('notification-modal', 'is_open'),
     Output('notification-body', 'children')],
    [Input('check-status-btn', 'n_clicks'),
     Input('wake-btn', 'n_clicks'),
     Input('sleep-btn', 'n_clicks'),
     Input('hibernate-btn', 'n_clicks'),
     Input('shutdown-btn', 'n_clicks'),
     Input('restart-btn', 'n_clicks')],
    prevent_initial_call=True
)
def handle_actions(status_clicks, wake_clicks, sleep_clicks, hibernate_clicks, shutdown_clicks, restart_clicks):
    # Initialize all outputs with no_update
    outputs = [no_update] * 8
    
    # Determine which button was clicked
    button_id = ctx.triggered_id if ctx.triggered_id else 'no-id'
    
    # Check Status
    if button_id == 'check-status-btn':
        is_online = is_pc_online()
        status = "Online" if is_online else "Offline"
        color = "green" if is_online else "red"
        outputs[0] = html.Span(f"Status: {status}", style={'color': color})
        # Don't show modal for status check
        outputs[6] = False  
    
    # Wake PC
    elif button_id == 'wake-btn':
        send_wol(cfg['TARGET_MAC'])
        outputs[1] = ""  # No visible output on page
        outputs[6] = True  # Show modal
        outputs[7] = "Magic Packet Sent! PC should wake up shortly."
    
    # Sleep PC
    elif button_id == 'sleep-btn':
        result = run_ssh_command("powershell.exe -Command \"rundll32.exe powrprof.dll,SetSuspendState 0,1,0\"")
        if result == 0:
            msg = "Sleep command successful! PC is now sleeping."
        else:
            msg = "Error: Failed to put PC to sleep. Please check connection."
        outputs[2] = ""  # No visible output on page
        outputs[6] = True  # Show modal
        outputs[7] = msg  # Modal message
    
    # Hibernate PC
    elif button_id == 'hibernate-btn':
        result = run_ssh_command("powershell.exe -Command \"shutdown /h\"")
        if result == 0:
            msg = "Hibernate command successful! PC is now hibernating."
        else:
            msg = "Error: Failed to hibernate PC. Please check connection."
        outputs[3] = ""  # No visible output on page
        outputs[6] = True  # Show modal
        outputs[7] = msg  # Modal message
    
    # Shutdown PC
    elif button_id == 'shutdown-btn':
        result = run_ssh_command("powershell.exe -Command \"shutdown /s /t 0\"")
        if result == 0:
            msg = "Shutdown command successful! PC is shutting down."
        else:
            msg = "Error: Failed to shutdown PC. Please check connection."
        outputs[4] = ""  # No visible output on page
        outputs[6] = True  # Show modal
        outputs[7] = msg  # Modal message
    
    # Restart PC
    elif button_id == 'restart-btn':
        result = run_ssh_command("powershell.exe -Command \"shutdown /r /t 0\"")
        if result == 0:
            msg = "Restart command successful! PC is restarting."
        else:
            msg = "Error: Failed to restart PC. Please check connection."
        outputs[5] = ""  # No visible output on page
        outputs[6] = True  # Show modal
        outputs[7] = msg  # Modal message
    
    return outputs

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=cfg['PORT'], debug=cfg['DEBUG'])