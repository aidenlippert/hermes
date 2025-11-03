from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import structlog
from typing import Optional

logger = structlog.get_logger(__name__)


def setup_tracing(
    service_name: str = "hermes-backend",
    service_version: str = "2.0.0",
    otlp_endpoint: Optional[str] = None,
    console_export: bool = True
) -> trace.Tracer:
    """
    Set up OpenTelemetry distributed tracing.

    Args:
        service_name: Name of the service for trace identification
        service_version: Version of the service
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317")
        console_export: Whether to export traces to console (useful for development)

    Returns:
        Configured tracer instance
    """
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": "production"
    })

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("otlp_exporter_configured", endpoint=otlp_endpoint)
        except Exception as e:
            logger.error("otlp_exporter_failed", error=str(e))

    if console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)
    logger.info("tracing_initialized", service_name=service_name)

    return tracer


def instrument_fastapi(app):
    """
    Automatically instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(app)
    logger.info("fastapi_instrumented")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance for manual instrumentation.

    Args:
        name: Name for the tracer (typically __name__ from calling module)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def add_span_attributes(span: trace.Span, attributes: dict):
    """
    Add custom attributes to a span.

    Args:
        span: The span to add attributes to
        attributes: Dictionary of attribute key-value pairs
    """
    for key, value in attributes.items():
        span.set_attribute(key, value)


def trace_async(span_name: str, **attributes):
    """
    Decorator for tracing async functions.

    Usage:
        @trace_async("my_operation", user_id="123")
        async def my_function():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                add_span_attributes(span, attributes)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_sync(span_name: str, **attributes):
    """
    Decorator for tracing synchronous functions.

    Usage:
        @trace_sync("my_operation", user_id="123")
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                add_span_attributes(span, attributes)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator
