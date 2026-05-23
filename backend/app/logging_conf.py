import contextvars
import logging
import sys

# Set by InternalSecretMiddleware/CorrelationMiddleware on every request;
# pulled by the logging Filter below so every log line during a request is
# tagged with that request's id.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'request_id', default='-'
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def configure_logging(level: str = 'INFO') -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s | %(message)s'
        )
    )
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)
    root.setLevel(level)
