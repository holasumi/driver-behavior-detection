export const angle = x => ((x + 180) % 360 + 360) % 360 - 180;
const median = a => { a.sort((x,y)=>x-y); const n=a.length; return n%2?a[(n-1)/2]:(a[n/2-1]+a[n/2])/2; };
export class DriverState {
  constructor(rules, eyesObscured=false) { Object.assign(this,{rules,eyesObscured,samples:[],baseline:null,last:null,previousClosed:null,history:[],started:{},active:new Set(),closed:false,perclos:null}); }
  update(m, now) {
    if(!Number.isFinite(now)) throw Error('Timestamp must be finite');
    const r=this.rules, dt=this.last===null?0:now-this.last;
    if(dt<0) throw Error('Timestamp must be monotonic');
    this.last=now;
    this.history=this.history.filter(x=>x[1]>now-r.perclos_window).map(([a,b,c])=>[Math.max(a,now-r.perclos_window),b,c]);
    if(dt>r.max_gap) {this.closed=false;this.started={};this.active.clear();this.previousClosed=null;if(!this.baseline)this.samples=[];}
    if(!m || !['ear','mar','yaw','pitch','roll'].every(k=>Number.isFinite(m[k])) || m.face_valid===false) {
      this.started={};this.active.clear();this.previousClosed=null;this.closed=false;
      if(!this.baseline)this.samples=[];
      return this.result('no_face',[],false,0,null);
    }
    const left=m.left_ear??m.ear, right=m.right_ear??m.ear, eye=Math.max(left,right);
    let eyeValid=!this.eyesObscured && m.eyes_valid!==false && left>=.02 && left<=.6 && right>=.02 && right<=.6 && Math.abs(left-right)<.12;
    if(!this.baseline) {
      const usable=Math.abs(m.roll)<15 && (this.eyesObscured || (eyeValid && eye>.14 && m.mar<.35));
      if(!usable){this.samples=[];return this.result('calibration',[],eyeValid,0,null);}
      if(this.samples.length && (Math.abs(angle(m.yaw-this.samples[0][1].yaw))>8 || Math.abs(angle(m.pitch-this.samples[0][1].pitch))>8))this.samples=[];
      this.samples.push([now,{...m,eye}]);
      const progress=Math.min(1,(now-this.samples[0][0])/r.calibration_seconds,this.samples.length/r.calibration_samples);
      if(progress<1)return this.result('calibration',[],eyeValid,progress,null);
      this.baseline=Object.fromEntries(['eye','mar','yaw','pitch'].map(k=>[k,median(this.samples.map(x=>x[1][k]))]));
      this.samples=[];this.previousClosed=null;
    }
    const yaw=angle(m.yaw-this.baseline.yaw), pitch=angle(m.pitch-this.baseline.pitch);
    eyeValid=eyeValid && Math.abs(yaw)<35 && Math.abs(pitch)<30 && Math.abs(m.roll)<25;
    this.closed=eyeValid?eye<this.baseline.eye*r[this.closed?'eye_release_ratio':'eye_ratio']:false;
    if(eyeValid && this.previousClosed!==null && dt>0 && dt<=r.max_gap)this.history.push([now-dt,now,this.previousClosed]);
    this.previousClosed=eyeValid?this.closed:null;
    const observed=this.history.reduce((s,[a,b])=>s+(b-a),0);
    this.perclos=observed?this.history.reduce((s,[a,b,c])=>s+(c?b-a:0),0)/observed:null;
    const conditions={drowsy:[eyeValid&&this.closed,r.eye_seconds],yawn:[Math.abs(yaw)<35&&Math.abs(pitch)<30&&Math.abs(m.roll)<25&&m.mar>Math.max(.5,this.baseline.mar+.3),r.yawn_seconds],distracted:[Math.abs(yaw)>r.yaw_degrees||Math.abs(pitch)>r.pitch_degrees,r.away_seconds],fatigue:[eyeValid&&observed>=r.perclos_min_seconds&&this.perclos!==null&&this.perclos>r.perclos_alert,0]};
    const next=new Set();
    for(const [key,[condition,duration]] of Object.entries(conditions)) {
      if(condition){this.started[key]??=now;if(now-this.started[key]>=duration-1e-9)next.add(key);}
      else delete this.started[key];
    }
    const events=[...next].filter(x=>!this.active.has(x)).sort();
    if(this.active.has('drowsy')&&!next.has('drowsy'))events.push('drowsy_end');
    this.active=next;
    const status=['drowsy','distracted','yawn','fatigue'].find(k=>next.has(k))??(eyeValid?'normal':'eyes_unknown');
    return this.result(status,events,eyeValid,1,{yaw,pitch,ear:eye,mar:m.mar,threshold:this.baseline.eye*r.eye_ratio});
  }
  result(status,events,eyes_valid,progress,metrics) {
    const observed_seconds=this.history.reduce((s,[a,b])=>s+(b-a),0);
    return {status,events,eyes_valid,progress,metrics,perclos:eyes_valid&&!['no_face','calibration'].includes(status)&&observed_seconds>=this.rules.perclos_min_seconds?this.perclos:null,observed_seconds,active:[...this.active].sort()};
  }
}
const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const ear=(p,ids)=>{const [a,b,c,d,e,f]=ids.map(i=>p[i]);return (dist(b,f)+dist(c,e))/(2*dist(a,d));};
export function faceMetrics(result,width,height) {
  const lm=result.faceLandmarks?.[0], matrix=result.facialTransformationMatrixes?.[0]?.data;
  if(!lm||!matrix || lm.length<468 || matrix.length!==16 || !Array.from(matrix).every(Number.isFinite) || result.faceLandmarks.length!==1)return null;
  const p=lm.map(v=>[v.x*width,v.y*height]);
  if(!p.every(v=>v.every(Number.isFinite)) || dist(p[33],p[263])<30)return null;
  const eyesValid=[[362,385,387,263,373,380],[33,160,158,133,153,144]].every(ids=>dist(p[ids[0]],p[ids[3]])>=12&&ids.every(i=>p[i][0]>=0&&p[i][0]<width&&p[i][1]>=0&&p[i][1]<height));
  const left=ear(p,[362,385,387,263,373,380]),right=ear(p,[33,160,158,133,153,144]);
  // MediaPipe MatrixData is column-major. Normalize columns to remove scale.
  const sx=Math.hypot(matrix[0],matrix[1],matrix[2]);
  const sy=Math.hypot(matrix[4],matrix[5],matrix[6]);
  const sz=Math.hypot(matrix[8],matrix[9],matrix[10]);
  if(Math.min(sx,sy,sz)<1e-6)return null;
  const yaw=Math.asin(Math.max(-1,Math.min(1,-matrix[2]/sx)))*180/Math.PI;
  const pitch=Math.atan2(matrix[6]/sy,matrix[10]/sz)*180/Math.PI;
  const roll=Math.atan2(matrix[1]/sx,matrix[0]/sx)*180/Math.PI;
  return {eyes_valid:eyesValid,ear:(left+right)/2,left_ear:left,right_ear:right,mar:dist(p[13],p[14])/dist(p[78],p[308]),yaw,pitch,roll,face_valid:[1,152,33,263,61,291].every(i=>lm[i].x>0&&lm[i].x<1&&lm[i].y>0&&lm[i].y<1)};
}
