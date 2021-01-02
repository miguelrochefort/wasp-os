# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

import wasp
import icons
import fonts

class StopwatchApp():
    """Stopwatch application.

    .. figure:: res/TimerApp.png
        :width: 179

        Screenshot of the stopwatch application
    """
    NAME = 'Timer'
    ICON = icons.app

    def __init__(self):
        self._reset()
        self._count = 0

    def foreground(self):
        """Activate the application."""
        wasp.system.bar.clock = False
        self._draw()
        wasp.system.request_tick(97)
        wasp.system.request_event(wasp.EventMask.TOUCH |
                                  wasp.EventMask.BUTTON |
                                  wasp.EventMask.NEXT)
        self.press(None, True)

    def sleep(self):
        return True

    def wake(self):
        self._update()

    def swipe(self, event):
        """Handle NEXT events by augmenting the default processing by resetting
        the count if we are not currently timing something.

        No other swipe event is possible for this application.
        """
        if not self._started_at:
            self._reset()
        return True     # Request system default handling

    def press(self, button, state):
        if not state:
            return

        uptime = wasp.watch.rtc.get_uptime_ms()
        uptime //= 10
        self._started_at = uptime - self._count
        self._update()

    def touch(self, event):
        pass

    def tick(self, ticks):
        self._update()

    def _reset(self):
        self._started_at = 0
        self._count = 0
        self._last_count = -1
        self._splits = []
        self._nsplits = 0

    def _draw_splits(self):
        draw = wasp.watch.drawable
        splits = self._splits
        if 0 == len(splits):
            draw.fill(0, 0, 120, 240, 120)
            return
        y = 240 - 6 - (len(splits) * 24)
        
        n = self._nsplits
        for i, s in enumerate(splits):
            centisecs = s
            secs = centisecs // 100
            centisecs %= 100
            minutes = secs // 60
            secs %= 60

            t = '# {}   {:02}:{:02}.{:02}'.format(n, minutes, secs, centisecs)
            n -= 1

            draw.set_font(fonts.sans24)
            draw.set_color(0xe73c)
            w = fonts.width(fonts.sans24, t)
            draw.string(t, 0, y + (i*24), 240)

    def _draw(self):
        """Draw the display from scratch."""
        draw = wasp.watch.drawable
        draw.fill()

        self._last_count = -1
        self._update()
        wasp.system.bar.draw()
        self._draw_splits()

    def _update(self):
        # Before we do anything else let's make sure _count is
        # up to date
        if self._started_at:
            
            uptime = wasp.watch.rtc.get_uptime_ms()
            uptime //= 10
            self._count = uptime - self._started_at
            if self._count > 999*60*100:
                self._reset()

        # Update the statusbar
        wasp.system.bar.update()

        if self._last_count != self._count:
            centisecs = self._count
            secs = centisecs // 100
            centisecs %= 100
            minutes = secs // 60
            secs %= 60

            (yyyy, mm, dd, HH, MM, SS, wday, yday) = wasp.watch.rtc.get_localtime()

            # print(HH, MM, SS)

            hours = 24 - HH
            minutes = 60 - MM
            secs = 60 - SS

            hours = 0
            minutes =

            t1 = '{:02}:{:02}:{:02}'.format(hours, minutes, secs)

            draw = wasp.watch.drawable
            draw.set_font(fonts.sans36)
            draw.set_color(0xFFFF)
            w = fonts.width(fonts.sans36, t1)
            # print(w)
            draw.string(t1, (240-w)//2, 100)
            # draw.string(t1, 180-w, 120-36)
            # draw.fill(0, 0, 120-36, 180-w, 36)

            self._last_count = self._count
