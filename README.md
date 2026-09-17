# PySide6 Countdown Timer

## Message behavior

The timer now has a **configurable Default Message** plus configurable
threshold messages.

Example:

- Timer starts at **30:00**
- Custom message threshold is **05:00**

Behavior:

```text
30:00 ─────────────── 05:01
       DEFAULT MESSAGE

05:00 ─────────────── 00:00
       CUSTOM MESSAGE
```

So the rule is:

```python
time_left > 5 minutes
    -> Default Message

time_left <= 5 minutes
    -> 5-minute Custom Message
```

If additional thresholds are configured:

```text
30:00 - 05:01  -> Default
05:00 - 03:01  -> 5-minute custom
03:00 - 02:01  -> 3-minute custom
02:00 - 00:01  -> 2-minute custom
00:00           -> Time's Up custom
```

The **default message itself can be edited**, including its text and color.
Custom messages can also be added, edited, deleted, and assigned their own
colors and optional beep durations.

## Run

```bash
pip install -r requirements.txt
python countdown_timer.py
```
