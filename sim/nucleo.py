"""Núcleo del simulador dinámico (numba). Ver docs/SIMULACION_DINAMICA.md para el modelo completo.

Planta: cuerpo rígido plano (x, y, guiñada) con el CG adelantado al eje; dos llantas motrices con
fricción de Coulomb regularizada (la fuerza total de cada llanta nunca supera mu·N: círculo de fricción);
apoyo de bola sin fuerza lateral (solo rodadura); transferencia de carga longitudinal y lateral;
dinámica de cada rueda con la inercia del rotor reflejada; motor DC lineal con decaimiento lento;
batería con resistencia interna. Sensores con la geometría real de la barra, mancha óptica, ruido
y huecos; control con periodo y latencia (lectura + cálculo)."""
import math

import numpy as np
from numba import njit

DS = 0.001
G = 9.81

# índices del vector de parámetros de la planta
(I_M, I_XCG, I_H, I_IZ, I_L, I_W, I_R, I_XA, I_XS, I_FS, I_MU, I_CRR, I_EPS, I_J,
 I_VOC, I_RINT, I_ILOG, I_IFAN, I_RM, I_KE, I_KT, I_I0, I_LIMV,
 I_MANCHA, I_RUIDO, I_UMBRAL, I_TLECT, I_TCTRL, I_TPERD, I_IOCP, I_GRUIDO, I_GSESGO, I_ANCHO,
 I_KEL, I_KER, I_Y0, I_PSI0, I_TMAX, I_DT, I_VMEDIDO, I_MUK, I_VSTR, I_CPR) = range(43)
NP = 43

# controladores
C_LAZO_ABIERTO = 0  # pruebas: ciclos fijos (prm: izq, der, t_cambio, izq2, der2)
C_PD = 1      # C1: PD directo sobre el ciclo
C_SF = 2      # C2/C3: perfil de velocidad + FF de motor + persecución pura + PD

# motivos de falla
OK, SALIDA, DETENIDO, SENTIDO, VUELCO = 0, 1, 2, 3, 4
N_RES = 20       # tamaño del vector de resultados


@njit(cache=True)
def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


@njit(cache=True)
def _ff(v, a, vbat, P, prm_ffacel):
    # Feed-forward del firmware con el motor NOMINAL: V = Ke·ω + R·(I0 + m·a·r/(2Kt))
    r = P[I_R]
    w = v / r
    i_a = P[I_M] * a * r / (2.0 * P[I_KT]) if prm_ffacel else 0.0
    i0 = math.copysign(P[I_I0], w) if abs(w) > 1e-3 else 0.0
    return (P[I_KE] * w + P[I_RM] * (i0 + i_a)) / vbat


