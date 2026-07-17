# -*- coding: utf-8 -*-
"""Buffer d'uscita a 2 transistor (2N2222) — confronto dell'impulso in uscita
quando l'ingresso e' CMP_Q (uscita comparatore, 0->3,3 V) oppure TTL (dopo
MCP1402, 0->5 V).

Modello: BJT con Ebers-Moll + immagazzinamento di carica (transit time TF/TR +
capacita' di giunzione Cje/Cjc). E' l'effetto di carica immagazzinata che
produce lo "storage time" (ritardo di spegnimento) e quindi l'allungamento
dell'impulso: senza di esso i due casi sarebbero identici.

Topologia (come lo schema/LTspice): tutte le R = 1k, Vcc = 5V.
  Rin: vin -> B(Q1);  Rc: 5V -> C(Q1);  Rb: C(Q1) -> B(Q2);  RL: 5V -> C(Q2)=out
  emettitori a massa;  Cload sul nodo di uscita (pin Arduino + cavo).
Nodi: 0=B1 1=C1 2=B2 3=OUT
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VT = 0.02585
# 2N2222 / MMBT2222A (parametri tipici)
IS, BF, BR = 1e-14, 200.0, 4.0
TF, TR = 0.5e-9, 7e-9        # transit time diretto / inverso (satur.)
CJE, CJC = 25e-12, 8e-12       # capacita' di giunzione a riposo
RIN = RC = RB = RL = 1e3
VCC = 5.0
CLOAD = 20e-12                 # pin Arduino + traccia/cavo corto

def q_and_c(v):
    """carica e capacita' di una giunzione (diffusione + giunzione)."""
    ex = np.exp(min(v, 0.95) / VT)
    If = IS * (ex - 1.0)
    return If, ex

def bjt(vbe, vbc, TFj=TF, TRj=TR):
    """correnti Ebers-Moll (trasporto) + cariche immagazzinate."""
    ebe = np.exp(min(vbe, 0.95) / VT)
    ebc = np.exp(min(vbc, 0.95) / VT)
    If = IS * (ebe - 1.0)
    Ir = IS * (ebc - 1.0)
    ic = If - Ir - Ir / BR
    ib = If / BF + Ir / BR
    # conduttanze
    gf = IS * ebe / VT
    gr = IS * ebc / VT
    dic_dbe = gf
    dic_dbc = -gr - gr / BR
    dib_dbe = gf / BF
    dib_dbc = gr / BR
    # cariche
    qbe = TFj * If + CJE * vbe
    qbc = TRj * Ir + CJC * vbc
    cbe = TFj * gf + CJE
    cbc = TRj * gr + CJC
    return ic, ib, dic_dbe, dic_dbc, dib_dbe, dib_dbc, qbe, qbc, cbe, cbc

N = 4
def solve_dc(vin):
    v = np.array([0.7, 0.2, 0.7, 0.2])
    for _ in range(200):
        f = np.zeros(N); J = np.zeros((N, N))
        def addR(a, b, R):
            g = 1/R; va = v[a] if a>=0 else 0; vb = v[b] if b>=0 else 0
            i = g*(va-vb)
            if a>=0: f[a]+=i; J[a,a]+=g;
            if a>=0 and b>=0: J[a,b]-=g
            if b>=0: f[b]-=i; J[b,b]+=g
            if a>=0 and b>=0: J[b,a]-=g
        def addRk(a, Vk, R):  # a known-voltage rail/source
            g=1/R; f[a]+=g*(v[a]-Vk); J[a,a]+=g
        addRk(0, vin, RIN); addRk(1, VCC, RC); addR(1,2,RB); addRk(3, VCC, RL)
        # Q1 B0 C1, Q2 B2 C3
        for (b,c) in ((0,1),(2,3)):
            ic,ib,dcb,dcc,dbb,dbc,*_ = bjt(v[b], v[b]-v[c])
            f[b]+=ib; f[c]+=ic
            J[b,b]+=dbb+dbc; J[b,c]-=dbc
            J[c,b]+=dcb+dcc; J[c,c]-=dcc
        dv = np.linalg.solve(J, -f)
        dv = np.clip(dv, -0.2, 0.2); v += dv
        if np.max(np.abs(dv))<1e-12: break
    return v

