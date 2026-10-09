# -*- coding: utf-8 -*-
"""Simula il FRONT-END partendo dalla netlist ESTRATTA dal .kicad_sch
(netlist_from_kicad), non da valori scritti a mano. Solver MNA generico:
costruisce le equazioni dai componenti e dalle connessioni trovate nel file.

Poi confronta il risultato con il simulatore di riferimento (sim_catena):
se coincidono, la simulazione e' davvero guidata dallo schema -> un errore
nello schema (valore o cablaggio) cambierebbe il risultato.
"""
import re, math
import numpy as np
from netlist_from_kicad import extract, RAILS

VT = 0.02585
def rval(s):
    s = s.strip().replace('F','').replace(' ','')
    m = re.match(r'^([\d.]+)([kRnpuM]?)(\d*)$', s)
    if not m: return None
    base, suf, dec = m.groups()
    mult = {'':1,'R':1,'k':1e3,'M':1e6,'n':1e-9,'p':1e-12,'u':1e-6}[suf]
    return float(base + ('.'+dec if dec else '')) * mult

# modelli BJT per valore (tipici)
BJTMODEL = {
    "BFR93A":  dict(IS=50e-15, BF=90, BR=4, pnp=False),
    "MMBTH81": dict(IS=50e-15, BF=70, BR=4, pnp=True),
    "MMBT2222A": dict(IS=1e-14, BF=200, BR=4, pnp=False),
    "2N2222":  dict(IS=1e-14, BF=200, BR=4, pnp=False),
}

def build_frontend(path):
    comps, nets, cpn = extract(path)
    # net del SiPM = net collegato a J1 pin 1 (segnale)
    sipm_net = cpn.get(("J1","1"))
    # attraversa R/C/Q dal SiPM, senza passare per i rail, per raccogliere i nodi
    dev_of_net = {}
    for ref, c in comps.items():
        lib = c["lib"]
        if lib in ("R","C","NPN","PNP") or c["value"] in BJTMODEL:
            for num in c["pins"]:
                dev_of_net.setdefault(cpn[(ref,num)], []).append(ref)
    frontier = [sipm_net]; nodes=set(); devices=set()
    while frontier:
        net = frontier.pop()
        if net in nodes or net in RAILS:
            if net in RAILS: continue
        nodes.add(net)
        for ref in dev_of_net.get(net, []):
            devices.add(ref)
            for num in comps[ref]["pins"]:
                nn = cpn[(ref,num)]
                if nn not in nodes and nn not in RAILS:
                    frontier.append(nn)
    # ferma la crescita ai pin di IC (comparatore): CMP_IN resta un nodo foglia
    node_list = sorted(n for n in nodes if n not in RAILS)
    idx = {n:i for i,n in enumerate(node_list)}
    out_net = cpn.get(("U3","1")) or "CMP_IN"    # ingresso + comparatore
    # lista componenti da stampare
    R=[]; C=[]; Q=[]
    for ref in devices:
        c=comps[ref]; lib=c["lib"]; val=c["value"]
        p={num:cpn[(ref,num)] for num in c["pins"]}
        if lib=="R" or (val and val.replace(' ','')[0].isdigit() and lib=="R"):
            R.append((ref, rval(val), p['1'], p['2']))
        elif lib=="C":
            C.append((ref, rval(val), p['1'], p['2']))
        elif lib in ("NPN","PNP") or val in BJTMODEL:
            m=BJTMODEL.get(val, dict(IS=50e-15,BF=100,BR=4,pnp=(lib=="PNP")))
            Q.append((ref, m, p['1'], p['2'], p['3']))   # B,E,C
    return dict(nodes=node_list, idx=idx, R=R, C=C, Q=Q, sipm=sipm_net, out=out_net,
                comps=comps, cpn=cpn)

