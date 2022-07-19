import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    if os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
        resource = Resource.create(attributes={
            "service.name": "OrderDjangoApp"
        })

        trace.set_tracer_provider(TracerProvider(resource=resource))
        span_processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'))
        )
        trace.get_tracer_provider().add_span_processor(span_processor)
        DjangoInstrumentor().instrument()
        LoggingInstrumentor().instrument(set_logging_format=True)
        RequestsInstrumentor().instrument()
