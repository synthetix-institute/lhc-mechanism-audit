# LHC Physical Constructor

Verdict: `incomplete_direct_mechanism_branch`

Equation quantities fill mechanism slots; surrounding text identifies the physical regime. Branch closure additionally requires a source-local equation path between every adjacent slot.

| Mechanism condition | Status | Direct collider equations | Transfer candidates |
|---|---:|---:|---:|
| production threshold | `direct_mechanism_receipt` | 3 | 0 |
| survival against evaporation | `direct_mechanism_receipt` | 3 | 0 |
| stopping or capture in matter | `direct_mechanism_receipt` | 5 | 2 |
| net positive mass growth | `direct_mechanism_receipt` | 11 | 10 |
| growth on a relevant timescale | `direct_mechanism_receipt` | 1 | 3 |
| evasion of astronomical survival bounds | `candidate_transfer_only` | 0 | 1 |

## Equation Receipts

### production threshold

Required relation: $\sqrt{\hat s}=\sqrt{x_1x_2s}>M_{\min},\quad \sigma_{\rm form}\sim \pi r_s^2(M,M_D,n)$

Direct collider equations:

- `0806.3381` / `E00292`: `$\sigma_{BH}(M>M_{min}) = \sum_{ij} \int_{\tau_{min}}^1 \, d\tau \int_{\tau}^{1} \, \frac{dx}{x} f_i(x) f_j(\tau/x) \hat\sigma(\rshat) \; ,$`
- `0806.3381` / `E00295`: `$\tau=x_1 x_2 > \tau_{min}=M_{min}^2/(y^2 s) \; .$`
- `0806.3381` / `E00293`: `$\hat\sigma(\rshat)=\pi R^2(\rshat)/4$`

### survival against evaporation

Required relation: $\tau_{\rm evap}(M,M_D,n)>\tau_{\rm capture}$

Direct collider equations:

- `0901.2948` / `E00455`: `$\left.\frac{\ud M}{\ud t}\right|_{\rm evap} \simeq -\frac{g_{\rm eff}}{960\, \pi\,\lp}\left(\frac{\mpl}{\mc}\right)^3 \frac{M^2(t)}{\sqrt{M^2(t)+p^2(t)}} \ .$`
- `0901.2948` / `E00453`: `$\left.\frac{\ud M}{\ud t}\right|_{\rm evap} \simeq -\frac{1}{\gamma} \left.\frac{\ud M}{\ud \tau}\right|_{\rm evap} \ ,$`
- `0901.2948` / `E00411`: `$\frac{\ud M}{\ud\tau}=-{\cal A}_{(D)}\, {\cal L}_{(D)} \ ,$`

### stopping or capture in matter

Required relation: $L_{\rm stop}(M,v,\rho,\sigma)<L_{\rm body}\quad {\rm or}\quad \tau_{\rm capture}<\tau_{\rm escape}$

Direct collider equations:

- `0806.3381` / `E00124`: `$\left({dp\over dt}\right)_{ac} &=& n \pi[\bhm R({\sqrt s})]^2 \Delta p \;, \\ \left({dM\over dt}\right)_{ac} &=& n \pi [\bhm R({\sqrt s})]^2 \Delta M \;,$`
- `0806.3381` / `E00129`: `$\left({dp\over d\ell}\right)_{sc} = -{E^2\over s} \rho \int_{\cos\theta_c}^1 \, d\cos\theta {d\sigma\over d\cos\theta} \, 2\sin^2 {\theta\over 2}\ ,$`
- `0806.3381` / `E00130`: `$\left({dp\over d\ell}\right)_{sc} = -\cel\bhm^2 \pi \rho {E^2\over s} R^2(\sqrt s)\ .$`
- `0806.3381` / `E00149`: `${dp\over d\ell} &=& -(\cac-\cacm) \bhm^2 \pi\rho R^2\\ {dM\over d\ell}&=& \cacm \bhm^2 \pi\rho {R^2\over v}\ .$`
- `0806.3381` / `E00126`: `$\left({dp\over d\ell}\right)_{ac} = - (\cac-\cacm)\bhm^2 \pi\rho{E^2\over M^2} R^2(\sqrt s)\ ,$`

