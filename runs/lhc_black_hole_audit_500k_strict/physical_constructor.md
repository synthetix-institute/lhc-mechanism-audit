# LHC Physical Constructor

Verdict: `broken_danger_branch`

A dangerous LHC black-hole mechanism requires every slot below. The table distinguishes direct collider receipts from astrophysical transfer receipts.

| Slot | Status | Direct receipts | Transfer receipts | Required condition |
|---|---:|---:|---:|---|
| production threshold | `direct_hook` | 1 | 0 | parton collision can enter a low-scale-gravity production channel |
| survival against evaporation | `transfer_only` | 0 | 6 | object lifetime exceeds the capture or stopping time |
| stopping or capture in matter | `transfer_only` | 0 | 1 | object loses enough kinetic energy to remain inside matter |
| net positive mass growth | `transfer_only` | 0 | 29 | matter intake exceeds mass loss |
| growth on a relevant timescale | `transfer_only` | 0 | 11 | integrated growth time is shorter than the physical exposure time |
| evasion of astronomical survival bounds | `transfer_only` | 0 | 28 | same mechanism must avoid contradiction with compact-object survival |

## Slot Receipts

### production threshold

- status: `direct_hook`
- equation template: `\sqrt{\hat s}=\sqrt{x_1x_2s}>M_{\min},\quad \sigma_{\rm form}\sim \pi r_s^2(M,M_D,n)`

Direct collider receipts:

- `0904.0230` / `E00053`: `|y_{\gamma \gamma}| \leq 1`

### survival against evaporation

- status: `transfer_only`
- equation template: `\tau_{\rm evap}(M,M_D,n)>\tau_{\rm capture}`

Astrophysical transfer receipts:

- `astro-ph0212297` / `E01142`: `B_c\simeq 10^{16}\mbox{G}\left({7M_\odot}/{M_H}\right) \left({6M_H}/{R}\right)^2\left({M_T}/{0.03M_H}\right)^{1/2}`
- `1109.6593` / `E00147`: `M_{turn}=1-1.5 ~M_{\odot}`
- `1604.02455` / `E01020`: `4000M \sim 60(M_{\rm NS/1.625M_\odot)`
- `1604.02455` / `E01021`: `\Delta t \sim 0.1 (M_{\rm NS/1.625M_\odot)`
- `astro-ph0212297` / `E01141`: `{\cal E_B}/{{\cal E}_k}<0.1`

### stopping or capture in matter

- status: `transfer_only`
- equation template: `L_{\rm stop}(M,v,\rho,\sigma)<L_{\rm body}\quad {\rm or}\quad \tau_{\rm capture}<\tau_{\rm escape}`

Astrophysical transfer receipts:

- `astro-ph0105365` / `E01083`: `\dot M \sim (R_{in}/R_a)\dot M_{Bondi}`

### net positive mass growth

- status: `transfer_only`
- equation template: `\dot M_{\rm net}=\rho\,\sigma(M)\,v-P_{\rm evap}(M)/c^2>0`

Astrophysical transfer receipts:

- `0807.3458` / `E00034`: `3 \times 10^{-13}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 1 \times 10^{-10}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `0807.3458` / `E00035`: `4 \times 10^{-14}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 2 \times 10^{-11}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `astro-ph0109539` / `E01098`: `\langle M\rangle \sim 9 {M}_\odot`
- `astro-ph0212297` / `E01142`: `B_c\simeq 10^{16}\mbox{G}\left({7M_\odot}/{M_H}\right) \left({6M_H}/{R}\right)^2\left({M_T}/{0.03M_H}\right)^{1/2}`
- `1307.7685` / `E00825`: `\delta M_{BH}< 5 \times 10^{-4}M_{BH}`

### growth on a relevant timescale

- status: `transfer_only`
- equation template: `t_{\rm grow}=\int_{M_0}^{M_*}\frac{dM}{\dot M_{\rm net}(M)}<t_{\rm exposure}`

Astrophysical transfer receipts:

- `0807.3458` / `E00034`: `3 \times 10^{-13}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 1 \times 10^{-10}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `0807.3458` / `E00035`: `4 \times 10^{-14}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 2 \times 10^{-11}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `astro-ph0212297` / `E01142`: `B_c\simeq 10^{16}\mbox{G}\left({7M_\odot}/{M_H}\right) \left({6M_H}/{R}\right)^2\left({M_T}/{0.03M_H}\right)^{1/2}`
- `1604.02455` / `E01020`: `4000M \sim 60(M_{\rm NS/1.625M_\odot)`
- `1604.02455` / `E01021`: `\Delta t \sim 0.1 (M_{\rm NS/1.625M_\odot)`

### evasion of astronomical survival bounds

- status: `transfer_only`
- equation template: `N_{\rm CR}\,P_{\rm capture}\,P_{\rm grow}\ll 1\quad {\rm for\ observed\ white\ dwarfs/neutron\ stars}`

Astrophysical transfer receipts:

- `0807.3458` / `E00034`: `3 \times 10^{-13}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 1 \times 10^{-10}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `0807.3458` / `E00035`: `4 \times 10^{-14}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 2 \times 10^{-11}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}`
- `astro-ph0212297` / `E01142`: `B_c\simeq 10^{16}\mbox{G}\left({7M_\odot}/{M_H}\right) \left({6M_H}/{R}\right)^2\left({M_T}/{0.03M_H}\right)^{1/2}`
- `1207.1244` / `E00797`: `M_1 = 0.9_{-0.3}^{+4.6} M_\odot`
- `1307.7685` / `E00825`: `\delta M_{BH}< 5 \times 10^{-4}M_{BH}`
