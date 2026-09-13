import json
import subprocess
import unittest
from pathlib import Path
from state import DriverState

M = dict(ear=.3, left_ear=.3, right_ear=.3, mar=.1, yaw=0, pitch=0, roll=0)
def calibrated(fps=30, **kwargs):
    s=DriverState(**kwargs)
    for i in range(4*fps+1):s.update(M,i/fps)
    assert s.baseline
    return s

class StateTests(unittest.TestCase):
    def test_rejects_invalid_time(self):
        for t in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                DriverState().update(M, t)

    def test_gap_resets_eye_hysteresis(self):
        s = calibrated()
        s.update(dict(M, left_ear=.1, right_ear=.1), 4.1)
        out = s.update(dict(M, left_ear=.23, right_ear=.23), 6)
        self.assertFalse(s.closed)
        self.assertNotIn('drowsy', out['active'])

    def test_extreme_pose_does_not_report_yawn(self):
        s = calibrated()
        for i in range(1, 91):
            out = s.update(dict(M, yaw=45, mar=.8), 4+i/30)
        self.assertNotIn('yawn', out['active'])
        self.assertIn('distracted', out['active'])

    def test_turn_detected_at_multiple_fps(self):
        for fps in (10,15,30,60):
            s=calibrated(fps)
            for i in range(1,fps+2):out=s.update(dict(M,yaw=28),4+i/fps)
            self.assertIn('distracted',out['active'])
    def test_brief_glance_does_not_alert(self):
        s=calibrated()
        for i in range(1,20):out=s.update(dict(M,yaw=28),4+i/30)
        self.assertNotIn('distracted',out['active'])
    def test_blink_and_wink_do_not_alert(self):
        s=calibrated()
        for i in range(1,7):s.update(dict(M,ear=.1,left_ear=.1,right_ear=.1),4+i/30)
        out=s.update(M,4.3)
        self.assertNotIn('drowsy',out['active'])
        for i in range(1,70):out=s.update(dict(M,left_ear=.1),4.3+i/30)
        self.assertNotIn('drowsy',out['active'])
    def test_sustained_closure_alerts_once(self):
        s=calibrated();events=[]
        for i in range(1,91):
            out=s.update(dict(M,ear=.1,left_ear=.1,right_ear=.1),4+i/30);events+=out['events']
        self.assertEqual(events.count('drowsy'),1)
        self.assertIn('drowsy',out['active'])
    def test_camera_gap_cannot_trigger_alarm(self):
        s=calibrated();s.update(dict(M,yaw=30),4.1)
        self.assertNotIn('distracted',s.update(dict(M,yaw=30),20)['active'])
    def test_no_face_resets_turn_duration(self):
        s=calibrated();s.update(dict(M,yaw=30),4.1);s.update(None,4.4)
        self.assertNotIn('distracted',s.update(dict(M,yaw=30),4.5)['active'])
    def test_unknown_not_open_and_perclos_warmup(self):
        s=calibrated()
        for i in range(1,31):s.update(M,4+i/30)
        known=sum(b-a for a,b,_ in s.history)
        for i in range(1,61):out=s.update(None,5+i/30)
        self.assertIsNone(out['perclos']);self.assertEqual(out['status'],'no_face')
        self.assertAlmostEqual(sum(b-a for a,b,_ in s.history),known)
    def test_occluded_glasses_still_detect_turn(self):
        s=calibrated(eyes_obscured=True)
        for i in range(1,40):out=s.update(dict(M,yaw=30),4+i/30)
        self.assertIn('distracted',out['active']);self.assertFalse(out['eyes_valid'])
    def test_calibration_rejects_unstable_head(self):
        s=DriverState()
        for i in range(180):s.update(dict(M,yaw=20 if i%2 else -20),i/30)
        self.assertIsNone(s.baseline)
    def test_nonfinite_pose_is_unknown(self):
        self.assertEqual(calibrated().update(dict(M,yaw=float('nan')),4.1)['status'],'no_face')
    def test_perclos_time_weighted(self):
        s=calibrated()
        # Ten seconds open at 10 FPS; ten seconds closed at 30 FPS.
        for i in range(1,101):s.update(M,4+i/10)
        for i in range(1,301):out=s.update(dict(M,ear=.1,left_ear=.1,right_ear=.1),14+i/30)
        self.assertAlmostEqual(out['perclos'],.5,delta=.01)
    def test_browser_python_parity(self):
        seq=[]
        for i in range(1201):
            t=i/30;m=dict(M)
            if 6<t<9:m['yaw']=30
            if 11<t<14:m.update(ear=.1,left_ear=.1,right_ear=.1)
            if 15<t<16:m=None
            if 18<t<21:m['mar']=.8
            if 22<t<25:m.update(yaw=45,mar=.8)
            if 27<t<29:m['eyes_valid']=False
            seq.append([t,m])
        s=DriverState();expected=[s.update(m,t) for t,m in seq]
        script="""import {DriverState} from './web/dist/engine.mjs';import fs from 'node:fs';const rules=JSON.parse(fs.readFileSync('./web/dist/rules.json'));const seq=JSON.parse(fs.readFileSync(0,'utf8'));const s=new DriverState(rules);console.log(JSON.stringify(seq.map(([t,m])=>s.update(m,t))));"""
        out=subprocess.check_output(['node','--input-type=module','-e',script],input=json.dumps(seq).encode())
        actual=json.loads(out)
        for a,b in zip(expected,actual):
            self.assertEqual(a['status'],b['status']);self.assertEqual(a['events'],b['events'])
            if a['perclos'] is not None:self.assertAlmostEqual(a['perclos'],b['perclos'])

if __name__=='__main__':unittest.main()
