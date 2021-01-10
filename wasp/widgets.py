# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2020 Daniel Thompson

"""Widget library
~~~~~~~~~~~~~~~~~

The widget library allows common fragments of logic and drawing code to be
shared between applications.
"""

import fonts
import icons
import wasp
import watch

from micropython import const

class BatteryMeter:
    """Battery meter widget.

    A simple battery meter with a charging indicator, will draw at the
    top-right of the display.
    """
    def __init__(self):
        self.level = -2

    def draw(self):
        """Draw from meter (from scratch)."""
        self.level = -2
        self.update()

    def update(self):
        """Update the meter.

        The update is lazy and won't redraw unless the level has changed.
        """
        icon = icons.battery
        draw = watch.drawable

        if watch.battery.charging():
            if self.level != -1:
                draw.blit(icon, 239-icon[1]-5, 5,
                             fg=wasp.system.theme('battery'))
                self.level = -1
        else:
            level = watch.battery.level()
            if level == self.level:
                return


            green = level // 3
            if green > 31:
                green = 31
            red = 31-green
            rgb = (red << 11) + (green << 6)

            if self.level < 0 or ((level > 5) ^ (self.level > 5)):
                if level  > 5:
                    draw.blit(icon, 239-icon[1]-5, 5,
                             fg=wasp.system.theme('battery'))
                else:
                    rgb = 0xf800
                    draw.blit(icon, 239-icon[1]-5, 5, fg=0xf800)

            w = icon[1] - 4
            x = 239 - 7 - w
            h = level * 22 // 100
            if 18 - h:
                draw.fill(0, x, 9, w, 22-h)
            if h:
                draw.fill(rgb, x, 9+22-h, w, h)

            self.level = level

class Clock:
    """Small clock widget."""
    def __init__(self, enabled=True):
        self.on_screen = None
        self.enabled = enabled

    def draw(self):
        """Redraw the clock from scratch.

        The container is required to clear the canvas prior to the redraw
        and the clock is only drawn if it is enabled.
        """
        self.on_screen = None
        self.update()

    def update(self):
        """Update the clock widget if needed.

        This is a lazy update that only redraws if the time has changes
        since the last call *and* the clock is enabled.

        :returns: An time tuple if the time has changed since the last call,
                  None otherwise.
        """
        now = wasp.watch.rtc.get_localtime()
        on_screen = self.on_screen

        if on_screen and on_screen == now:
            return None

        if self.enabled and (not on_screen
                or now[4] != on_screen[4] or now[3] != on_screen[3]):
            t1 = '{:02}:{:02}'.format(now[3], now[4])

            draw = wasp.watch.drawable
            draw.set_font(fonts.sans28)
            draw.set_color(wasp.system.theme('status-clock'))
            draw.string(t1, 52, 4, 138)

        self.on_screen = now
        return now

class NotificationBar:
    """Show BT status and if there are pending notifications."""
    def __init__(self, x=0, y=0):
        self._pos = (x, y)

    def draw(self):
        """Redraw the notification widget.

        For this simple widget :py:meth:`~.draw` is simply a synonym for
        :py:meth:`~.update` because we unconditionally update from scratch.
        """
        self.update()

    def update(self):
        """Update the widget.

        This widget does not implement lazy redraw internally since this
        can often be implemented (with less state) by the container.
        """
        draw = watch.drawable
        (x, y) = self._pos

        if wasp.watch.connected():
            draw.blit(icons.bluetooth, x+5, y+5, fg=wasp.system.theme('ble'))
            if wasp.system.notifications:
                draw.blit(icons.alert, x+22+5, y+5,
                        fg=wasp.system.theme('notify-icon'))
            else:
                draw.fill(0, x+22+5, y+5, 30, 32)
        elif wasp.system.notifications:
            draw.blit(icons.alert, x, y,
                      fg=wasp.system.theme('notify-icon'))
            draw.fill(0, x+30, y, 22, 32)
        else:
            draw.fill(0, x, y, 52, 32)

class StatusBar:
    """Combo widget to handle notification, time and battery level."""
    def __init__(self):
        self._clock = Clock()
        self._meter = BatteryMeter()
        self._notif = NotificationBar()

    @property
    def clock(self):
        """True if the clock should be included in the status bar, False
        otherwise.
        """
        return self._clock.enabled

    @clock.setter
    def clock(self, enabled):
        self._clock.enabled = enabled

    def draw(self):
        """Redraw the status bar from scratch."""
        self._clock.draw()
        self._meter.draw()
        self._notif.draw()

    def update(self):
        """Lazily update the status bar.

        :returns: An time tuple if the time has changed since the last call,
                  None otherwise.
        """
        now = self._clock.update()
        if now:
            self._meter.update()
            self._notif.update()
        return now

class ScrollIndicator:
    """Scrolling indicator.

    A pair of arrows that prompted the user to swipe up/down to access
    additional pages of information.
    """
    def __init__(self, x=240-18, y=240-24):
        self._pos = (x, y)
        self.up = True
        self.down = True

    def draw(self):
        """Draw from scrolling indicator.

        For this simple widget :py:meth:`~.draw` is simply a synonym for
        :py:meth:`~.update`.
        """
        self.update()

    def update(self):
        """Update from scrolling indicator."""
        draw = watch.drawable
        color = wasp.system.theme('scroll-indicator')

        if self.up:
            draw.blit(icons.up_arrow, self._pos[0], self._pos[1], fg=color)
        if self.down:
            draw.blit(icons.down_arrow, self._pos[0], self._pos[1]+13, fg=color)

