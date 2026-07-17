# -*- coding: utf-8 -*-
"""Simulazione transitoria della catena di segnale:
impulso SiPM -> C7 -> Q1 (BFR93A, CE con retroazione) -> Q2 (MMBTH81, PNP)
-> C11 -> MAX961 (comportamentale con isteresi + latch C9/R16) -> uscite.

Solver: MNA + backward Euler + Newton. BJT: Ebers-Moll (trasporto).
Nodi: 0=SIG, 1=B(Q1 base), 2=C(Q1 coll/Q2 base), 3=E2(Q2 emitter),
      4=D(Q2 coll), 5=E(ingresso comparatore)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

VCC = 3.3
VT = 0.02585

# BJT Ebers-Moll (modello di trasporto), parametri tipici RF
class BJT:
    def __init__(self, IS, BF, BR=4.0, pnp=False):
        self.IS, self.BF, self.BR, self.pnp = IS, BF, BR, pnp

    def currents(self, vbe, vbc):
        s = -1.0 if self.pnp else 1.0
        vbe, vbc = s * vbe, s * vbc
        vbe = min(vbe, 0.95); vbc = min(vbc, 0.95)   # clamp anti-overflow
        e1 = np.exp(vbe / VT); e2 = np.exp(vbc / VT)
        icc = self.IS * (e1 - e2)
        ibe = self.IS / self.BF * (e1 - 1)
        ibc = self.IS / self.BR * (e2 - 1)
        ic = icc - ibc
        ib = ibe + ibc
        # derivate
        g1 = self.IS * e1 / VT
        g2 = self.IS * e2 / VT
        dic_dvbe = g1
        dic_dvbc = -g2 - g2 / self.BR
        dib_dvbe = g1 / self.BF
        dib_dvbc = g2 / self.BR
        return (s * ic, s * ib,
                dic_dvbe, dic_dvbc, dib_dvbe, dib_dvbc)

Q1 = BJT(IS=50e-15, BF=90)                 # BFR93A (tipico)
Q2 = BJT(IS=50e-15, BF=70, pnp=True)       # MMBTH81 (tipico)

# reti passive
R10, C7v, R9, R11, R12 = 10e3, 10e-9, 1.8e3, 5.6e3, 1e3
R13, R14, C11v, R15 = 560.0, 1e3, 10e-9, 1e3
# capacita' parassite piccole per stabilita' numerica
CPAR = 0.5e-12

N = 6  # nodi

def stamp_R(G, a, b, R):
    g = 1.0 / R
    if a >= 0: G[a, a] += g
    if b >= 0: G[b, b] += g
    if a >= 0 and b >= 0:
        G[a, b] -= g; G[b, a] -= g

def residual_jacobian(v, v_prev, dt, i_in):
    """f(v)=0 con backward Euler; ritorna (f, J)."""
    f = np.zeros(N)
    J = np.zeros((N, N))

    def add_R(a, b, R):
        g = 1.0 / R
        va = v[a] if a >= 0 else 0.0
        vb = v[b] if b >= 0 else 0.0
        i = g * (va - vb)
        if a >= 0:
            f[a] += i; J[a, a] += g
            if b >= 0: J[a, b] -= g
        if b >= 0:
            f[b] -= i; J[b, b] += g
            if a >= 0: J[b, a] -= g

    def add_R_to_vcc(a, R):
        g = 1.0 / R
        i = g * (v[a] - VCC)
        f[a] += i; J[a, a] += g

    def add_C(a, b, C):
        g = C / dt
        va = v[a] if a >= 0 else 0.0
        vb = v[b] if b >= 0 else 0.0
        va0 = v_prev[a] if a >= 0 else 0.0
        vb0 = v_prev[b] if b >= 0 else 0.0
        i = g * ((va - vb) - (va0 - vb0))
        if a >= 0:
            f[a] += i; J[a, a] += g
            if b >= 0: J[a, b] -= g
        if b >= 0:
            f[b] -= i; J[b, b] += g
            if a >= 0: J[b, a] -= g

    # ingresso: generatore di corrente nel nodo SIG (verso il nodo)
    f[0] -= i_in
    add_R(0, -1, R10)
    add_C(0, 1, C7v)
    add_R(1, -1, R9)
    add_R(1, 2, R11)
    add_R_to_vcc(2, R12)
    add_R_to_vcc(3, R13)
    add_R(4, -1, R14)
    add_C(4, 5, C11v)
    add_R(5, -1, R15)
    for n in range(N):
        add_C(n, -1, CPAR)

    # Q1 NPN: B=1, C=2, E=GND
    ic, ib, dic_be, dic_bc, dib_be, dib_bc = Q1.currents(v[1], v[1] - v[2])
    f[1] += ib
    f[2] += ic
    # vbe=v1, vbc=v1-v2
    J[1, 1] += dib_be + dib_bc; J[1, 2] += -dib_bc
    J[2, 1] += dic_be + dic_bc; J[2, 2] += -dic_bc

    # Q2 PNP: B=2, E=3, C=4
    vbe2 = v[2] - v[3]
    vbc2 = v[2] - v[4]
    ic2, ib2, dic_be2, dic_bc2, dib_be2, dib_bc2 = Q2.currents(vbe2, vbc2)
    f[2] += ib2
    f[3] -= (ib2 + ic2)      # emettitore
    f[4] += ic2
    J[2, 2] += dib_be2 + dib_bc2
    J[2, 3] += -dib_be2
    J[2, 4] += -dib_bc2
    J[3, 2] -= (dib_be2 + dib_bc2 + dic_be2 + dic_bc2)
    J[3, 3] += (dib_be2 + dic_be2)
    J[3, 4] += (dib_bc2 + dic_bc2)
    J[4, 2] += dic_be2 + dic_bc2
    J[4, 3] += -dic_be2
    J[4, 4] += -dic_bc2
    return f, J

def solve_dc():
    v = np.array([0.0, 0.7, 2.5, 3.1, 0.3, 0.0])
    for _ in range(200):
        f, J = residual_jacobian(v, v, 1e0, 0.0)
        dv = np.linalg.solve(J, -f)
        dv = np.clip(dv, -0.1, 0.1)
        v = v + dv
        if np.max(np.abs(dv)) < 1e-12:
            break
    return v

def transient(npe, tau=45e-9, T=1.5e-6, dt=0.5e-9, vth=0.05):
    """npe = fotoelettroni; Q = npe * 0.5 pC (SiPM gain ~3e6)."""
    Qtot = npe * 0.5e-12
    v = solve_dc()
    v_dc = v.copy()
    steps = int(T / dt)
    t_axis = np.zeros(steps); out = np.zeros((steps, N))
    comp = np.zeros(steps); le = np.zeros(steps); qb = np.zeros(steps)
    t0 = 100e-9
    q_state = 0.0     # uscita comparatore (0/3.3)
    v_le = 0.0        # tensione su LE (rete C9/R16)
    R16v, C9v = 1e3, 100e-12
    hyst = 0.002      # isteresi interna MAX961 (+-2 mV)
    for k in range(steps):
        t = (k + 1) * dt
        i_in = (Qtot / tau) * np.exp(-(t - t0) / tau) if t >= t0 else 0.0
        vn = v.copy()
        for _ in range(60):
            f, J = residual_jacobian(vn, v, dt, i_in)
            dv = np.linalg.solve(J, -f)
            dv = np.clip(dv, -0.3, 0.3)
            vn += dv
            if np.max(np.abs(dv)) < 1e-9:
                break
        # comparatore MAX961: E (nodo 5) vs soglia; latch se LE alto
        q_prev = q_state
        latched = v_le > VCC / 2
        if not latched:
            if v[5] > vth + hyst:
                q_state = VCC
            elif v[5] < vth - hyst:
                q_state = 0.0
        # rete LE: C9 tra Q e LE, R16 a GND: dv_le = dVq - v_le*dt/(R16*C9)
        v_le += (q_state - q_prev) - v_le * dt / (R16v * C9v)
        v_le = max(min(v_le, VCC), -VCC)
        v = vn
        t_axis[k] = t; out[k] = v; comp[k] = q_state; le[k] = v_le
        qb[k] = VCC - q_state
    return t_axis, out, comp, le, v_dc

# ------------------------- run -------------------------
def _main():
    vdc = solve_dc()
    print("Punto di lavoro DC:")
    names = ["SIG", "B(Q1)", "C(Q1)/B(Q2)", "E(Q2)", "D(Q2 coll)", "E(comp in)"]
    for n, val in zip(names, vdc):
        print(f"  {n:14s} = {val:7.3f} V")
    ic1 = (VCC - vdc[2]) / R12
    ic2 = vdc[4] / R14
    print(f"  Ic(Q1) ~ {ic1*1e3:.2f} mA, Ic(Q2) ~ {ic2*1e3:.2f} mA")

    fig, axes = plt.subplots(3, 2, figsize=(13, 9))
    fig.suptitle("Riv. Cosmici 2024 - catena di segnale (soglia 50 mV)", fontsize=13)

    cases = [(10, "tab:blue"), (50, "tab:orange"), (200, "tab:green")]
    peak_D = {}
    for npe, col in cases:
        t, vv, comp, le, _ = transient(npe, vth=0.05)
        tus = t * 1e9
        dV = vv - vdc
        axes[0, 0].plot(tus, dV[:, 0] * 1e3, col, label=f"{npe} p.e.")
        axes[0, 1].plot(tus, dV[:, 1] * 1e3, col)
        axes[1, 0].plot(tus, dV[:, 2] * 1e3, col)
        axes[1, 1].plot(tus, dV[:, 5] * 1e3, col)
        axes[2, 0].plot(tus, comp, col)
        axes[2, 1].plot(tus, le, col)
        peak_D[npe] = dV[:, 5].max()

    axes[0, 0].set_title("SIG (ingresso, ac)"); axes[0, 0].set_ylabel("mV")
    axes[0, 1].set_title("Base Q1 (ac)")
    axes[1, 0].set_title("Collettore Q1 / base Q2 (ac)"); axes[1, 0].set_ylabel("mV")
    axes[1, 1].set_title("Ingresso comparatore (nodo E)")
    axes[2, 0].set_title("Uscita comparatore Q"); axes[2, 0].set_ylabel("V")
    axes[2, 0].set_xlabel("ns")
    axes[2, 1].set_title("LE (latch, rete C9/R16)"); axes[2, 1].set_xlabel("ns")
    axes[0, 0].legend()
    for ax in axes.flat:
        ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("sim_catena.png", dpi=110)
    print("salvato sim_catena.png")
    print("picchi al comparatore:", {k: f"{v*1e3:.1f} mV" for k, v in peak_D.items()})

    # curva ampiezza vs n.p.e. + soglia
    npes = [2, 5, 10, 20, 50, 100, 200, 400]
    peaks = []
    for npe in npes:
        t, vv, comp, le, _ = transient(npe, T=0.8e-6)
        peaks.append((vv[:, 5] - vdc[5]).max() * 1e3)
    plt.figure(figsize=(7, 4.5))
    plt.loglog(npes, peaks, "o-")
    plt.axhline(2, color="r", ls="--", label="soglia min (~2 mV)")
    plt.axhline(1290, color="g", ls="--", label="soglia max (~1,29 V)")
    plt.xlabel("fotoelettroni (0,5 pC/p.e.)"); plt.ylabel("picco al comparatore [mV]")
    plt.title("Ampiezza al comparatore vs carica SiPM")
    plt.grid(True, which="both", alpha=0.3); plt.legend()
    plt.tight_layout(); plt.savefig("sim_ampiezze.png", dpi=110)
    print("salvato sim_ampiezze.png")
    print("ampiezze:", dict(zip(npes, [f'{p:.1f} mV' for p in peaks])))

if __name__ == "__main__":
    _main()
