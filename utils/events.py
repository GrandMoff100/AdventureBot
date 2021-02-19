_reg = {}



def on_event(*events):
    """Register function to be called on given events"""
    def inner(func):
        for arg in events:
            if arg in _reg:
                _reg[arg].append(func)
            else:
                _reg[arg] = [func]


def register(*events):
    """Call registered listeners of given events on function completion"""
    def inner(func):
        async def run_events(*a, **kw):
            await func(*a, **kw)  # Main function
            for event in events:  # Iterate though registered listeners to call them
                for handler in _reg[event] if event in _reg else []:
                    handler(event)  # I want to be able to pass an event class or something, but idk how
    return inner


def call_event(*events):
    """Call registered listeners of given events"""
    for event in events:  # Iterate though registered listeners to call them
        for handler in _reg[event] if event in _reg else []:
            handler(event)  # Call listener
