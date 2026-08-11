"""OpenTelemetry + Arize Phoenix tracing setup for the agent."""

_tracing_started = False


def init_tracing():
    """Launch a local Phoenix session and instrument LangChain. Imports
    are deliberately deferred inside this function, not at module level
    -- Phoenix has a known compatibility bug on some Python 3.11 patch
    versions (see docs/PROJECT_DESIGN.md CI notes), and a broken import
    at module level would crash the whole app before startup even runs.
    Deferring it here means a Phoenix failure only disables tracing,
    it can't take down the API."""
    global _tracing_started
    if _tracing_started:
        return None

    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor
    except Exception as e:
        print(f"Phoenix could not be imported, tracing disabled: {e}")
        return None

    try:
        session = px.launch_app()
        tracer_provider = register(project_name="renewal-risk-agent")
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception as e:
        print(f"Phoenix failed to start, tracing disabled: {e}")
        return None

    _tracing_started = True
    print(f"Phoenix tracing UI: {session.url}")
    return session