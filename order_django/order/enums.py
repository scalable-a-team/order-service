class QueueName:
    ORDER = 'order'
    PRODUCT = 'product'


class EventStatus:
    CREATE_ORDER = 'create_order'
    REJECT_ORDER = 'reject_order'


class OrderStatus:
    IN_PROGRESS = 'in_progress'
    SUCCESS = 'success'
    FAILED = 'failed'
    SHIPPED = 'shipped'

    _state = {
        IN_PROGRESS: {SUCCESS, FAILED},
        SUCCESS: {SHIPPED}
    }

    @classmethod
    def is_new_status_valid(cls, current_status, new_status):
        return new_status in cls._state.get(current_status, set())