Cross-regime equation candidates:

- `0806.3381` / `E00208`: `$&&\int_r^\infty {dp\over \rho} = {c_s^2\over \Gamma-1}\Bigg\vert^\infty_r\quad,\quad \Gamma\neq1\\ && \int_r^\infty {dp\over \rho} = K\ln\left[{\rho(\infty)\over \rho(r)}\right]\quad,\quad \Gamma=1\ .$`
- `0806.3381` / `E00228`: `${dE\over dl} = \eta \sigma \rho\ ,$`

### net positive mass growth

Required relation: $\dot M_{\rm net}=\rho\,\sigma(M)\,v-P_{\rm evap}(M)/c^2>0$

Direct collider equations:

- `0806.3381` / `E00124`: `$\left({dp\over dt}\right)_{ac} &=& n \pi[\bhm R({\sqrt s})]^2 \Delta p \;, \\ \left({dM\over dt}\right)_{ac} &=& n \pi [\bhm R({\sqrt s})]^2 \Delta M \;,$`
- `0901.2948` / `E00457`: `$\frac{\ud p}{\ud t} &\!\!=\!\!& \frac{p(t)}{M(t)}\left.\frac{\ud M}{\ud t}\right|_{\rm evap} \nonumber \\ &\!\!\simeq\!\!& -\frac{g_{\rm eff}}{960\, \pi\,\lp} \left(\frac{\mpl}{M_c}\right)^3 \frac{M(t)\,p(t)}{\sqrt{M^2(t)+p^2(t)}} \ .$`
- `0806.3381` / `E00149`: `${dp\over d\ell} &=& -(\cac-\cacm) \bhm^2 \pi\rho R^2\\ {dM\over d\ell}&=& \cacm \bhm^2 \pi\rho {R^2\over v}\ .$`
- `0806.3381` / `E00127`: `$\left({dM\over d\ell}\right)_{ac} = \cacm \bhm^2 \pi\rho {E\over M} R^2(\sqrt s)\ ,$`
- `0901.2948` / `E00456`: `$\left.\frac{\ud M}{\ud t}\right|_{\rm acc} = \pi\, \rho\, v(t)\, \rem^2 \ ,$`
- `0806.3381` / `E00198`: `${dM\over dt} = \pi \rho R^2\ .$`
- `0901.2948` / `E00451`: `$\left.\frac{\ud M}{\ud t}\right|_{\rm acc} =\frac{4\, \pi\,\rho\,\lp^2}{v^3}\left(\frac{M}{\mpl}\right)^2 \ .$`
- `0901.2948` / `E00440`: `$\left.\frac{\ud M}{\ud t}\right|_{\rm acc} = \pi\,v\,\rho\,\reff^2 \ ,$`
- `0901.2948` / `E00452`: `$\frac{\ud M}{\ud t} = \left.\frac{\ud M}{\ud t}\right|_{\rm evap} +\left. \frac{\ud M}{\ud t}\right|_{\rm acc} \ .$`
- `0901.2948` / `E00413`: `$\frac{\ud M}{\ud\tau}\simeq f_{(4)}\,\frac{\mpl}{\lp}\,\left(\frac{\mpl}{M}\right)^2 \ ,$`
- `0806.3381` / `E00041`: `$\frac{dM}{dt} = \pi \rho \, v \, r_c^2(M) \; ,$`

Cross-regime equation candidates:

