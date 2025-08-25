def add_event_sink_to_env(env: dict, sink_name: str, daemon_url: str):
    env["TOOLBOX_EVENTS_SINK_KIND"] = "http"
    env["TOOLBOX_EVENTS_SINK_SOURCE_NAME"] = sink_name
    env["TOOLBOX_EVENTS_SINK_DAEMON_URL"] = daemon_url
