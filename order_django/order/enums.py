class QueueName:
    ORDER = 'order'
    PRODUCT = 'product'


class EventStatus:
    CREATE_ORDER = 'create_order'
    REJECT_ORDER = 'reject_order'
    UPDATE_ORDER_SUCCESS = 'update_order_success'
    UPDATE_ORDER_REJECTED = 'update_order_rejected'


class OrderStatus:
    PENDING = 'pending'
    SUCCESS = 'success'
    REJECTED = 'rejected'

    _state = {
        PENDING: {SUCCESS, REJECTED},
    }

    _event_status = {
        SUCCESS: EventStatus.UPDATE_ORDER_SUCCESS,
        REJECTED: EventStatus.UPDATE_ORDER_REJECTED
    }

    @classmethod
    def is_new_status_valid(cls, current_status, new_status):
        return new_status in cls._state.get(current_status, set())

    @classmethod
    def get_event_from_new_status(cls, new_status):
        return cls._event_status.get(new_status)