def simulate(fe, npe=180, T=1.5e-6, dt=0.5e-9):
    idx=fe["idx"]; NN=len(idx)
    def ni(net): return idx.get(net, None)   # None = rail
    def railV(net): return RAILS[net]
    def stampR(f,J,v,ref,R,a,b):
        g=1.0/R; ia=ni(a); ib=ni(b)
        va=v[ia] if ia is not None else railV(a)
        vb=v[ib] if ib is not None else railV(b)
        i=g*(va-vb)
        if ia is not None: f[ia]+=i; J[ia,ia]+=g
        if ib is not None: f[ib]-=i; J[ib,ib]+=g
        if ia is not None and ib is not None: J[ia,ib]-=g; J[ib,ia]-=g
    def stampC(f,J,v,vp,dt,C,a,b):
        g=C/dt; ia=ni(a); ib=ni(b)
        va=v[ia] if ia is not None else railV(a); vb=v[ib] if ib is not None else railV(b)
        va0=vp[ia] if ia is not None else railV(a); vb0=vp[ib] if ib is not None else railV(b)
        i=g*((va-vb)-(va0-vb0))
        if ia is not None: f[ia]+=i; J[ia,ia]+=g
        if ib is not None: f[ib]-=i; J[ib,ib]+=g
        if ia is not None and ib is not None: J[ia,ib]-=g; J[ib,ia]-=g
    def stampQ(f,J,v,m,B,E,Cc):
        s=-1.0 if m["pnp"] else 1.0
        iB=ni(B); iE=ni(E); iC=ni(Cc)
        vB=v[iB] if iB is not None else railV(B)
        vE=v[iE] if iE is not None else railV(E)
        vC=v[iC] if iC is not None else railV(Cc)
        vbe=s*(vB-vE); vbc=s*(vB-vC)
        vbe=min(vbe,0.95); vbc=min(vbc,0.95)
        IS,BF,BR=m["IS"],m["BF"],m["BR"]
        e1=math.exp(vbe/VT); e2=math.exp(vbc/VT)
        ic=IS*(e1-e2)-IS/BR*(e2-1); ib=IS/BF*(e1-1)+IS/BR*(e2-1)
        gf=IS*e1/VT; gr=IS*e2/VT
        # correnti reali (segno s) iniettate: base=+ib, collettore=+ic, emettitore=-(ib+ic)
        IBr=s*ib; ICr=s*ic; IEr=-(IBr+ICr)
        # derivate rispetto a vB,vE,vC (chain: dvbe/dvB=s, dvbe/dvE=-s, dvbc/dvB=s, dvbc/dvC=-s)
        dib_dvbe=gf/BF; dib_dvbc=gr/BR
        dic_dvbe=gf;    dic_dvbc=-gr-gr/BR
        # d(IBr)/dvB = s*(dib/dvbe*s + dib/dvbc*s) = dib_dvbe+dib_dvbc ; /dvE = -(dib_dvbe); /dvC=-(dib_dvbc)
        def add(iN, cur, dvB,dvE,dvC):
            if iN is None: return
            f[iN]+=cur
            if iB is not None: J[iN,iB]+=dvB
            if iE is not None: J[iN,iE]+=dvE
            if iC is not None: J[iN,iC]+=dvC
        add(iB, IBr, dib_dvbe+dib_dvbc, -dib_dvbe, -dib_dvbc)
        add(iC, ICr, dic_dvbe+dic_dvbc, -dic_dvbe, -dic_dvbc)
        add(iE, IEr, -(dib_dvbe+dib_dvbc+dic_dvbe+dic_dvbc),
                     (dib_dvbe+dic_dvbe), (dib_dvbc+dic_dvbc))
    def resid(v,vp,dt,iin,f,J):
        f[:]=0; J[:]=0
        for ref,R,a,b in fe["R"]: stampR(f,J,v,ref,R,a,b)
        for ref,Cv,a,b in fe["C"]: stampC(f,J,v,vp,dt,Cv,a,b)
        for ref,m,B,E,Cc in fe["Q"]: stampQ(f,J,v,m,B,E,Cc)
        # capacita' parassite piccole per stabilita'
        for i in range(NN):
            g=0.5e-12/dt; f[i]+=g*(v[i]-vp[i]); J[i,i]+=g
        si=idx[fe["sipm"]]; f[si]-=iin
    # DC
    v=np.zeros(NN)
    for _ in range(300):
        f=np.zeros(NN); J=np.zeros((NN,NN)); resid(v,v,1.0,0.0,f,J)
        dv=np.clip(np.linalg.solve(J,-f),-0.1,0.1); v+=dv
        if np.max(np.abs(dv))<1e-12: break
    vdc=v.copy()
    # transient
    TAU=45e-9; Q=npe*0.5e-12; t0=100e-9; steps=int(T/dt)
    oi=idx[fe["out"]]; peak=0; vp=v.copy()
    for k in range(steps):
        t=(k+1)*dt; iin=(Q/TAU)*math.exp(-(t-t0)/TAU) if t>=t0 else 0.0
        for _ in range(40):
            f=np.zeros(NN); J=np.zeros((NN,NN)); resid(v,vp,dt,iin,f,J)
            dv=np.clip(np.linalg.solve(J,-f),-0.3,0.3); v+=dv
            if np.max(np.abs(dv))<1e-9: break
        vp=v.copy()
        peak=max(peak, v[oi]-vdc[oi])
    return vdc, idx, peak