- `0806.3381` / `E00220`: `${dM\over dt} = \pi R_B^2(M) \rho(\infty) c_s(\infty) \lambda_D$`
- `0806.3381` / `E00080`: `$&&\left( \frac{dM}{dt} \right)_{EM} = \Delta^2 \, \pi \, \rho \, v_{EM} \; \arad^2 \, \left( \frac{M}{M_{a,D}} \right) ^{2/(D-1)} \\ &&\left( \frac{dM}{dt} \right)_{B} = \lambda_D\left[{D-3\over 4}\right]^{2/(D-3)} \, \pi \, \rho \, c_s \; \arad^2 \, \left( \frac{M}{M_{a,D}} \right) ^{2/(D-3)} \;.$`
- `0806.3381` / `E00215`: `${dM\over dt} = 4\pi \, \rho(r_s) \, r_s^2 \, c(r_s)\ .$`
- `0806.3381` / `E00070`: `${dM\over dt} = {\pi\lambda_Dc_s R_B^2 \rho} \ ,$`
- `0806.3381` / `E00203`: `$\frac{dM}{dt} = 4\pi \, \rho(r) \, r^2 \, v(r) = \mathrm{constant}$`
- `0806.3381` / `E00061`: `${dM\over dt} = {\pi \rho v} \rem^2\ .$`
- `0806.3381` / `E00039`: `${dM\over dt} = \pi r_c^2 F\ .$`
- `astro-ph/0105365` / `E00650`: `$\dot M \sim (R_{in}/R_a)\dot M_{Bondi}$`
- `astro-ph/0109539` / `E00663`: `$\dot M > 10^{15}$`
- `astro-ph/0102478` / `E00647`: `$\dot M \sim$`

### growth on a relevant timescale

Required relation: $t_{\rm grow}=\int_{M_0}^{M_*}\frac{dM}{\dot M_{\rm net}(M)}<t_{\rm exposure}$

Direct collider equations:

- `0806.3381` / `E00179`: `$t(R_B<R_D) &=& 1.3\times 10^5 \,\frac{1}{\lambda_7} \left({M_D\over M_0}\right)^{5/3} \yr\ ,\ \ \quad\quad\quad D=7\\ t(R_D<R_B<R_C) &=& 6 \times 10^7\,\frac{1}{\lambda_4} \left({M_D\over M_0}\right)^{5/3}\yr\ ,\ \ \quad\quad\quad D=7\\ t(R_B>R_C) &=& 1.9\times 10^6\,\frac{1}{\lambda_4}\left({M_D\over M_0}\right)^{5/3} \yr\ ,\ \ \quad\quad\quad D=7\ .$`

Cross-regime equation candidates:

- `0806.3381` / `E00180`: `$t_w\approx {M(R_C)\over \pi \rho c_s R_C^2} = {16\pi c_sd_0\over \lambda_4} \left({M_4\over M_0}\right)^2 {1\over M_0 R_C}\ .$`
- `0806.3381` / `E00178`: `$t(R_B<R_D) &=& 8\,\frac{1}{\lambda_6} \left({M_D\over M_0}\right)^2 \yr\ ,\ \ \quad\quad\quad D=6\\ t(R_D<R_B<R_C) &=& 4\times 10^2\,\frac{1}{\lambda_4} \left({M_D\over M_0}\right)^2 \yr\ ,\ \ \quad\quad\quad D=6\\ t(R_B>R_C) &=& 15\,\frac{1}{\lambda_4} \left({M_D\over M_0}\right)^2 \yr\ ,\ \ \quad\quad\quad D=6$`
- `0806.3381` / `E00202`: `$t_{NS,w}\sim 20\yr$`

### evasion of astronomical survival bounds

Required relation: $N_{\rm CR}P_{\rm capture}P_{\rm grow}\ll 1\quad {\rm for\ observed\ white\ dwarfs/neutron\ stars}$

Cross-regime equation candidates:

- `0806.3381` / `E00202`: `$t_{NS,w}\sim 20\yr$`

## Composition

- `stopping_capture -> net_positive_growth`: 4 source-local equation path(s).
- `production_selector -> survival_lifetime`: no source-local equation path.
- `survival_lifetime -> stopping_capture`: no source-local equation path.
- `net_positive_growth -> growth_timescale`: no source-local equation path.
- `growth_timescale -> astronomical_bound_evasion`: no source-local equation path.