class Button():
    """A button with a text label."""
    def __init__(self, x, y, w, h, label):
        self._im = (x, y, w, h, label)

    def draw(self):
        """Draw the button."""
        draw = wasp.watch.drawable
        im = self._im
        bg = draw.darken(wasp.system.theme('ui'))
        frame = wasp.system.theme('mid')
        txt = wasp.system.theme('bright')

        draw.fill(bg, im[0], im[1], im[2], im[3])
        draw.set_color(txt, bg)
        draw.set_font(fonts.sans24)
        draw.string(im[4], im[0], im[1]+(im[3]//2)-12, width=im[2])

        draw.fill(frame, im[0],im[1],          im[2], 2)
        draw.fill(frame, im[0], im[1]+im[3]-2, im[2], 2)
        draw.fill(frame, im[0],         im[1], 2, im[3])
        draw.fill(frame, im[0]+im[2]-2, im[1], 2, im[3])

    def touch(self, event):
        """Handle touch events."""
        x = event[1]
        y = event[2]

        # Adopt a slightly oversized hit box
        im = self._im
        x1 = im[0] - 10
        x2 = x1 + im[2] + 20
        y1 = im[1] - 10
        y2 = y1 + im[3] + 20

        if x >= x1 and x < x2 and y >= y1 and y < y2:
            return True

        return False

class Checkbox():
    """A simple (labelled) checkbox."""
    def __init__(self, x, y, label=None):
        self._im = (x, y, label)
        self.state = False

    @property
    def label(self):
        return self._im[2]

    def draw(self):
        """Draw the checkbox and label."""
        draw = wasp.watch.drawable
        im = self._im
        if im[2]:
            draw.set_color(wasp.system.theme('bright'))
            draw.set_font(fonts.sans24)
            draw.string(im[2], im[0], im[1]+6)
        self.update()

    def update(self):
        """Draw the checkbox."""
        draw = wasp.watch.drawable
        im = self._im
        if self.state:
            c1 = wasp.system.theme('ui')
            c2 = draw.lighten(c1, wasp.system.theme('contrast'))
            fg = c2
        else:
            c1 = 0
            c2 = 0
            fg = wasp.system.theme('mid')
        # Draw checkbox on the right margin if there is a label, otherwise
        # draw at the natural location
        x = 239 - 32 - 4 if im[2] else im[0]
        draw.blit(icons.checkbox, x, im[1], fg, c1, c2)

    def touch(self, event):
        """Handle touch events."""
        y = event[2]
        im = self._im
        if y >= im[1] and y < im[1]+40:
            self.state = not self.state
            self.update()
            return True
        return False

_SLIDER_KNOB_DIAMETER = const(40)
_SLIDER_KNOB_RADIUS = const(_SLIDER_KNOB_DIAMETER // 2)
_SLIDER_WIDTH = const(220)
_SLIDER_TRACK = const(_SLIDER_WIDTH - _SLIDER_KNOB_DIAMETER)
_SLIDER_TRACK_HEIGHT = const(8)
_SLIDER_TRACK_Y1 = const(_SLIDER_KNOB_RADIUS - (_SLIDER_TRACK_HEIGHT // 2))
_SLIDER_TRACK_Y2 = const(_SLIDER_TRACK_Y1 + _SLIDER_TRACK_HEIGHT)

class Slider():
    """A slider to select values."""
    def __init__(self, steps, x=10, y=90, color=None):
        self.value = 0
        self._steps = steps
        self._stepsize = _SLIDER_TRACK / (steps-1)
        self._x = x
        self._y = y
        self._color = color
        self._lowlight = None

    def draw(self):
        """Draw the slider."""
        draw = watch.drawable
        x = self._x
        y = self._y
        color = self._color
        if self._color is None:
            self._color = wasp.system.theme('ui')
            color = self._color
        if self._lowlight is None:
            self._lowlight = draw.lighten(color, wasp.system.theme('contrast'))
        light = self._lowlight

        knob_x = x + ((_SLIDER_TRACK * self.value) // (self._steps-1))
        draw.blit(icons.knob, knob_x, y, color)

        w = knob_x - x
        if w > 0:
            draw.fill(0, x, y, w, _SLIDER_TRACK_Y1)
            if w > _SLIDER_KNOB_RADIUS:
                draw.fill(0, x, y+_SLIDER_TRACK_Y1,
                          _SLIDER_KNOB_RADIUS, _SLIDER_TRACK_HEIGHT)
                draw.fill(color, x+_SLIDER_KNOB_RADIUS, y+_SLIDER_TRACK_Y1,
                          w-_SLIDER_KNOB_RADIUS, _SLIDER_TRACK_HEIGHT)
            else:
                draw.fill(0, x, y+_SLIDER_TRACK_Y1, w, _SLIDER_TRACK_HEIGHT)
            draw.fill(0, x, y+_SLIDER_TRACK_Y2, w, _SLIDER_TRACK_Y1)

        sx = knob_x + _SLIDER_KNOB_DIAMETER
        w = _SLIDER_WIDTH - _SLIDER_KNOB_DIAMETER - w
        if w > 0:
            draw.fill(0, sx, y, w, _SLIDER_TRACK_Y1)
            if w > _SLIDER_KNOB_RADIUS:
                draw.fill(0, sx+w-_SLIDER_KNOB_RADIUS, y+_SLIDER_TRACK_Y1,
                          _SLIDER_KNOB_RADIUS, _SLIDER_TRACK_HEIGHT)
                draw.fill(light, sx, y+_SLIDER_TRACK_Y1,
                          w-_SLIDER_KNOB_RADIUS, _SLIDER_TRACK_HEIGHT)
            else:
                draw.fill(0, sx, y+_SLIDER_TRACK_Y1, w, _SLIDER_TRACK_HEIGHT)
            draw.fill(0, sx, y+_SLIDER_TRACK_Y2, w, _SLIDER_TRACK_Y1)

    def update(self):
        self.draw()

    def touch(self, event):
        tx = event[1]
        threshold = self._x + 20 - (self._stepsize / 2)
        v = int((tx - threshold) / self._stepsize)
        if v < 0:
            v = 0
        elif v >= self._steps:
            v = self._steps - 1
        self.value = v

class Spinner():
    """A simple Spinner widget.

    In order to have large enough hit boxes the spinner is a fairly large
    widget and requires 60x120 px.
    """
    def __init__(self, x, y, mn, mx, field=1):
        self._im = (x, y, mn, mx, field)
        self.value = mn

    def draw(self):
        """Draw the slider."""
        draw = watch.drawable
        im = self._im
        fg = draw.lighten(wasp.system.theme('ui'), wasp.system.theme('contrast'))
        draw.blit(icons.up_arrow, im[0]+30-8, im[1]+20, fg)
        draw.blit(icons.down_arrow, im[0]+30-8, im[1]+120-20-9, fg)
        self.update()

    def update(self):
        """Update the spinner value."""
        draw = watch.drawable
        im = self._im
        draw.set_color(wasp.system.theme('bright'))
        draw.set_font(fonts.sans28)
        s = str(self.value)
        if len(s) < im[4]:
            s = '0' * (im[4] - len(s)) + s
        draw.string(s, im[0], im[1]+60-14, width=60)

    def touch(self, event):
        x = event[1]
        y = event[2]
        im = self._im
        if x >= im[0] and x < im[0]+60 and y >= im[1] and y < im[1]+120:
            if y < im[1] + 60:
                self.value += 1
                if self.value > im[3]:
                    self.value = im[2]
            else:
                self.value -= 1
                if self.value < im[2]:
                    self.value = im[3] - 1

            self.update()
            return True

        return False

class ConfirmationView:
    """Confirmation widget allowing user confirmation of a setting."""

    def __init__(self):
        self.active = False
        self.value = False
        self._yes = Button(20, 140, 90, 45, 'Yes')
        self._no = Button(130, 140, 90, 45, 'No')

    def draw(self, message):
        draw = wasp.watch.drawable
        mute = wasp.watch.display.mute

        mute(True)
        draw.set_color(wasp.system.theme('bright'))
        draw.set_font(fonts.sans24)
        draw.fill()
        draw.string(message, 0, 60)
        self._yes.draw()
        self._no.draw()
        mute(False)

        self.active = True

    def touch(self, event):
        if not self.active:
            return False

        if self._yes.touch(event):
            self.active = False
            self.value = True
            return True
        elif self._no.touch(event):
            self.active = False
            self.value = False
            return True

        return False

class Card:
    def __init__(self, icon, title, state):
        self.icon = icon
        self.title = title
        self.state = state
        self.is_last = True
        self.is_first = True
        pass

    def draw(self, all=True):
        draw = wasp.watch.drawable

        if all:
            if not self.is_first:
                draw.fill(0xffff, 30, 0, 180, 5)
            if not self.is_last:
                draw.fill(0xffff, 30, 235, 180, 5)

        x = 20
        y = 20

        if all:
            draw.fill(0xffff, x, y, 200, 200)


        draw.set_color(0xffff, 0xffff)
        if self.icon:
            draw.blit(self.icon, x+10, y+10)

    
        
        if all and self.title:
            draw.set_color(0x0000, 0xffff)
            draw.set_font(fonts.sans24)
            chunks = draw.wrap(self.title, 160)
            for i in range(len(chunks)-1): # TODO: Max 2
                sub = self.title[chunks[i]:chunks[i+1]].rstrip()
                draw.string(sub, x+20, (y+100) + ((24+4) * i))

        # draw.string(self.title, x+20, y+100) # w=160
        # draw.string(self.title, x+20, y+124) # w=160
        
        draw.set_color(wasp.system.theme('mid'), 0xffff)
        draw.string(self.state, x+20, y+148+12) # w=160
        pass

    def touch(self, event):
        if self.state == "On":
            self.state = "Off"
            self.on_icon = self.icon
            self.icon = light_off_50
        else:
            self.state = "On"
            self.icon = self.on_icon
        self.draw(all=False)
        return True


# 2-bit RLE, generated from res/light_off.png, 1564 bytes
light_off = (
    b'\x02'
    b'PP'
    b'\xff\xff\xc6\xc1\xc1@\xfbABA\xc1\xc1\xff\x05\xc1A'
    b'\x80\xeb\x81\xc0V\xc1@\xfdA\x80\xfc\x81\x01\x02\x01\x81'
    b'A\xc1\xc0\xeb\xc1@\xfbA\x80\xd7\x81\xbe\x81\xc0\xac\xc1'
    b'@VA\x80\xfc\x81\x01\x04\x02\x04\x01\x81A\xc1\xc0\xd7'
    b'\xc1\xfb@\xfbA\x80\xff\x81\x01\x02\xc0\xfc\xc1@\xfeA'
    b'\x80\xdb\x81\xc0\xeb\xc1@\xacA\x80\xfb\x82A\xc1\xc0\xdb'
    b'\xc1@\xfeA\x80\xfc\x81\x02\x01\xc0\xff\xc1@\xfbA\x80'
    b'\xd7\xb8\x81\xc0\x81\xc1@\xfcA\x02\x80\xfd\x81\xc1\xc0\xfb'
    b'\xc1@\xd7J\xc1\x80\x81\x81\xc0\xfd\xc1\x02@\xfcA\x81'
    b'\x80\xd7\x81\xb5\x81\xc0V\xc1\x01\x01A@\xebA\x81\x89'
    b'\x81\x81\x81\x82\x81A\x80\xfc\x81\x01\x01\xc1\xc0\xd7\xc1\xf3'
    b'\xc1@\xffA\x01\x01A\x80\xfb\x81\xc7\xc5\xc6\x81A\x01'
    b'\x01A\xc1\xf1\xc1\xc0V\xc1\x01\x01@\xdbA\x80\xd7\x81'
    b'\x85\x83\x8c\x81A\x01\x01\xc1\x81\xaf\x81A\x01\x01A\x86'
    b'\x81\x91A\x01\x01\xc0\x81\xc1\x81\xae@\xacA\x01\x01\x80'
    b'V\x81\xc0\xd7\xc5\xc1\xd4\x81\x01\x01A\xed\xc1@+A'
    b'\x01\x80\xfd\x81\xc1\xc4\xc1\xd5\xc1\x81\x01\x81\xc1\xec\xc0\x81'
    b'\xc1\x01\x01@\xacA\x80\xd7\x84\x81\x97A\x01\x01\xc1\xab'
    b'\x81\xc0+\xc1\x01@VA\x84\x81\x99A\x01\xc1\x81\xaa'
    b'\x80\xeb\x81\x01\x01\xc0\xac\xc1@\xd7CAZ\xc1\x01\x01'
    b'\xc1iA\x80V\x81\x01\xc0\xfe\xc1CA[A\xc1\x01'
    b'\x81AhA@\xfcA\x01\x80\x81\x81\xc0\xd7\xc2\xc1\xdd'
    b'\x81\x01A\xc1\xe8@\xfbA\x01\x01\x80\xac\x81\xc2\xc1\xdd'
    b'\x81\x01\x01A\xe8\xc0\xeb\xc1\x01@\xfcA\x80\xd7\x81\x81'
    b'\x81\x9e\xc0\xfb\xc1A\x01@\xebA\xa8\x80\x81\x81\x01\xc0'
    b'+\xc1@\xd7AAA^A\xc1\x01\x81h\x80\xdb\x81'
    b'\x01\xc0\xfe\xc1b@\xfdA\x01\x81\x80\xd7\xa8\xc0\xdb\xc1'
    b'\x01@\xfeA\xa2A\x01\xc1\xa8\xc1\x01\x80\xfd\x81\xc0\xd7'
    b'\xe2\x81\x01@\xdbA\xe8\x80\x81\x81\x01\xc0\xfc\xc1@\xd7'
    b'A`A\xc1\x01\x80\xeb\x81h\xc0\xac\xc1\x01\x01@\xfb'
    b'A\x80\xd7\xa0\xc1\x01\x01\xc1\xa8\x81\xc0\xfc\xc1\x01@\x81'
    b'A\xa0\x80\xdb\x81\x01\xc1\xc0\xd7\xc1\xe8\xc1@\xffA\x01'
    b'\x80\xfe\x81\xc1\xde\xc1\xc0\xfc\xc1\x01@\xdbA\x80\xd7\xaa'
    b'\xc0\xeb\xc1\x01\x01@\xacA\x9e\x80\x81\x81\x01\x01\xc0\xfb'
    b'\xc1@\xd7jA\x80+\x81\x01\xc0\xff\xc1]A\x81\x01'
    b'\xc1Ak@\xebA\x01\x01\x80\xac\x81\xc0\xd7\xdcA\x01'
    b'\x01\x81\xec\xc1@\xfdA\x01A\xc1\xda\xc1\x80+\x81\x01'
    b'\xc0\xff\xc1@\xd7Am\x80\xac\x81\x01\x01\xc0\x81\xc1Z'
    b'@\xebA\x01\x01\x81\x80\xd7\xae\x81\xc0V\xc1\x01@\xfc'
    b'A\x80\xfb\x81\xc0\xd7\xc5\xc1\xc1\xc4\xc2\xc4\xc1\xc1\xc5\xc1'
    b'@\xfeA\x01A\xc1\xef\x81\x80\xfc\x81\x01\xc0\xdb\xc1@'
    b'\xd7D\x80\x81\x81\xc0\xfc\xc1\xc1\xc4\xc2\xc4\xc1\xc1\x81D'
    b'@\xacA\x01\x01\x80\xeb\x81\xc0\xd7\xf1@\x81A\x01\x80'
    b'\xfc\x81\xc1\xc3\xc0\xff\xc1\x0e\xc1@\xd7D\x80\xdb\x81\x01'
    b'\xc0\xfc\xc1Aq@\xfbA\x01\x01\x80\xac\x81\xc0\xd7\xc3'
    b'A@\xebACA\x80\x81\x81\x01\x01\x81ACA\xc0'
    b'\xfb\xc1@\xd7CA\x80\xfd\x81\x01\xc0V\xc1rA\x81'
    b'\x01@\xdbA\x80\xd7\x89\xc0\xfb\xc1\x01\x01\xc1\x89\xc1\x01'
    b'\x01@\xacA\xb3\x80\xdb\x81\x01\xc0+\xc1@\xd7AH'
    b'\x80\xfb\x81\x01\x01\x81I\xc0\x81\xc1\x01@\xfcA\x80\xd7'
    b'\x81\xb3\xc0\xac\xc1\x01\x01@\xfbA\x88A\x01\x01A\x89'
    b'\x80\xfe\x81\x01\xc0V\xc1@\xd7AsA\x80\xfc\x81\x01'
    b'\xc0\x81\xc1H@\xfbA\x01\x01A\x80\xd7\x88A\x01\x01'
    b'\xc0\xeb\xc1\xb4\x81@\xffA\x01A\x88\x80\xfb\x81\x01\x01'
    b'\x81\xc0\xd7\xc8@\xebA\x01\x80\xfc\x81\xc0\xfb\xc1@\xd7'
    b'u\x80\x81\x81\x01\xc0\xfc\xc1AG@\xfbA\x01\x01A'
    b'\x80\xd7\x88\xc0\xff\xc1\x01\xc1\x81\xb5A\x01\x01@\xacA'
    b'\x87\x80\xfb\x81\x01\x01\x81\xc0\xd7\xc7\x81@\xfcA\x01\x80'
    b'\x81\x81\xf6\xc1A\x01\x81\xc7\xc0\xfb\xc1\x01\x01\xc1@\xd7'
    b'G\x80\xeb\x81\x01\x01\xc1w\xc0V\xc1\x01@\xfeA\x80'
    b'\xd7\x87\xc0\xfb\xc1\x01\x01\xc1\x87@VA\x01\x80\xfd\x81'
    b'\xc0\xd7\xc1\xf7@\xebA\x01\x80\xfc\x81\xc0\xfb\xc1@\xd7'
    b'F\xc1\x01\x01\xc1FA\x81\x01\x80\x81\x81x\xc1\x01\x01'
    b'\x81\xc0\xac\xc6@\xebA\x01\x01A\xc6\x81\x01\x01\xc1\x80'
    b'\xd7\xb8\x81\xc0+\xc1\x14\xc1\x81\xb9@\x81A\x01\x05\x01'
    b'\x01\x03\x08\x01A\xba\x81\x80\xfb\x81\x81\x81\x81\x81\x81\x81'
    b'\xc0\xac\xc1\x81\x89\x81\x81@\xd7A|A\x81\x80\xeb\x81'
    b'\xc0\xdb\xc1@\xfeA\x80\xfc\x81\x01\xc1\xc0\xd7\xc9\xc1\xfc'
    b'\xc1@\xdbA\x81\x01\x01\x03\x01A\xc4\xc1\xc1\x80\xac\x81'
    b'\xc0\x81\xc1@VA\x80\xfd\x81A\xc0\xd7\xc1\xfa\xc1@'
    b'\xfcA\x01\x01A\x81\x80V\x81\xc0\xeb\xc1@\xfbA\x80'
    b'\xd7\x81\x81A\xc1\xc0\xdb\xc1@\xfeA\x80\xfc\x81\x01\x03'
    b'\x81\xc0\xd7\xc1\xfb@\xacA\x80\x81\x81A\xc1\xc1\xc1A'
    b'\x81\xc0\xff\xc1@\xfcA\x01\x01\x02\x01\x01A\xc1\x81\x80'
    b'\xac\x81\xc0\xd7\xfc\xc1@\xfbA\x80\xeb\x81\xc0\xdb\xc1@'
    b'\xfdA\x80\xfc\x81\x01\x03\x01\x81\xc0\xfe\xc1@\xdbA\x80'
    b'\xeb\x81\xc0\xfb\xc1@\xd7B\xc1A{A\x80\xfe\x81\x01'
    b'\x01\x02\x01\x01\xc0+\xc1@VA\x80\x81\x81\xc0\xac\xc1'
    b'@\xd7AA\x80\xfb\x81\xc1\xc0\x81\xc1@\xffA\x80\xfc'
    b'\x81\x01\xc0\xfd\xc1@\xd7AzA\x80+\x81\x01\xc0\xfc'
    b'\xc1@\xfeA\x80\xdb\x81\xc0\xeb\xc1@\xfbA\x80\xd7\x81'
    b'\x81\x82\xc1\xc0+\xc1\x01\x01\x03\x01@\xfdA\x81\xbb\x80'
    b'\xfb\x81\x81\xc0\xd7\xc1\xc1\xc6\xc1@VA\x01\x01\x01\x80'
    b'+\x81A\xc0\x81\xc1@\xacA\x80\xd7\x81\xbf\x01\x87\xc0'
    b'\xfb\xc1@\xebA\x80\xac\x81\xc0\xd7\xc1\xc1\xc1\xfe\xc1@'
    b'\x81A\x80\xff\x8a\xc0V\xc1\xc1\xc1\xc1\x81\x83A@\xd7'
    b'Az\x80\xfb\x81\x01\x12\x01\x81zA\xc0\xfc\xc1\x01@'
    b'\xdbA\x80\x81\x81\x8c\x81A\x01\xc1\xc0\xd7\xc1\xfb@V'
    b'A\x01A\x80\xfb\x81\xc0\xac\xc1\xca\xc1\x81A\x01A@'
    b'\xd7A{\x81\x01\x01\x80\xdb\x81\xc1\xc1\xc8\xc1\xc1\x81\x01'
    b'\x01\xc0\xfb\xc1}@\xebA\x01\x01\x80\xfe\x81A\xc0\xac'
    b'\xc1\xc1\xc1\xc2\xc1\xc1\xc1A\x81\x01\x01A@\xd7~A'
    b'\x80\xeb\x81\xc0\xfc\xc1\x01\x01@\xfeA\x80\xdb\x81\xc0\x81'
    b'\xc1@\xebB\xc1\x81\x80\xfe\x81\x01\x01\xc0\xfc\xc1A@'
    b'\xd7A\x7f\x01\x80\xfb\x81\xc0\xdb\xc1@\xfcA\x01\x06\x01'
    b'A\xc1\x81\x80\xd7\xbf\x04\x81\xc0\xfb\xc1@\xebA\x80\xdb'
    b'\x81\xc0\xfe\xc1@\xfdAA\xc1\x81\x80\xeb\x81\xc0\xfb\xc1'
    b'@\xd7A\x7f\tD\x7f\xff\xc8'
)

# 2-bit RLE, generated from res/light_off_50.png, 1505 bytes
light_off_50 = (
    b'\x02'
    b'PP'
    b'\xff\xff\xc7\xc1@\xacA\x80\x81\x81\x81A\xc1\xff\x07\xc1'
    b'A\xc0\xeb\xc1\x81\x81@\xdbABA\x81\x81\xc1\x80\xac'
    b'\x81\xc0\xd7\xc1\xff\x01@\xfbA\x80\xeb\x81\xc0\x81\xc1@'
    b'\xdbDAAAAD\xc1\x81\x80\xfb\x81\xc0\xd7\xfc\x81'
    b'@\xebA\x80\xdb\x81\x82\x81A\xc0\xac\xc1@\xfbAA'
    b'BAA\xc1\x80\xeb\x81\xc0\xdb\xc1\xc2\xc1\x81A@\xd7'
    b'y\x80\xac\x81\xc0\x81\xc1@\xdbB\xc1\x81\x80\xd7\x81\x8a'
    b'\x81\xc0\xac\xc1@\x81A\x80\xdb\x82A\xc1\xc0\xd7\xf6\xc1'
    b'@\xebA\x82\x80\x81\x81\xc0\xac\xc1@\xd7ANA\xc1'
    b'\x81\x80\xdb\x82\xc0\xeb\xc1AsA\xc1\x82\xc1ARA'
    b'\xc1\x82\xc1AqA\xc1\x82@\xacA\x80\xd7\x95\x81A'
    b'\xc0\xdb\xc2@\xebA\x81\xb0\x80\xac\x81\xc2\x81\xc0\xd7\xd8'
    b'\x81@\xdbB\x81\xef\x80\xfb\x81AA\xc0\xeb\xc1@\xd7'
    b'Z\xc1\x80\xdb\x81\x81\xc0\xfb\xc1mA@\x81A\x81A'
    b'\x80\xd7\x81\x9a\x81A\xc0\xdb\xc1A\x81\xac@\xacA\xc1'
    b'\xc1\x80\xfb\x81\xc0\xd7\xdc\x81@\xdbAA\x80\xac\x81\xeb'
    b'\xc1\xc0\x81\xc1A@\xebA\x80\xd7\x9eA\xc0\xdb\xc1@'
    b'\x81A\x81\xaa\x80\xfb\x81\xc1\xc1\x81\xc0\xd7\xde\x81@\xdb'
    b'AA\x81\xea\x80\xeb\x81A\xc0\x81\xc1@\xd7`\xc1\x80'
    b'\xdb\x81\xc0\xeb\xc1iA@\x81A\x81\x80\xac\x81\xc0\xd7'
    b'\xe0\x81@\xdbA\x80\x81\x81\xc1\xe8\xc0\xfb\xc1AA\xc1'
    b'@\xd7`\xc1\x80\xdb\x81\x81\xc1h\xc1\x81\xc0\x81\xc1A'
    b'`A\xc1\x81@\xfbA\x80\xd7\xa8\xc0\xac\xc1@\xdbA'
    b'\x80\x81\x81\xc0\xd7\xe1\xc1\x81A@\xacA\xe8\x80\xeb\x81'
    b'\xc0\xdb\xc1@\x81A\x80\xd7\xa2A\xc1\xc0\xeb\xc1\xa8A'
    b'@\xdbA\xc1\xa2\x80\x81\x81A\x81\xc0\xd7\xe8@\xebA'
    b'\x80\xdb\x81\xc0\x81\xc1@\xd7b\xc1\x81\x80\xeb\x81h\xc0'
    b'\xac\xc1@\xdbA\x80\x81\x81\xc0\xd7\xc1\xe0\xc1\x81A@'
    b'\xacA\xe8\x80\xfb\x81\xc0\xdb\xc1\xc1\x81@\xd7`\x81\xc1'
    b'\xc1\x81hA\x80\x81\x81\xc1\xc0\xac\xc1`\xc1@\xdbA'
    b'\x81\x80\xd7\x81\xa9\xc0\xeb\xc1A@\x81A\x9f\x81A\x80'
    b'\xdb\x81\xc1\xc0\xd7\xea@\xfbA\x81\x81A\xde\x80\xac\x81'
    b'\xc0\xdb\xc1\xc1A@\xd7jA\x80\x81\x81\xc1\xc0\xeb\xc1'
    b']A\x81@\xdbA\xc1\x80\xd7\xac\xc0\xac\xc1AA@'
    b'\xfbA\x9c\xc1\x80\xdb\x81\x81A\xc0\xd7\xec\xc1@\x81A'
    b'\x81A\xc1\xda\xc1A\x81\x80\xeb\x81\xee\xc0\xfb\xc1@\xdb'
    b'AA\x80\xac\x81\xc0\xd7\xda\x81AA@\xfbA\xef\x80'
    b'\xeb\x81\xc0\xdb\xc1@\x81A\x80\xd7\x81\x85\x81\x81\x84\x82'
    b'\x84\x81\x81\x85\x81A\xc1\xc0\xeb\xc1\xb0@\xfbA\x80\x81'
    b'\x81\xc0\xdb\xc1@\xebA\x80\xd7\x84\xc0\xac\xc1@\x81A'
    b'ADBDAA\xc1\x84\x80\xfb\x81\xc0\xdb\xc1\xc1\x81'
    b'@\xd7q\x80\xac\x81\xc1\xc0\x81\xc1AC@\xebA\x80'
    b'\xdb\x8eA\xc0\xd7\xc4@\xacA\x81\x80\x81\x81\xc1\xf1\xc0'
    b'\xfb\xc1@\xdbAA\xc1\x80\xd7\x83\x81\xc1\xc3\xc1\xc0\xac'
    b'\xc1AA\xc1@\xfbACA\x81\x83\x81\x80\x81\x81\xc0'
    b'\xdb\xc1@\xebA\x80\xd7\xb3\xc0\x81\xc1@\xdbA\x80\xeb'
    b'\x81\xc0\xd7\xc9@\xfbA\x80\xdb\x81\x81A\xc9A\x81\x81'
    b'A\xf3\xc0\xac\xc1\x81@\x81A\x80\xd7\x81\x88\xc0\xfb\xc1'
    b'@\xdbAA\xc1\x89\x80\xac\x81A\xc0\x81\xc1@\xd7A'
    b's\x80\xfb\x81\xc0\xdb\xc1\xc1\x81H\x81\xc1\xc1\x81I@'
    b'\xebA\xc1A\x80\xd7\xb4\x81\xc0\x81\xc1@\xdbA\x80\xac'
    b'\x81\xc0\xd7\xc8@\xfbA\x80\xdb\x81\x81A\xc8\xc1\x81\x81'
    b'\xc0\xac\xc1@\xd7u\x80\xeb\x81\xc0\xdb\xc1\x81H@\xfb'
    b'A\xc1\xc1A\x80\xd7\x88\xc0\xac\xc1@\xdbA\x80\x81\x81'
    b'\xc0\xd7\xc1\xf5@\xacA\x80\xdb\x81\xc0\x81\xc1@\xd7A'
    b'G\x80\xfb\x81\xc0\xdb\xc1\xc1\x81H@\xebA\xc1A\x80'
    b'\xd7\xb6\xc0\xfb\xc1@\xdbAA\xc1\x87\xc1AA\xc1\x87'
    b'\x81\x80\x81\x81A\xc0\xac\xc1@\xd7vA\x81\x80\xdb\x81'
    b'\xc1G\xc0\xfb\xc1\x81\x81\xc1G\xc1\x81\x81\xc1w@\xeb'
    b'A\x81A\x80\xd7\x87\xc1\xc0\xdb\xc1\xc1@\xfbA\x87\x80'
    b'\xeb\x81\xc1\xc0\x81\xc1@\xd7x\x80\xac\x81\xc0\xdb\xc1@'
    b'\x81A\x80\xd7\x81\x86\xc0\xfb\xc1@\xdbAA\xc1\x86\x81'
    b'\x80\x81\x81A\xc0\xac\xc1@\xd7x\x80\xfb\x81\xc0\xdb\xc1'
    b'\xc1@\xacA\x86A\xc1\xc1A\x86A\xc1\xc1\x81\x80\xd7'
    b'\xb8\x81\xc0\x81\xc1@\xdbT\xc1\x81\xb9\x80\xac\x81AE'
    b'AAKA\x81\xc0\xd7\xfb\xc2\xc1\xc1\xc1\xc1@\xfbA'
    b'AA\xca\xc1\xfd\xc1AA\x81\x80\xeb\x81\xc0\x81\xc1@'
    b'\xdbA\x80\xac\x81\xc0\xd7\xff\x07\xc1\x81@\x81A\x80\xdb'
    b'\x81\x85\xc0\xac\xc1@\xd7EA\x80\xfb\x81\xc1\xc0\xeb\xc1'
    b'@\x81A\xc1\x80\xd7\x81\xba\x81A\xc0\xdb\xc2AA@'
    b'\xebA\x80\xac\x81\xc0\xfb\xc1@\xd7AA\xc1\xc1\x81\x80'
    b'\x81\x81\x81\xc0\xdb\xc1\xc3\x81A{@\xfbA\x80\xac\x81'
    b'A\xc0\xd7\xc1\xc1\xc1A\x81@\xebA\x80\x81\x81\xc0\xdb'
    b'\xc1\xc4\xc1\x81A@\xacA\x80\xfb\x81\xc0\xd7\xfd\x81A'
    b'@\xebA\x80\x81\x81\x81\xc0\xdb\xc5\x81\x81A@\xfbA'
    b'A\x80\xd7\x82\x81\x81\xbb\x81\xc0\xeb\xc1@\xdbADA'
    b'\x80\x81\x81\xc1\xc0\xac\xc1@\xfbA\x80\xd7\x81\x81\x81A'
    b'\xc1\xc0\xeb\xc1@\x81A\x80\xdb\x81A\xc0\xd7\xc1\xfa\xc1'
    b'A\x81A@\xebA\x80\xac\x81\xc0\xfb\xc1\xc1@\xd7A'
    b'C\x81\x80\x81\x81\xc0\xdb\xc1\xc5\x81A{A@\xfbA'
    b'\x80\xd7\x81\x88\xc0\xeb\xc1@\xdbBA\x80\x81\x81\xc1\xc0'
    b'\xac\xc1@\xfbA\x80\xd7\x81\xbf\x08\x81\xc1A\x81\xbf\x01'
    b'\x81\xc1\xc0\xeb\xca\xc1\xc1\xc1\xc1\xc1\xc3@\xacA\x81\xba'
    b'\x81\x80\xdb\x81\x92\x81\xc0\xd7\xc1\xfa\xc1@\x81A\x81\x80'
    b'\xac\x81\x81\x8c\x81\x81\xc0\xdb\xc1A@\xd7A{\x80\xeb'
    b'\x81\xc1\x81\xc0\xfb\xc1\xc1\xca\xc1\xc1\x81@\xdbA\x81\x80'
    b'\xd7\xbc\xc1AA\xc0\xeb\xc1@\xfbAAHAA\xc1'
    b'\x80\xdb\x81\x81A\xc0\xd7\xfd@\xacA\x81\x81\x80\xeb\x81'
    b'\xc0\xfb\xc1\xc1\xc1\xc1\xc2\xc1\xc1\xc1\xc1\x81@\xdbAA'
    b'\x80\xac\x81\xc0\xd7\xff\x00@\xfbA\x80\x81\x81\xc0\xdb\xc1'
    b'\xc1\x81@\xacAABAA\x81\xc1\xc1\x81\x80\xfb\x81'
    b'\xc0\xd7\xff\x02\xc1@\xebA\x80\x81\x81\xc0\xdb\xc3\xc2\xc3'
    b'\x81A@\xfbA\x80\xd7\xbf\x05\x81\xc0\xac\xc1@\xebA'
    b'A\x80\x81\x82AA\xc1\xc0\xd7\xc1\xff\xff\xff\x16'
)



class NomieCard:
    def __init__(self, icon, title, state):
        self.icon = icon
        self.title = title
        self.state = state
        self.is_last = True
        self.is_first = True
        pass

    def draw(self, all=True):
        draw = wasp.watch.drawable

        if all:
            if not self.is_first:
                draw.fill(0xffff, 30, 0, 180, 5)
            if not self.is_last:
                draw.fill(0xffff, 30, 235, 180, 5)

        x = 20
        y = 20

        if all:
            draw.fill(0xffff, x, y, 200, 200)


        draw.set_color(0xffff, 0xffff)
        if self.icon:
            draw.blit(self.icon, x+60, y+60)

    
        
        if all and self.title:
            draw.set_color(0x0000, 0xffff)
            draw.set_font(fonts.sans24)
            draw.string(self.title, x+20, y+160, 160)
            # chunks = draw.wrap(self.title, 160)
            # for i in range(len(chunks)-1): # TODO: Max 2
            #     sub = self.title[chunks[i]:chunks[i+1]].rstrip()
            #     draw.string(sub, x+20, (y+100) + ((24+4) * i))

        
        draw.fill(0x0f00, x+10, y+10, 40, 40)

        draw.set_color(0x0000, 0xf00)
        draw.string(self.state, x+10, y+20, 40) 
        pass

    def touch(self, event):
        return True
        # if self.state == "On":
        #     self.state = "Off"
        #     self.on_icon = self.icon
        #     self.icon = light_off_50
        # else:
        #     self.state = "On"
        #     self.icon = self.on_icon
        # self.draw(all=False)
        # return True