@njit(cache=True)
def paso_sf(ST, e_use, Tc, vbat, P, prm, dL, dR, gz, wLm=0.0, wRm=0.0):
    """Controlador C2/C3 (traducción del firmware sf_logica.cpp ControlSF::paso, sin inversión ni
    freno activo). ST = [e_f, de_f, k_f, km_f, v_cmd, inicial]. prm = v_max, a_lat, a_lon, k_pp, kp, kd,
    tau_d, tau_k, fuente (0 error = C2, 1 modelo del motor = C3m, 2 giroscopio = C3g, 3 encoders = C3e).
    wLm, wRm: velocidad angular de cada rueda medida con los encoders (rad/s), solo para la fuente 3."""
    v_max = prm[0]; a_lat = prm[1]; a_lon = prm[2]; k_pp = prm[3]; kp = prm[4]; kd = prm[5]
    tau_d = prm[6]; tau_k = prm[7]; fuente = int(prm[8])
    L = P[I_L]; W = P[I_W]; rw = P[I_R]
    if ST[5] > 0.5:
        ST[0] = e_use; ST[5] = 0.0
    de = (e_use - ST[0]) / Tc
    ST[0] = e_use
    ST[1] += Tc / (tau_d + Tc) * (de - ST[1])
    k_inst = 2.0 * e_use / (L * L)
    ST[2] += Tc / (tau_k + Tc) * (k_inst - ST[2])
    kmag = abs(ST[2])
    vref = max(ST[4], 0.1)
    if fuente == 1:
        wLe = (dL * vbat - P[I_RM] * P[I_I0]) / P[I_KE]
        wRe = (dR * vbat - P[I_RM] * P[I_I0]) / P[I_KE]
        km = (wRe - wLe) * rw / (W * vref)
        ST[3] += Tc / (tau_k + Tc) * (km - ST[3])
        kmag = max(kmag, abs(ST[3]))
    elif fuente == 2:
        km = gz / vref
        ST[3] += Tc / (tau_k + Tc) * (km - ST[3])
        kmag = max(kmag, abs(ST[3]))
    elif fuente == 3:
        km = (wRm - wLm) * rw / (W * vref)
        ST[3] += Tc / (tau_k + Tc) * (km - ST[3])
        kmag = max(kmag, abs(ST[3]))
    v_obj = min(v_max, math.sqrt(a_lat / max(kmag, 1e-6)))
    paso = _clamp(v_obj - ST[4], -a_lon * Tc, a_lon * Tc)
    ST[4] += paso
    a_cmd = paso / Tc
    v = max(ST[4], 0.05)
    lim = min(vbat, P[I_LIMV]) / vbat
    base = _ff(v, a_cmd, vbat, P, True)
    dv_pp = k_pp * 2.0 * v * e_use * W / (L * L)
    delta = (_ff(v + dv_pp * 0.5, 0.0, vbat, P, False) - _ff(v - dv_pp * 0.5, 0.0, vbat, P, False)) \
        + kp * e_use + kd * ST[1]
    nL = base + delta * 0.5; nR = base - delta * 0.5
    hi = max(nL, nR)
    if hi > lim:
        nL -= hi - lim; nR -= hi - lim
    piso = prm[9] if prm.shape[0] > 9 else 0.0   # ciclo mínimo permitido en la rueda interior (0 = sin inversión)
    bajo = min(nL, nR)
    if bajo < piso:
        nL -= bajo - piso; nR -= bajo - piso
    return _clamp(nL, -lim, lim), _clamp(nR, -lim, lim)