if __name__ == "__main__":
    import sim_catena as SC
    fe = build_frontend("../hardware/riv_cosmici.kicad_sch")
    print("=== netlist front-end estratta dal .kicad_sch ===")
    print("nodi:", fe["nodes"])
    print("R:", [(r[0],r[1]) for r in fe["R"]])
    print("C:", [(c[0],c[1]) for c in fe["C"]])
    print("Q:", [(q[0],"PNP" if q[1]["pnp"] else "NPN","B=%s E=%s C=%s"%(q[2],q[3],q[4])) for q in fe["Q"]])
    print("ingresso SiPM =", fe["sipm"], " uscita misurata =", fe["out"])
    vdc, idx, peak = simulate(fe, npe=180)
    print("\n=== confronto punto di lavoro DC ===")
    ref = SC.solve_dc()
    names={"N2":"B(Q1)","N3":"C(Q1)","N4":"E(Q2)","N5":"D(Q2)"}
    # mappa i nodi estratti a quelli del riferimento per confronto
    print(f"  nodo estratto     schema[V]   sim_catena[V]")
    pairs=[("N2",1),("N3",2),("N4",3),("N5",4)]
    ok=True
    for nn,ri in pairs:
        vs=vdc[idx[nn]]; vr=ref[ri]
        d=abs(vs-vr); ok&= d<0.02
        print(f"  {nn} ({names[nn]:6s})   {vs:7.3f}     {vr:7.3f}   {'OK' if d<0.02 else 'DIVERSO'}")
    # picco al comparatore
    _,_,_,_,vdc_ref = SC.transient(180, dt=0.5e-9)
    tarr,vv,comp,le,_ = SC.transient(180, dt=0.5e-9)
    peak_ref=(vv[:,5]-vdc_ref[5]).max()
    print(f"\n  picco al comparatore: schema {peak*1e3:.0f} mV | sim_catena {peak_ref*1e3:.0f} mV | "
          f"{'OK' if abs(peak-peak_ref)<0.02 else 'DIVERSO'}")
    print("\nRISULTATO:", "la simulazione dallo schema COINCIDE col riferimento" if ok else "DISCREPANZA")


# ============ estensione: uscita verso Raspberry Pi dallo schema ============
# Il buffer discreto a 2 transistor e' stato sostituito da U9 74LVC1G17
# (alimentato a +3V3). La simulazione della scheda intera e' in
# ltspice/ (verifica_ltspice.py); qui si controlla dallo schema KiCad che lo
# stadio d'uscita sia collegato come previsto.
def check_output_stage(path):
    comps, nets, cpn = extract(path)
    exp = {("U9", "2"): "CMP_Q", ("U9", "3"): "GND", ("U9", "5"): "+3V3",
           ("J4", "2"): "GND", ("U4", "3"): "CMP_Q", ("U4", "2"): "+5V"}
    ok = True
    for (ref, pin), net in exp.items():
        got = cpn.get((ref, pin))
        good = got == net
        ok &= good
        print(f"  {ref}.{pin:2s} -> {got!s:8s} (atteso {net:6s}) {'OK' if good else 'ERRATO'}")
    y = cpn[("U9", "4")]
    out = cpn[("J4", "1")]
    r23 = {cpn[("R23", "1")], cpn[("R23", "2")]}
    good = r23 == {y, out} and comps["R23"]["value"] == "33R"
    ok &= good
    print(f"  U9.Y -> R23 ({comps['R23']['value']}) -> J4.1      {'OK' if good else 'ERRATO'}")
    # nessun pin dello stadio d'uscita verso +5V oltre al driver TTL U4
    on5 = [r for (r, p), n in cpn.items() if n == "+5V" and r in ("U9", "R23", "J4")]
    ok &= not on5
    print("  niente +5V verso J4 (GPIO del Pi a 3,3 V):", "OK" if not on5 else f"ERRATO {on5}")
    return ok

if __name__ == "__main__" and "--uscita" in __import__("sys").argv:
    print("=== stadio d'uscita estratto dal .kicad_sch ===")
    ok = check_output_stage("../hardware/riv_cosmici.kicad_sch")
    print("\nRISULTATO:", "OK" if ok else "ERRORI")