def run(vin_wave, t):
    dt = t[1]-t[0]
    v = solve_dc(vin_wave[0])
    # cariche iniziali
    def charges(v):
        _,_,_,_,_,_,q1be,q1bc,_,_ = bjt(v[0], v[0]-v[1])
        _,_,_,_,_,_,q2be,q2bc,_,_ = bjt(v[2], v[2]-v[3])
        return np.array([q1be,q1bc,q2be,q2bc, CLOAD*v[3]])
    qp = charges(v)
    out = np.zeros(len(t))
    for k in range(len(t)):
        vin = vin_wave[k]
        for _ in range(60):
            f = np.zeros(N); J = np.zeros((N,N))
            def addR(a,b,R):
                g=1/R; va=v[a] if a>=0 else 0; vb=v[b] if b>=0 else 0; i=g*(va-vb)
                if a>=0: f[a]+=i; J[a,a]+=g
                if a>=0 and b>=0: J[a,b]-=g
                if b>=0: f[b]-=i; J[b,b]+=g
                if a>=0 and b>=0: J[b,a]-=g
            def addRk(a,Vk,R):
                g=1/R; f[a]+=g*(v[a]-Vk); J[a,a]+=g
            addRk(0,vin,RIN); addRk(1,VCC,RC); addR(1,2,RB); addRk(3,VCC,RL)
            # transistor + cariche
            q1=[0,0]; q2=[0,0]
            for idx,(b,c,off) in enumerate(((0,1,0),(2,3,2))):
                ic,ib,dcb,dcc,dbb,dbc,qbe,qbc,cbe,cbc = bjt(v[b], v[b]-v[c])
                f[b]+=ib; f[c]+=ic
                J[b,b]+=dbb+dbc; J[b,c]-=dbc
                J[c,b]+=dcb+dcc; J[c,c]-=dcc
                # corrente capacitiva be: (qbe-qbe_prev)/dt sul nodo base
                i_be=(qbe-qp[off])/dt
                f[b]+=i_be; J[b,b]+=cbe/dt
                # corrente capacitiva bc: tra base e collettore
                i_bc=(qbc-qp[off+1])/dt
                f[b]+=i_bc; f[c]-=i_bc
                J[b,b]+=cbc/dt; J[b,c]-=cbc/dt; J[c,b]-=cbc/dt; J[c,c]+=cbc/dt
                if idx==0: q1=[qbe,qbc]
                else: q2=[qbe,qbc]
            # Cload sul nodo out (3)
            i_cl=(CLOAD*v[3]-qp[4])/dt
            f[3]+=i_cl; J[3,3]+=CLOAD/dt
            dv=np.linalg.solve(J,-f); dv=np.clip(dv,-0.4,0.4); v+=dv
            if np.max(np.abs(dv))<1e-7: break
        qp=np.array([q1[0],q1[1],q2[0],q2[1],CLOAD*v[3]])
        out[k]=v[3]
    return out

def width(t, y, lo, hi):
    """larghezza a meta' fra lo e hi; ritorna (t_rise, t_fall, w)."""
    thr=(lo+hi)/2
    above=y>thr
    if not above.any(): return None
    i0=np.argmax(above); i1=len(above)-1-np.argmax(above[::-1])
    def cross(i,rising):
        if i<=0 or i>=len(t): return t[i]
        y0,y1=y[i-1],y[i];
        if y1==y0: return t[i]
        return t[i-1]+(thr-y0)/(y1-y0)*(t[i]-t[i-1])
    tr=cross(i0,True); tf=cross(i1+1 if i1+1<len(t) else i1,False)
    return tr,tf,tf-tr

# ---------------- ingressi realistici ----------------
# CMP_Q dalla catena vera (uscita comparatore): larghezza = time-over-threshold.
from sim_catena import transient, solve_dc as chain_dc
def cmpq_width(npe, vth=0.10):
    t,vv,comp,le,vdc = transient(npe, T=1.5e-6, dt=0.5e-9, vth=vth)
    above=comp>1
    if not above.any(): return 0.0
    i0=np.argmax(above); i1=len(above)-1-np.argmax(above[::-1])
    return (t[i1]-t[i0])
# muone tipico e muone grande
W_typ = cmpq_width(180)
W_big = cmpq_width(500)
print(f"time-over-threshold CMP_Q: muone tipico(180 pe)={W_typ*1e9:.0f} ns, grande(500 pe)={W_big*1e9:.0f} ns")

# griglia fine per il buffer
DT=0.25e-9; TW=700e-9; t=np.arange(0,TW,DT)
t0=80e-9
def pulse(t, t0, W, amp, tr=6e-9, td=0.0):
    """impulso trapezoidale: parte a t0+td, largo W, fronti tr."""
    x=np.zeros_like(t)
    a=t0+td; b=a+W
    rise=np.clip((t-a)/tr,0,1); fall=np.clip((b-t)/tr,0,1)
    return amp*np.minimum(rise,fall)
