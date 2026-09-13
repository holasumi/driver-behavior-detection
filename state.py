"""Calibrated, time-based rules; rules.json is also consumed by the web UI.

EAR measures closure, not fatigue ground truth. Missing/implausible eye
measurements are unknown and never counted as open eyes.
"""
import json
import math
import statistics
import time
from pathlib import Path

RULES = json.loads((Path(__file__).parent / 'web/dist/rules.json').read_text())

def angle(value):
    return (value + 180) % 360 - 180

class DriverState:
    def __init__(self, eyes_obscured=False):
        self.rules = RULES
        self.eyes_obscured = eyes_obscured
        self.samples = []
        self.baseline = None
        self.last = None
        self.previous_closed = None
        self.history = []
        self.started = {}
        self.active = set()
        self.closed = False
        self.perclos = None

    def update(self, metrics, now=None):
        now = time.monotonic() if now is None else now
        if not math.isfinite(now):
            raise ValueError('Timestamp must be finite')
        r = self.rules
        dt = 0 if self.last is None else now - self.last
        if dt < 0:
            raise ValueError('Timestamp must be monotonic')
        gap = dt > r['max_gap']
        self.last = now
        self.history = [(max(a, now-r['perclos_window']), b, c)
                        for a,b,c in self.history if b > now-r['perclos_window']]
        if gap:
            self.closed = False
            self.started.clear()
            self.active.clear()
            self.previous_closed = None
            if not self.baseline:
                self.samples.clear()
        m = vars(metrics) if metrics is not None and not isinstance(metrics, dict) else metrics
        valid = m is not None and all(math.isfinite(m.get(k, float('nan'))) for k in ('ear','mar','yaw','pitch','roll'))
        if valid:
            valid = m.get('face_valid', True)
        if not valid:
            self.started.clear()
            self.active.clear()
            self.previous_closed = None
            self.closed = False
            if not self.baseline:
                self.samples.clear()
            return self._result('no_face', [], False, 0, None)

        left = m.get('left_ear', m['ear'])
        right = m.get('right_ear', m['ear'])
        eye_valid = (not self.eyes_obscured and m.get('eyes_valid', True)
                     and 0.02 <= left <= 0.6 and 0.02 <= right <= 0.6
                     and abs(left-right) < 0.12)
        eye = max(left, right)  # both eyes must close; a wink is not sleep
        if self.baseline is None:
            usable = abs(m['roll']) < 15 and (self.eyes_obscured or (eye_valid and eye > 0.14 and m['mar'] < 0.35))
            if not usable:
                self.samples.clear()
                return self._result('calibration', [], eye_valid, 0, None)
            if self.samples and (abs(angle(m['yaw']-self.samples[0][1]['yaw'])) > 8 or abs(angle(m['pitch']-self.samples[0][1]['pitch'])) > 8):
                self.samples.clear()
            self.samples.append((now, dict(m, eye=eye)))
            progress = min(1, (now-self.samples[0][0])/r['calibration_seconds'], len(self.samples)/r['calibration_samples'])
            if progress < 1:
                return self._result('calibration', [], eye_valid, progress, None)
            self.baseline = {k: statistics.median(s[k] for _,s in self.samples) for k in ('eye','mar','yaw','pitch')}
            self.samples.clear()
            self.previous_closed = None

        yaw = angle(m['yaw']-self.baseline['yaw'])
        pitch = angle(m['pitch']-self.baseline['pitch'])
        eye_valid = eye_valid and abs(yaw) < 35 and abs(pitch) < 30 and abs(m['roll']) < 25
        if eye_valid:
            threshold = self.baseline['eye'] * r['eye_release_ratio' if self.closed else 'eye_ratio']
            self.closed = eye < threshold
        else:
            self.closed = False
        if eye_valid and self.previous_closed is not None and 0 < dt <= r['max_gap']:
            self.history.append((now-dt, now, self.previous_closed))
        self.previous_closed = self.closed if eye_valid else None
        observed = sum(b-a for a,b,_ in self.history)
        self.perclos = sum(b-a for a,b,c in self.history if c)/observed if observed else None
        conditions = {
            'drowsy': (eye_valid and self.closed, r['eye_seconds']),
            'yawn': (abs(yaw) < 35 and abs(pitch) < 30 and abs(m['roll']) < 25
                     and m['mar'] > max(0.5, self.baseline['mar']+0.3), r['yawn_seconds']),
            'distracted': (abs(yaw) > r['yaw_degrees'] or abs(pitch) > r['pitch_degrees'], r['away_seconds']),
            'fatigue': (eye_valid and observed >= r['perclos_min_seconds'] and self.perclos is not None and self.perclos > r['perclos_alert'], 0),
        }
        new = set()
        for key,(condition,duration) in conditions.items():
            if condition:
                self.started.setdefault(key, now)
                if now-self.started[key] >= duration-1e-9:
                    new.add(key)
            else:
                self.started.pop(key, None)
        events = sorted(new-self.active)
        if 'drowsy' in self.active and 'drowsy' not in new:
            events.append('drowsy_end')
        self.active = new
        status = next((k for k in ('drowsy','distracted','yawn','fatigue') if k in new), 'normal' if eye_valid else 'eyes_unknown')
        return self._result(status, events, eye_valid, 1, {'yaw':yaw,'pitch':pitch,'ear':eye,'mar':m['mar'],'threshold':self.baseline['eye']*r['eye_ratio']})

    def _result(self, status, events, eyes_valid, progress, metrics):
        observed = sum(b-a for a,b,_ in self.history)
        return {'status':status, 'events':events, 'eyes_valid':eyes_valid,
                'progress':progress, 'metrics':metrics, 'perclos':self.perclos if eyes_valid and status not in ('no_face','calibration') and observed >= RULES['perclos_min_seconds'] else None,
                'observed_seconds':observed, 'active':sorted(self.active)}