@njit(cache=True)
def simular(tx, ty, trumbo, thueco, P, sx, sy, ctrl, prm, seed, traza):
    np.random.seed(seed)
    n_tr = tx.shape[0]
    Ltr = n_tr * DS
    ns = sx.shape[0]
    m = P[I_M]; xcg = P[I_XCG]; h = P[I_H]; Iz = P[I_IZ]; L = P[I_L]; W = P[I_W]; rw = P[I_R]
    b = P[I_XA]; xs_ = P[I_XS]; Fs = P[I_FS]; mu = P[I_MU]; crr = P[I_CRR]; eps = P[I_EPS]; J = P[I_J]
    Voc = P[I_VOC]; Rint = P[I_RINT]; Ilog = P[I_ILOG]; Ifan = P[I_IFAN]
    Rm = P[I_RM]; Kt = P[I_KT]; I0 = P[I_I0]; limV = P[I_LIMV]
    KeL = P[I_KE] * P[I_KEL]; KeR = P[I_KE] * P[I_KER]
    mancha = P[I_MANCHA]; ruido = P[I_RUIDO]; umbral = P[I_UMBRAL]; medio = P[I_ANCHO] / 2
    t_lect = P[I_TLECT]; Tc = P[I_TCTRL]; t_perd = P[I_TPERD]; Iocp = P[I_IOCP]
    dt = P[I_DT]; tmax = P[I_TMAX]
    muk = P[I_MUK]; vstr = P[I_VSTR]

    # pose inicial: barra sobre la línea de salida (índice 0), eje detrás
    ia = (n_tr - int(round((L + 0.005) / DS))) % n_tr
    psi = trumbo[ia] + P[I_PSI0]
    nx, ny = -math.sin(trumbo[ia]), math.cos(trumbo[ia])
    Ax = tx[ia] + nx * P[I_Y0]; Ay = ty[ia] + ny * P[I_Y0]
    X = Ax + xcg * math.cos(psi); Y = Ay + xcg * math.sin(psi)
    vx = 0.0; vy = 0.0; wz = 0.0; wl = 0.0; wr = 0.0; Nc = 0.0
    ax_ = 0.0; ay_ = 0.0
    Vbus = Voc; Ibus = Ilog + Ifan
    idx = ia; prog = 0; prog_max = 0
    meta = int(round((L + 0.005 + Ltr + 0.02) / DS))

    # control
    dL = 0.0; dR = 0.0; pend_L = 0.0; pend_R = 0.0; t_apl = 1e9
    t_ctrl = 0.0
    e_f = 0.0; v_cmd = 0.0; inicial = True
    ST = np.zeros(6); ST[5] = 1.0
    e_ult = 0.0; t_sin = 0.0; parado = False
    sesgo = P[I_GSESGO] * (2.0 * np.random.random() - 1.0)
    lect = np.zeros(ns)
    t_fuera = 0.0
    # encoders: ángulo de cada rueda y cuentas en la última lectura (CPR = cuentas por vuelta de RUEDA)
    cpr = P[I_CPR]
    thL = 0.0; thR = 0.0; cL0 = 0.0; cR0 = 0.0; wLm = 0.0; wRm = 0.0; t_enc = 0.0
    # métricas
    vmax = 0.0; Imax = 0.0; n_ocp = 0; Q = 0.0; E = 0.0; Vmin = Voc; emax = 0.0
    n_sat = 0; n_ticks = 0; deslmax = 0.0; motivo = -1; t_fin = tmax
    ntr = int(tmax / Tc) + 2 if traza else 1
    T = np.zeros((ntr, 16))
    k_tr = 0

    t = 0.0
    while t < tmax:
        c = math.cos(psi); s = math.sin(psi)
        Ax = X - xcg * c; Ay = Y - xcg * s
        # ---------------- avance sobre la pista (punto más cercano al eje)
        best = 1e9; bj = 0
        for k in range(-5, 21):
            j = (idx + k) % n_tr
            d2 = (tx[j] - Ax) ** 2 + (ty[j] - Ay) ** 2
            if d2 < best:
                best = d2; bj = k
        idx = (idx + bj) % n_tr
        prog += bj
        if prog > prog_max:
            prog_max = prog
        if prog >= meta:
            motivo = OK; t_fin = t
            break
        if math.sqrt(best) > 0.12 and ctrl != C_LAZO_ABIERTO:
            motivo = SALIDA; t_fin = t
            break
        if prog_max - prog > 50 and ctrl != C_LAZO_ABIERTO:
            motivo = SENTIDO; t_fin = t
            break

        # ---------------- salida pendiente: se aplica ANTES de calcular la siguiente (latencia ≥ periodo)
        if t >= t_apl:
            dL = pend_L; dR = pend_R; t_apl = 1e9
        # ---------------- control (periodo Tc, salida aplicada tras t_lect)
        if t >= t_ctrl:
            if t_apl < 1e8:          # el MCU aplica la salida anterior al terminar su lectura, antes de la siguiente
                dL = pend_L; dR = pend_R; t_apl = 1e9
            t_ctrl += Tc
            n_ticks += 1
            if cpr > 0.0:            # velocidad por diferencia de cuentas entre lecturas (cuantización real)
                cL = math.floor(thL * cpr / (2.0 * math.pi)); cR = math.floor(thR * cpr / (2.0 * math.pi))
                dtt = t - t_enc if t > t_enc else Tc
                wLm = (cL - cL0) * 2.0 * math.pi / cpr / dtt; wRm = (cR - cR0) * 2.0 * math.pi / cpr / dtt
                cL0 = cL; cR0 = cR; t_enc = t
            sobre_linea = False
            for i in range(ns):
                wx = Ax + sx[i] * c - sy[i] * s
                wy = Ay + sx[i] * s + sy[i] * c
                bd = 1e9; bjj = 0
                for k in range(-80, 300, 2):
                    j = (idx + k) % n_tr
                    d2 = (tx[j] - wx) ** 2 + (ty[j] - wy) ** 2
                    if d2 < bd:
                        bd = d2; bjj = j
                # refinamiento a 1 mm
                j0 = bjj
                for k in range(-2, 3):
                    j = (j0 + k) % n_tr
                    d2 = (tx[j] - wx) ** 2 + (ty[j] - wy) ** 2
                    if d2 < bd:
                        bd = d2; bjj = j
                d = math.sqrt(bd)
                cob = 0.0 if thueco[bjj] else _clamp((medio - d) / (2.0 * mancha) + 0.5, 0.0, 1.0)
                if d <= medio or thueco[bjj]:
                    sobre_linea = True
                lect[i] = _clamp(cob + ruido * np.random.standard_normal(), 0.0, 1.0)
            # estimación (igual al firmware, con coordenada lateral de cada sensor)
            sw = 0.0; sm = 0.0
            w0 = 0.0; wn = 0.0
            for i in range(ns):
                w = _clamp((lect[i] - umbral) / (1.0 - umbral), 0.0, 1.0)
                sw += w; sm += w * (-sy[i])
                if i == 0:
                    w0 = w
                if i == ns - 1:
                    wn = w
            visible = sw >= 0.5
            e_med = sm / sw if visible else 0.0
            borde = visible and (w0 > 0.3 or wn > 0.3)
            if not sobre_linea:
                t_fuera += Tc
            else:
                t_fuera = 0.0
            if t_fuera > 0.10 and ctrl != C_LAZO_ABIERTO:
                motivo = SALIDA; t_fin = t
                break

            vbat = Vbus * P[I_VMEDIDO]
            # ---- envoltura de línea perdida (firmware actualizar)
            if visible:
                e_use = e_med; e_ult = e_med; t_sin = 0.0
            else:
                t_sin += Tc; e_use = e_ult
                if t_sin > t_perd:
                    parado = True
            if ctrl == C_LAZO_ABIERTO:
                nL = prm[0] if t < prm[2] else prm[3]
                nR = prm[1] if t < prm[2] else prm[4]
            elif parado:
                nL = 0.0; nR = 0.0
            elif ctrl == C_PD:
                b0 = prm[0]; kfr = prm[1]; eref = prm[2]; kp = prm[3]; kd = prm[4]; rmin = prm[5]
                de = 0.0 if inicial else (e_use - e_f) / Tc
                inicial = False
                e_f = e_use
                u = _clamp(kp * e_use + kd * de, -1.0, 1.0)
                base = b0 * max(0.3, 1.0 - kfr * min(1.0, abs(e_use) / eref))
                nL = base + u; nR = base - u
                hi = max(nL, nR)
                if hi > 1.0:
                    nL -= hi - 1.0; nR -= hi - 1.0
                lim = min(1.0, limV / vbat)
                nL = _clamp(nL, rmin, 1.0) * lim; nR = _clamp(nR, rmin, 1.0) * lim
            else:
                gz = wz + sesgo + P[I_GRUIDO] * np.random.standard_normal()
                nL, nR = paso_sf(ST, e_use, Tc, vbat, P, prm, dL, dR, gz, wLm, wRm)
                v_cmd = ST[4]
            if abs(nL) >= 0.999 * min(1.0, limV / vbat) or abs(nR) >= 0.999 * min(1.0, limV / vbat):
                n_sat += 1
            pend_L = nL; pend_R = nR; t_apl = t + t_lect
            if visible and abs(e_med) > emax:
                emax = abs(e_med)
            if traza and k_tr < ntr:
                T[k_tr, 0] = t; T[k_tr, 1] = Ax; T[k_tr, 2] = Ay; T[k_tr, 3] = psi
                T[k_tr, 4] = vx; T[k_tr, 5] = e_use; T[k_tr, 6] = dL; T[k_tr, 7] = dR
                T[k_tr, 8] = v_cmd; T[k_tr, 9] = Vbus; T[k_tr, 10] = prog * DS; T[k_tr, 11] = wz
                T[k_tr, 12] = wl * rw; T[k_tr, 13] = wr * rw; T[k_tr, 14] = vy; T[k_tr, 15] = Nc
                k_tr += 1
        # ---------------- planta
        Ntot = m * G + Fs
        Nc = (m * G * xcg + Fs * xs_ - m * ax_ * h) / b
        Nd = Ntot - Nc
        dN = m * ay_ * h / W
        NL = Nd * 0.5 - dN; NR = Nd * 0.5 + dN
        if Nc < 0.0 or NL < 0.0 or NR < 0.0:
            motivo = VUELCO; t_fin = t
            break
        # velocidades de los puntos de contacto (marco del cuerpo, desde el CG)
        vxl = vx - wz * W * 0.5; vyl = vy - wz * xcg
        vxr = vx + wz * W * 0.5; vyr = vy - wz * xcg
        vxc = vx; vyc = vy + wz * (b - xcg)
        sxl = vxl - wl * rw; sxr = vxr - wr * rw
        ml = math.sqrt(sxl * sxl + vyl * vyl + eps * eps)
        mr = math.sqrt(sxr * sxr + vyr * vyr + eps * eps)
        # μ baja del estático al cinético cuando la llanta desliza (Stribeck simplificado)
        mul = mu * (muk + (1.0 - muk) * math.exp(-math.sqrt(sxl * sxl + vyl * vyl) / vstr))
        mur = mu * (muk + (1.0 - muk) * math.exp(-math.sqrt(sxr * sxr + vyr * vyr) / vstr))
        FxL = -mul * NL * sxl / ml; FyL = -mul * NL * vyl / ml
        FxR = -mur * NR * sxr / mr; FyR = -mur * NR * vyr / mr
        des = max(math.sqrt(sxl * sxl + vyl * vyl), math.sqrt(sxr * sxr + vyr * vyr))
        if des > deslmax:
            deslmax = des
        # rodadura (llantas y apoyo)
        rrl = -crr * NL * vxl / math.sqrt(vxl * vxl + eps * eps)
        rrr = -crr * NR * vxr / math.sqrt(vxr * vxr + eps * eps)
        mc = math.sqrt(vxc * vxc + vyc * vyc + eps * eps)
        Fcx = -crr * Nc * vxc / mc; Fcy = -crr * Nc * vyc / mc
        Fx = FxL + FxR + rrl + rrr + Fcx
        Fy = FyL + FyR + Fcy
        Mz = (-xcg) * FyL - (W * 0.5) * (FxL + rrl) + (-xcg) * FyR + (W * 0.5) * (FxR + rrr) + (b - xcg) * Fcy
        # motores
        VaL = _clamp(dL * Vbus, -limV, limV); VaR = _clamp(dR * Vbus, -limV, limV)
        IL = (VaL - KeL * wl) / Rm; IR = (VaR - KeR * wr) / Rm
        TL = Kt * (IL - I0 * math.tanh(wl / 2.0)); TR = Kt * (IR - I0 * math.tanh(wr / 2.0))
        aI = max(abs(IL), abs(IR))
        if aI > Imax:
            Imax = aI
        if aI > Iocp:
            n_ocp += 1
        # batería
        Ibus = (VaL / Vbus) * IL + (VaR / Vbus) * IR + Ilog + Ifan
        Vbus = Voc - Rint * Ibus
        if Vbus < Vmin:
            Vmin = Vbus
        Q += Ibus * dt; E += Vbus * Ibus * dt
        # integración semi-implícita
        wl += (TL - FxL * rw) / J * dt
        wr += (TR - FxR * rw) / J * dt
        thL += wl * dt; thR += wr * dt
        ax_ = Fx / m; ay_ = Fy / m
        vx += (ax_ + wz * vy) * dt
        vy += (ay_ - wz * vx) * dt
        wz += Mz / Iz * dt
        X += (vx * c - vy * s) * dt
        Y += (vx * s + vy * c) * dt
        psi += wz * dt
        if vx > vmax:
            vmax = vx
        t += dt

    if motivo == -1:
        motivo = DETENIDO; t_fin = t
    R = np.zeros(N_RES)
    R[0] = 1.0 if motivo == OK else 0.0
    R[1] = t_fin
    R[2] = (Ltr / t_fin) if motivo == OK else 0.0
    R[3] = vmax
    R[4] = motivo
    R[5] = prog * DS
    R[6] = emax
    R[7] = Imax
    R[8] = n_ocp
    R[9] = Q / 3.6          # mAh
    R[10] = E               # J
    R[11] = Vmin
    R[12] = n_sat / max(n_ticks, 1)
    R[13] = deslmax
    R[14] = Tc
    R[15] = 1.0 if parado else 0.0
    return R, T[:k_tr]