# CMP_Q: 0->3,3 V, larghezza W_typ
vin_cmpq = pulse(t, t0, W_typ, 3.3)
# TTL: 0->5 V, stessa larghezza + ritardo del MCP1402 (~25 ns) — la larghezza si conserva
vin_ttl  = pulse(t, t0, W_typ, 5.0, td=25e-9)

out_from_cmpq = run(vin_cmpq, t)
out_from_ttl  = run(vin_ttl,  t)

wc = width(t, out_from_cmpq, 0.2, out_from_cmpq.max())
wt = width(t, out_from_ttl,  0.2, out_from_ttl.max())
print(f"ingresso CMP_Q (3,3V, {W_typ*1e9:.0f} ns) -> uscita: larghezza {wc[2]*1e9:.0f} ns, picco {out_from_cmpq.max():.2f} V")
print(f"ingresso TTL   (5,0V, {W_typ*1e9:.0f} ns) -> uscita: larghezza {wt[2]*1e9:.0f} ns, picco {out_from_ttl.max():.2f} V")
print(f"differenza larghezza uscita: {(wt[2]-wc[2])*1e9:+.0f} ns")

# ---------------- grafici ----------------
fig, ax = plt.subplots(3,1, figsize=(12,9))
tns = t*1e9
fig.suptitle("Buffer d'uscita: CMP_Q vs TTL come ingresso (muone tipico, 180 p.e.)", fontsize=13)

ax[0].plot(tns, vin_cmpq, color="#5eb1ff", lw=1.8, label="CMP_Q  (uscita comparatore, 0→3,3 V)")
ax[0].plot(tns, vin_ttl,  color="#ffa94d", lw=1.8, label="TTL  (dopo MCP1402, 0→5 V, +25 ns)")
ax[0].axhline(3.3,color="#5eb1ff",ls=":",lw=.7); ax[0].axhline(5,color="#ffa94d",ls=":",lw=.7)
ax[0].set_ylabel("V"); ax[0].set_title("I due possibili INGRESSI del buffer — impulso rettangolare, larghezza = time-over-threshold")
ax[0].legend(loc="upper right", fontsize=9)
ax[0].annotate("", xy=(t0*1e9,3.55), xytext=((t0+W_typ)*1e9,3.55),
               arrowprops=dict(arrowstyle="<->",color="#5eb1ff"))
ax[0].text((t0+W_typ/2)*1e9, 3.7, f"{W_typ*1e9:.0f} ns", color="#5eb1ff", ha="center", fontsize=9)

ax[1].plot(tns, out_from_cmpq, color="#41d98d", lw=1.8, label=f"uscita da CMP_Q — largo {wc[2]*1e9:.0f} ns")
ax[1].plot(tns, out_from_ttl,  color="#e11d48", lw=1.8, label=f"uscita da TTL — largo {wt[2]*1e9:.0f} ns")
ax[1].axhline(out_from_cmpq.max()/2, color="#888", ls=":", lw=.7)
ax[1].set_ylabel("V uscita buffer"); ax[1].set_title("USCITA del buffer verso Arduino — il caso TTL e' piu' largo (piu' carica immagazzinata)")
ax[1].legend(loc="upper right", fontsize=9)

# zoom sul fronte di discesa reale
fall_c=wc[1]*1e9; fall_t=wt[1]*1e9
lo=min(fall_c,fall_t)-40; hi=max(fall_c,fall_t)+40
m=(tns>lo)&(tns<hi)
ax[2].plot(tns[m], out_from_cmpq[m], color="#41d98d", lw=2.2, label=f"da CMP_Q — scende a {fall_c:.0f} ns")
ax[2].plot(tns[m], out_from_ttl[m],  color="#e11d48", lw=2.2, label=f"da TTL — scende a {fall_t:.0f} ns")
ax[2].axhline(out_from_cmpq.max()/2, color="#888", ls=":", lw=.7)
ax[2].axvline(fall_c,color="#41d98d",ls=":",lw=.8); ax[2].axvline(fall_t,color="#e11d48",ls=":",lw=.8)
ax[2].annotate("", xy=(fall_c,1.2), xytext=(fall_t,1.2), arrowprops=dict(arrowstyle="<->",color="#888"))
ax[2].text((fall_c+fall_t)/2,1.4,f"+{fall_t-fall_c:.0f} ns",ha="center",color="#444",fontsize=10)
ax[2].set_ylabel("V"); ax[2].set_xlabel("tempo [ns]")
ax[2].set_title("ZOOM sul fronte di discesa: da TTL scende piu' tardi (piu' storage time + 25 ns di ritardo MCP1402)")
ax[2].legend(loc="upper right", fontsize=9)
for a in ax: a.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("sim_buffer.png", dpi=115)
print("salvato sim_buffer.png")
