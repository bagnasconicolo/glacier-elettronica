# -*- coding: utf-8 -*-
"""Treno di muoni END-TO-END, fino al pin Arduino.

Catena completa: muone -> SiPM -> ampli (Q1/Q2) -> comparatore (soglia)
-> CMP_Q (0->3,3 V) -> BUFFER a 2 transistor (5 V) -> pin Arduino.

- il front-end e' il solver circuitale non lineare (come sim_catena/sim_muoni);
- il buffer e' modellato in modo comportamentale ma CALIBRATO sul modello
  dettagliato di sim_buffer (uscita 0->5 V, la larghezza si conserva entro
  ~10-20 ns, fronte di salita ~storage-limited, discesa netta);
- l'Arduino conta i FRONTI DI SALITA (come attachInterrupt(RISING)).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sim_catena import residual_jacobian, solve_dc, VCC

rng = np.random.default_rng(42)

# ---------------- treno di eventi ----------------
T = 200e-6
DT = 2e-9
VTH = 0.10                 # soglia ~3 p.e.
QPE = 0.5e-12
TAU = 45e-9
RATE_MU = 60e3             # accelerato per la demo (reale ~1,7 Hz)
RATE_DARK = 200e3
VBUF = 5.0                 # alimentazione del buffer

def poisson_times(rate, T):
    t, out = 0.0, []
    while True:
        t += rng.exponential(1.0/rate)
        if t >= T: return out
        out.append(t)

mu_times = poisson_times(RATE_MU, T)
Vc = rng.chisquare(1, size=len(mu_times))
mu_npe = np.clip(220 + 60*(-np.log(Vc)), 80, 2000)
dark_times = poisson_times(RATE_DARK, T)
dark_npe = rng.choice([1,1,1,2], size=len(dark_times))
events = sorted([(t,q,'mu') for t,q in zip(mu_times,mu_npe)] +
                [(t,q,'dark') for t,q in zip(dark_times,dark_npe)])
ev_t = np.array([e[0] for e in events]); ev_q = np.array([e[1]*QPE for e in events])
print(f"finestra {T*1e6:.0f} us: {len(mu_times)} muoni + {len(dark_times)} dark count")

def i_in(t):
    dt = t-ev_t; m=(dt>=0)&(dt<8*TAU)
    if not m.any(): return 0.0
    return float(np.sum(ev_q[m]/TAU*np.exp(-dt[m]/TAU)))

# ---------------- run catena + buffer comportamentale ----------------
v = solve_dc(); vdc=v.copy()
steps = int(T/DT); dec=5; n_out=steps//dec
t_axis=np.zeros(n_out); i_ax=np.zeros(n_out); e_ax=np.zeros(n_out)
q_ax=np.zeros(n_out); buf_ax=np.zeros(n_out)
q_state=0.0; v_le=0.0; R16v,C9v=1e3,100e-12
v_buf=0.0                       # uscita buffer (stato, primo ordine)
TAU_RISE=26e-9; TAU_FALL=8e-9   # calibrati su sim_buffer (salita lenta, discesa netta)
mu_pending=0
cmpq_edges=[]; buf_edges=[]     # tempi dei fronti di salita
q_prev_glob=0
for k in range(steps):
    t=(k+1)*DT
    cur=i_in(t); vn=v.copy()
    for _ in range(40):
        f,J=residual_jacobian(vn,v,DT,cur)
        dv=np.linalg.solve(J,-f); dv=np.clip(dv,-0.3,0.3); vn+=dv
        if np.max(np.abs(dv))<1e-8: break
    q_prev=q_state; latched=v_le>VCC/2
    if not latched:
        if vn[5]>VTH+0.002: q_state=VCC
        elif vn[5]<VTH-0.002: q_state=0.0
    v_le+=(q_state-q_prev)-v_le*DT/(R16v*C9v); v_le=max(min(v_le,VCC),-VCC)
    if q_state>1 and q_prev<1: cmpq_edges.append(t)
    # buffer: uscita 0->5V, insegue CMP_Q con salita/discesa asimmetriche
    target = VBUF if q_state>1 else 0.0
    tau = TAU_RISE if target>v_buf else TAU_FALL
    v_buf += (target-v_buf)*(1-np.exp(-DT/tau))
    # fronte di salita del buffer (Arduino conta qui): soglia logica 2,5 V
    if v_buf>2.5 and q_prev_glob<=2.5: buf_edges.append(t)
    q_prev_glob=v_buf
    v=vn
    if k%dec==0:
        j=k//dec
        t_axis[j]=t; i_ax[j]=cur; e_ax[j]=vn[5]; q_ax[j]=q_state; buf_ax[j]=v_buf

n_mu=len(mu_times); n_trig=len(cmpq_edges); n_ard=len(buf_edges)
print(f"muoni: {n_mu} | trigger comparatore (CMP_Q): {n_trig} | conteggi Arduino (buffer): {n_ard}")
print(f"dark count generati: {len(dark_times)} -> falsi trigger: {n_trig-n_mu if n_trig>=n_mu else 0}")

# ---------------- grafico treno ----------------
fig,ax=plt.subplots(4,1,figsize=(13,10),sharex=True)
fig.suptitle(f"Treno completo end-to-end: {n_mu} muoni in {T*1e6:.0f} µs (rate demo {RATE_MU/1e3:.0f} kHz) — "
             f"soglia {VTH*1e3:.0f} mV — buffer 5 V da CMP_Q verso Arduino", fontsize=12)
tus=t_axis*1e6
ax[0].plot(tus,i_ax*1e3,"k",lw=0.7)
for tm,q in zip(mu_times,mu_npe):
    ax[0].annotate(f"µ {q:.0f}pe",(tm*1e6,(q*QPE/TAU)*1e3),fontsize=7,color="tab:red",rotation=45)
ax[0].set_ylabel("I SiPM [mA]"); ax[0].set_title("1) corrente dal SiPM  (muoni alti + dark count piccoli)")
ax[1].plot(tus,e_ax*1e3,"tab:blue",lw=0.7)
ax[1].axhline(VTH*1e3,color="r",ls="--",lw=1,label=f"soglia {VTH*1e3:.0f} mV")
ax[1].set_ylabel("mV"); ax[1].set_title("2) ingresso comparatore  (nodo E)"); ax[1].legend(loc="upper right")
ax[2].plot(tus,q_ax,"tab:green",lw=1)
ax[2].set_ylabel("V"); ax[2].set_ylim(-0.3,3.8)
ax[2].set_title(f"3) CMP_Q  (uscita comparatore, 0→3,3 V) — {n_trig} impulsi")
ax[3].plot(tus,buf_ax,color="#e11d48",lw=1.2)
ax[3].axhline(2.5,color="#888",ls=":",lw=.7,label="soglia logica Arduino ~2,5 V")
for te in buf_edges:
    ax[3].plot(te*1e6,5.05,"v",color="#c2410c",ms=7)
ax[3].set_ylabel("V"); ax[3].set_ylim(-0.4,5.7); ax[3].set_xlabel("µs")
ax[3].set_title(f"4) USCITA BUFFER → pin Arduino (0→5 V) — {n_ard} conteggi (▼ = interrupt RISING)")
ax[3].legend(loc="upper right")
for a in ax: a.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("sim_treno_completo.png",dpi=115)
print("salvato sim_treno_completo.png")

# ---------------- zoom su un muone (tutta la catena in un evento) ----------------
tm0 = mu_times[np.argmax(mu_npe)]     # il muone piu' grande
w = (t_axis>tm0-0.05e-6)&(t_axis<tm0+0.5e-6)
fig2,bx=plt.subplots(4,1,figsize=(11,8),sharex=True)
fig2.suptitle(f"Zoom su un singolo muone ({mu_npe[np.argmax(mu_npe)]:.0f} p.e.): la catena completa fino ad Arduino",fontsize=12)
tzz=(t_axis[w]-tm0)*1e9
bx[0].plot(tzz,i_ax[w]*1e3,"k"); bx[0].set_ylabel("I SiPM\n[mA]")
bx[1].plot(tzz,e_ax[w]*1e3,"tab:blue"); bx[1].axhline(VTH*1e3,color="r",ls="--",lw=1)
bx[1].set_ylabel("comp in\n[mV]")
bx[2].plot(tzz,q_ax[w],"tab:green"); bx[2].set_ylabel("CMP_Q\n[V]"); bx[2].set_ylim(-0.3,3.8)
bx[3].plot(tzz,buf_ax[w],color="#e11d48"); bx[3].axhline(2.5,color="#888",ls=":",lw=.7)
bx[3].set_ylabel("Arduino\n[V]"); bx[3].set_ylim(-0.4,5.7); bx[3].set_xlabel("tempo dal muone [ns]")
for a in bx: a.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("sim_treno_zoom.png",dpi=115)
print("salvato sim_treno_zoom.png")

# ---------------- scala reale + sketch Arduino ----------------
RATE_REAL=1.7; T2=60.0
mu_real=poisson_times(RATE_REAL,T2)
counts_per_s=[sum(1 for tm in mu_real if s<=tm<s+1) for s in range(int(T2))]
print(f"scala reale: {len(mu_real)} muoni in {T2:.0f} s -> media {len(mu_real)/T2:.2f} conteggi/s")
fig3,cx=plt.subplots(figsize=(11,3.4))
cx.bar(range(int(T2)),counts_per_s,width=0.9,color="#c2410c")
cx.axhline(RATE_REAL,color="#333",ls="--",lw=1,label=f"media attesa {RATE_REAL} Hz")
cx.set_xlabel("secondi"); cx.set_ylabel("conteggi Arduino/s")
cx.set_title(f"Conteggi al secondo che l'Arduino registrerebbe (paletta 10×10 cm, {T2:.0f} s)")
cx.legend(); cx.grid(alpha=0.3,axis="y")
plt.tight_layout(); plt.savefig("sim_treno_reale.png",dpi=115)
print("salvato sim_treno_reale.png")
