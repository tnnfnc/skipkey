"""Blinking icon and animated image.
"""
from kivy.clock import Clock


class Blinker():
    """A blinker alternates two properties of a widget.
    """

    def __init__(self, owner, attr_name, flash_count):
        """A blinker alternates two properties of a widget.

        Args:
            owner ([type]): [description]
            attr_name ([type]): [description]
            flash_count ([type]): [description]
        """
        self.blink_events = []
        self.app = owner
        self.attr_name = attr_name
        self.flash_count = flash_count
        self.cycle_counter = 0
        self._attr_value_on = None
        self._attr_value_off = None
        self.event = None

    def set_attr_value_on_off(self, on, off):
        """[summary]

        Args:
            on ([type]): [description]
            off ([type]): [description]
        """
        self._attr_value_on = on
        self._attr_value_off = off

    def blink(self, secs):
        """[summary]

        Args:
            secs ([type]): [description]
        """
        self.stop()
        self._set_value(self._attr_value_off)
        self.blink_events.append(Clock.schedule_interval(self.cycle(), secs))

    def _set_value(self, value):
        setattr(self.app, self.attr_name, value) if hasattr(
            self.app, self.attr_name) else None

    def _get_value(self):
        return getattr(self.app, self.attr_name) if hasattr(
            self.app, self.attr_name) else None

    def stop(self):
        """[summary]
        """
        if len(self.blink_events) > 0:
            for event in self.blink_events:
                event.cancel()
            del self.blink_events[:]
        self.cycle_counter = 0

    def reset(self):
        """[summary]
        """
        self.stop()
        self._set_value(self._attr_value_off)

    def cycle(self):
        """[summary]
        """
        def f(t):
            if self.cycle_counter >= self.flash_count:
                self.stop()
            else:
                if self._get_value() == self._attr_value_off:
                    self._set_value(self._attr_value_on)
                    self.cycle_counter += 1
                else:
                    self._set_value(self._attr_value_off)
        return f


class AnimatedIcon():
    """[summary]
    """

    def __init__(self, owner, attr_name):
        """[summary]

        Args:
            owner ([type]): [description]
            attr_name ([type]): [description]
        """
        self.animation_events = []
        self.app = owner
        self.attr_name = attr_name
        self.cycle_counter = 0
        self.event = None
        # self.flash_count = flash_count

    def set_attr_values(self, values=[]):
        """[summary]

        Args:
            values (list, optional): [description]. Defaults to [].
        """
        self._attr_values = values

    def start(self, secs):
        """[summary]

        Args:
            secs ([type]): [description]
        """
        if len(self._attr_values) == 0:
            return
        self.stop()
        self._set_value(self._attr_values[0])
        self.animation_events.append(
            Clock.schedule_interval(self._cycle(), secs))

    def _set_value(self, value):
        setattr(self.app, self.attr_name, value) if hasattr(
            self.app, self.attr_name) else None

    def _get_value(self):
        return getattr(self.app, self.attr_name) if hasattr(
            self.app, self.attr_name) else None

    def stop(self):
        """[summary]
        """
        if len(self.animation_events) > 0:
            for event in self.animation_events:
                event.cancel()
            del self.animation_events[:]

    def reset(self):
        """[summary]
        """
        if len(self._attr_values) == 0:
            return
        self.stop()
        self._set_value(self._attr_values[0])

    def _cycle(self):
        def f(t):
            self._set_value(self._attr_values[self.cycle_counter])
            self.cycle_counter = 0 if self.cycle_counter == len(
                self._attr_values) - 1 else self.cycle_counter + 1
        return f
