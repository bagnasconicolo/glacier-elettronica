# -*- coding: utf-8 -*-
"""Sequenza di muoni attraverso il rivelatore.

Parte 1 (circuitale): finestra di 200 us con arrivi poissoniani ACCELERATI
(per poterli vedere nella stessa finestra), carica da distribuzione
Landau/Moyal, piu' dark count del SiPM (1-2 p.e.) sotto soglia.
Solver non lineare riusato da sim_catena.

Parte 2 (comportamentale, scala reale): 20 s a 1,7 Hz (paletta 10x10 cm),
timeline TTL + LED (monostabile 11 ms) + statistiche.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sim_catena import residual_jacobian, solve_dc, VCC

rng = np.random.default_rng(42)

# ------------------- parte 1: transitorio circuitale -------------------
T = 200e-6
DT = 2e-9
VTH = 0.10          # soglia ~3 p.e. (100 mV): sopra i dark count
QPE = 0.5e-12
TAU = 45e-9

# muoni: rate accelerato per visualizzazione (reale ~1,7 Hz su 10x10 cm)
RATE_MU_DEMO = 60e3          # accelerato: ~12 eventi nella finestra
# dark counts SiPM: ~200 kHz, 1-2 p.e.
RATE_DARK = 200e3

def poisson_times(rate, T):
    t, out = 0.0, []
    while True:
        t += rng.exponential(1.0 / rate)
        if t >= T:
            return out
        out.append(t)

mu_times = poisson_times(RATE_MU_DEMO, T)
# carica muone: Moyal (approssimazione della Landau), mediana ~250 p.e.
# Moyal (approx. Landau): X = mu + sigma*(-ln V), V ~ chi2(1)
V = rng.chisquare(1, size=len(mu_times))
mu_npe = np.clip(220 + 60 * (-np.log(V)), 80, 2000)
dark_times = poisson_times(RATE_DARK, T)
dark_npe = rng.choice([1, 1, 1, 2], size=len(dark_times))  # per lo piu' 1 p.e.

events = [(t, q, "mu") for t, q in zip(mu_times, mu_npe)] + \
         [(t, q, "dark") for t, q in zip(dark_times, dark_npe)]
events.sort()
print(f"finestra {T*1e6:.0f} us: {len(mu_times)} muoni + {len(dark_times)} dark count")

ev_t = np.array([e[0] for e in events])
ev_q = np.array([e[1] * QPE for e in events])

def i_in(t):
    dt = t - ev_t
    m = (dt >= 0) & (dt < 8 * TAU)
    if not m.any():
        return 0.0
    return float(np.sum(ev_q[m] / TAU * np.exp(-dt[m] / TAU)))

v = solve_dc()
vdc = v.copy()
steps = int(T / DT)
dec = 5                      # salva 1 campione ogni 5 (dt salvato = 10 ns)
n_out = steps // dec
t_axis = np.zeros(n_out); v_cmp = np.zeros(n_out); i_axis = np.zeros(n_out)
q_axis = np.zeros(n_out)
q_state = 0.0
v_le = 0.0
R16v, C9v = 1e3, 100e-12
ttl_edges = []               # (t_rise, t_fall)
rise_t = None
for k in range(steps):
    t = (k + 1) * DT
    cur = i_in(t)
    vn = v.copy()
    for _ in range(40):
        f, J = residual_jacobian(vn, v, DT, cur)
        dv = np.linalg.solve(J, -f)
        dv = np.clip(dv, -0.3, 0.3)
        vn += dv
        if np.max(np.abs(dv)) < 1e-8:
            break
    q_prev = q_state
    latched = v_le > VCC / 2
    if not latched:
        if vn[5] > VTH + 0.002:
            q_state = VCC
        elif vn[5] < VTH - 0.002:
            q_state = 0.0
    v_le += (q_state - q_prev) - v_le * DT / (R16v * C9v)
    v_le = max(min(v_le, VCC), -VCC)
    if q_state > 1 and q_prev < 1:
        rise_t = t
    if q_state < 1 and q_prev > 1 and rise_t is not None:
        ttl_edges.append((rise_t, t))
        rise_t = None
    v = vn
    if k % dec == 0:
        j = k // dec
        t_axis[j] = t; v_cmp[j] = vn[5]; i_axis[j] = cur; q_axis[j] = q_state

n_trig = len(ttl_edges)
print(f"trigger TTL: {n_trig} (attesi: {len(mu_times)} muoni; dark rigettati)")
widths = [(b - a) * 1e9 for a, b in ttl_edges]

fig, ax = plt.subplots(3, 1, figsize=(13, 8), sharex=True)
fig.suptitle(f"Sequenza di eventi (finestra 200 µs, rate muoni accelerato a 60 kHz) — "
             f"soglia {VTH*1e3:.0f} mV ≈ 3 p.e.", fontsize=12)
ax[0].plot(t_axis * 1e6, i_axis * 1e3, "k", lw=0.8)
for tm, q in zip(mu_times, mu_npe):
    ax[0].annotate(f"µ {q:.0f}pe", (tm * 1e6, (q * QPE / TAU) * 1e3),
                   fontsize=7, color="tab:red", rotation=45)
ax[0].set_ylabel("I SiPM [mA]"); ax[0].set_title("corrente dal SiPM (muoni + dark count)")
ax[1].plot(t_axis * 1e6, v_cmp * 1e3, "tab:blue", lw=0.8)
ax[1].axhline(VTH * 1e3, color="r", ls="--", lw=1, label=f"soglia {VTH*1e3:.0f} mV")
ax[1].set_ylabel("mV"); ax[1].set_title("ingresso comparatore (nodo E)"); ax[1].legend(loc="upper right")
ax[2].plot(t_axis * 1e6, q_axis, "tab:green", lw=1)
ax[2].set_ylabel("V"); ax[2].set_xlabel("µs"); ax[2].set_title(f"uscita TTL — {n_trig} trigger")
for a in ax:
    a.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("sim_muoni_treno.png", dpi=110)
print("salvato sim_muoni_treno.png")
if widths:
    print("larghezze TTL [ns]:", [f"{w:.0f}" for w in widths])

# ------------------- parte 2: scala reale (comportamentale) -------------------
RATE_REAL = 1.7      # Hz, paletta 10x10 cm a livello del mare
T2 = 20.0
mu_real = poisson_times(RATE_REAL, T2)
T555 = 1.1 * 100e3 * 100e-9   # 11 ms

fig, ax = plt.subplots(2, 1, figsize=(13, 5))
fig.suptitle(f"Scala reale: {len(mu_real)} muoni in {T2:.0f} s (rate {RATE_REAL} Hz, 10×10 cm)", fontsize=12)
for tm in mu_real:
    ax[0].axvline(tm, color="tab:red", lw=1)
ax[0].set_ylabel("trigger"); ax[0].set_yticks([])
ax[0].set_title("impulsi TTL (larghezza ~100-200 ns, non in scala)")
# LED: monostabile retriggerable? TLC555 monostabile standard: non retrigger durante T555
led_on = []
t_end = -1
for tm in mu_real:
    if tm > t_end:
        led_on.append((tm, tm + T555))
        t_end = tm + T555
for a, b in led_on:
    ax[1].axvspan(a, b, color="tab:green", alpha=0.8)
ax[1].set_ylabel("LED"); ax[1].set_yticks([])
ax[1].set_xlabel("s")
duty = sum(b - a for a, b in led_on) / T2 * 100
ax[1].set_title(f"LED (11 ms/evento) — duty {duty:.1f}%")
for a in ax:
    a.grid(alpha=0.2, axis="x")
    a.set_xlim(0, T2)
plt.tight_layout()
plt.savefig("sim_muoni_reale.png", dpi=110)
print("salvato sim_muoni_reale.png")
print(f"duty LED: {duty:.2f}%  | prob. pile-up nel monostabile: {RATE_REAL*T555*100:.2f}%")
