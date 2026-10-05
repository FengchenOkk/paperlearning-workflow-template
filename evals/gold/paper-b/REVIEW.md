# Paper B — source review checklist

Status: **PENDING HUMAN REVIEW**. Draft and visual checking: MODEL_SOURCE_REVIEW. No scientific-validity acceptance or VERIFIED graph mutation.

Gold SHA-256: `f1647451ea439c4b4b29b31f41bc1ca7a368ada89d40d74fceebf019c96cba63`
PDF SHA-256: `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`

Review against the actual rendered PDF, not the extracted text alone. For each item check the quotation, intended type, page/block, context, number/unit/sign/exponent and figure/equation number. Caption statements are separate from visual interpretation. Formula glyph order is not an algebra transcription. Record ACCEPT / REVISE / REJECT with reasons and your actual reviewer identity; do not fill unknown values.

## Frozen source items

### b-problem · RESEARCH_PROBLEM · page 1

Section: Abstract; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 7; bbox [217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125].

> The development of next-generation electronics requires scaling of channel 
> material thickness down to the two-dimensional limit while maintaining ultralow 
> contact resistance1,2.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-contact-method · METHOD · page 1

Section: Abstract; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 7; bbox [217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125].

> Here we push the electrical contact of monolayer molybdenum 
> disulfide close to the quantum limit by hybridization of energy bands with semi- 
> metallic antimony (0112) through strong van der Waals interactions.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-central-result · RESULT · page 1

Section: Abstract; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 7; bbox [217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125].

> The contacts 
> exhibit a low contact resistance of 42 ohm micrometres and excellent stability at 
> 125 degrees Celsius.

| Value | Unit | Context |
| --- | --- | --- |
| 42 | ohm micrometres | contact resistance |
| 125 | degrees Celsius | stability temperature |

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-transistor-result · RESULT · page 1

Section: Abstract; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 7; bbox [217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125].

> Owing to improved contacts, short-channel molybdenum 
> disulfide transistors show current saturation under one-volt drain bias with an 
> on-state current of 1.23 milliamperes per micrometre, an on/off ratio over 108 and  
> an intrinsic delay of 74 femtoseconds.

| Value | Unit | Context |
| --- | --- | --- |
| 1.23 | milliamperes per micrometre | on-state current |
| 10^8 | dimensionless | on/off ratio lower bound |
| 74 | femtoseconds | intrinsic delay |

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-ballistic-assumption · ASSUMPTION · page 1

Section: Introduction; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 8; bbox [39.685001373291016, 531.3456420898438, 296.2746887207031, 584.526123046875].

> In an ideal M–S junction, there is a fundamental quantum limit in the 
> junction contact resistance by assuming ballistic transport of the con-
> ducting modes:

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-equation-1 · EQUATION · page 1

Section: Introduction; epistemic status: PAPER_EXPLICIT; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 9; bbox [125.19599914550781, 592.1370849609375, 162.9974365234375, 608.2368774414062].

> R
> h

Original extraction block 10; bbox [146.7942657470703, 597.9313354492188, 184.8877410888672, 614.8609008789062].

> q
> n
> = 2

Original extraction block 11; bbox [130.3800048828125, 592.1704711914062, 294.445556640625, 615.3026733398438].

> π
> 2
> ,
> (1)
> c,min
> 2
> 2D

Model transcription for comparison only: `R_c,min = h/(2 q^2) sqrt(pi/(2 n_2D))`. Production LaTeX remains null.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-symbol-definitions · DEFINITION · page 1

Section: Introduction; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 12; bbox [39.685001373291016, 628.0626220703125, 296.3440856933594, 659.776123046875].

> where h is Planck’s constant, q is the unit charge and n2D is the carrier 
> concentration in the semiconductor.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-figure-1 · FIGURE · page 2

Section: Results; epistemic status: PAPER_EXPLICIT; channel: CAPTION_EXPLICIT.

Original extraction block 97; bbox [39.68220520019531, 284.0237121582031, 294.2340087890625, 352.7767028808594].

> Fig. 1 | Electronic properties of Sb 0112
> (
> )–MoS2 and Sb (0001)–MoS2 contacts 
> from DFT calculations. a,b, Atomic-projected electronic band structure of Sb 
> (0112)–MoS2 (a) and Sb (0001)–MoS2 (b) contacts. The red and blue symbols 
> represent orbitals from MoS2 and Sb, respectively. The size of the symbols 
> represents the relative contribution. c,d, The charge density near EF (left) and 
> the differential charge density (right) of Sb (0112) (c) and Sb (0001) (d) contacts 
> (red, positive; blue, negative). The blue, green and yellow spheres represent  

Original extraction block 96; bbox [306.13946533203125, 283.0007019042969, 562.3009643554688, 351.6423034667969].

> Sb, Mo and S atoms, respectively. The differential charge density iscalculated 
> by subtracting pre-contact three-layer Sb and MoS2 charge density from the 
> post-contact charge density. The isosurface level is 9 × 10−5 e Bohr−3 and 
> 7 × 10−4 e Bohr−3 for the left and right panels, respectively. e, Projected PLDOS of 
> different orbitals of Sb (0112)–MoS2 and Sb (0001)–MoS2 contacts near EF. f, The 
> integrated DOS of TMDs at EF. g, The charge transfer from Sb to TMDs by Bader 
> charge analysis. h, The interfacial vdW interaction between TMDs and Sb.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-figure-2 · FIGURE · page 2

Section: Results; epistemic status: PAPER_EXPLICIT; channel: CAPTION_EXPLICIT.

Original extraction block 132; bbox [39.681610107421875, 695.92236328125, 291.4875793457031, 745.3051147460938].

> Fig. 2 | Characterization of the Sb 0112
> (
> )–MoS2 contact. a, Raman spectrum 
> of Sb film deposited on MoS2/Si substrate shows Sb Eg and A1g peaks at 111 cm−1 
> and 149 cm−1, respectively. b, XRD θ–2θ diffractogram of Sb film with different 
> deposition conditions and substrate. RT, room temperature. c, Cross-section 
> HAADF-STEM image of the Sb (0112)–MoS2 contact. The interplane distance of 

Original extraction block 131; bbox [306.1414794921875, 696.0575561523438, 558.864013671875, 744.8113403320312].

> 0.315 nm for Sb (0112) planes is marked. Scale bar, 2 nm. d, Zoom-in 
> atomic-resolution image from the red box in c. The Mo, S and Sb atoms are 
> overlayed on the image. The vdW gap of 0.285 nm is marked. Scale bar, 1 nm.  
> e, Optical microscope image of Sb films deposited on MoS2 and SiO2 substrate, 
> showing clear colour contrast. Scale bar, 20 μm.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-figure-3 · FIGURE · page 3

Section: Results; epistemic status: PAPER_EXPLICIT; channel: CAPTION_EXPLICIT.

Original extraction block 65; bbox [39.682498931884766, 262.4661560058594, 294.635986328125, 331.8489074707031].

> Fig. 3 | Electrical properties and stability of the Sb 0112
> (
> )–MoS2 contact. 
>  a, Transfer curves of a typical TLM structure with Lc ranging from 0.1 μm to 
> 1.5 μm and Vds = 0.1 V. Inset: false-colour scanning electron microscope image 
> of a TLM structure. Scale bar, 2 μm. b, Rc extraction using the TLM method from 
> the device in a. From top to bottom, n2D = 1.2 × 1013 cm−2, 1.6 × 1013 cm−2, 
> 2.1 × 1013 cm−2 and 3 × 1013 cm−2, respectively. Inset: the magnified data plot near 
> Lc = 0, where the y intercept and x intercept represent 2Rc and 2LT, respectively. 

Original extraction block 64; bbox [306.1393127441406, 261.412109375, 560.2733764648438, 330.07781982421875].

> It is noted that the LT derived by the TLM method assumes the same MoS2 sheet 
> resistivity underneath and outside the contact, which is probably violated 
> considering the charge transfer between Sb (0112) and MoS2. This could lead to 
> uncertainties in the obtained LT. c. Rc (red squares) and intrinsic mobility (black 
> rhombuses) as a function of temperature for another device. d–f, Rc (d), LT (e) 
> and μint (f) distribution of the Sb (0112) and Sb (0001) contacts, respectively. 
> The solid lines are Gaussian fittings.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-tlm-assumption · ASSUMPTION · page 3

Section: Figure 3 caption; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 64; bbox [306.1393127441406, 261.412109375, 560.2733764648438, 330.07781982421875].

> It is noted that the LT derived by the TLM method assumes the same MoS2 sheet 
> resistivity underneath and outside the contact, which is probably violated 
> considering the charge transfer between Sb (0112) and MoS2.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-tlm-limitation · LIMITATION · page 3

Section: Figure 3 caption; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 64; bbox [306.1393127441406, 261.412109375, 560.2733764648438, 330.07781982421875].

> This could lead to 
> uncertainties in the obtained LT.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-average-contact · RESULT · page 5

Section: Results; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 48; bbox [39.68223571777344, 369.8003234863281, 296.29644775390625, 553.02197265625].

> The average Rc of the Sb 
> (0112) contact was 209 ± 100 Ω μm, which was 3.47-times lower than 
> the Sb (0001) counterpart.

| Value | Unit | Context |
| --- | --- | --- |
| 209 ± 100 | Ω μm | average Sb(0112) contact resistance |
| 3.47 | times | lower than Sb(0001) average |

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-stability · RESULT · page 5

Section: Results; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 50; bbox [39.68510055541992, 552.8456420898438, 296.334228515625, 681.276123046875].

> No obvious degradation of Ion, threshold voltage 
> (Vth) and subthreshold swing (SS) was observed during 24 h for the Sb 
> contact.

| Value | Unit | Context |
| --- | --- | --- |
| 24 | h | stability observation interval |

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-dft-method · SIMULATION · page 7

Section: Methods; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 4; bbox [306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875].

> First-principles DFT calculations were performed by using the Vienna 
> Ab initio Simulation Package (VASP 5.4)49 with the exchange-correlation 
> functional based on Perdew–Burke–Ernzerhof 50 generalized gradient 
> approximation.

Human decision: PENDING. Reason: ____. Reviewer: ____.

### b-dft-convergence · METHOD · page 7

Section: Methods; epistemic status: AUTHOR_CLAIM; channel: PAPER_TEXT_EXPLICIT.

Original extraction block 4; bbox [306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875].

> All structures were fully relaxed until 
> the maximum force component acting on each atom was less than 
> 0.02 eV Å−1 with an energy convergence criterion of 10−4 eV and an kinetic 
> energy cut-off of 400 eV.

| Value | Unit | Context |
| --- | --- | --- |
| 0.02 | eV Å^−1 | maximum force threshold |
| 10^−4 | eV | energy convergence |
| 400 | eV | kinetic energy cut-off |

Human decision: PENDING. Reason: ____. Reviewer: ____.

## Precision predictions

All predictions in the frozen windows are included, including predictions outside gold. These are current model source judgments; human decisions remain pending.

| Key prefix | Type | Page | Model judgment | Human decision |
| --- | --- | --- | --- | --- |
| 1d94749e59dc | RESEARCH_PROBLEM | 1 | True | PENDING |
| 71a3da0b5bab | LIMITATION | 1 | True | PENDING |
| 736ff73f7f51 | METHOD | 1 | True | PENDING |
| 4afc27cb153d | RESULT | 1 | True | PENDING |
| 0ce4a64ad391 | RESULT | 1 | True | PENDING |
| d2b3529cf9ff | ASSUMPTION | 1 | True | PENDING |
| 9d465db2812c | EQUATION | 1 | True | PENDING |
| 37ef6a8106f3 | DEFINITION | 1 | True | PENDING |
| 20dc584a26a7 | FIGURE | 2 | True | PENDING |
| 99ec6ea9bc19 | FIGURE | 2 | True | PENDING |
| d600f4651fab | FIGURE | 3 | True | PENDING |
| c4e617ecca1d | ASSUMPTION | 3 | True | PENDING |
| f80f7f96f1fe | LIMITATION | 3 | True | PENDING |
| 8535901b689d | METHOD | 5 | True | PENDING |
| d31983b4f2f2 | RESULT | 5 | True | PENDING |
| c122b3c98f96 | RESULT | 5 | True | PENDING |
| 48b848f51191 | SIMULATION | 7 | True | PENDING |
| 00762870e275 | METHOD | 7 | True | PENDING |

Exact prediction text and reasons: [current report](../../reports/dual-paper/current-b.json) and [model prediction review](prediction-review.json).

## Limits

Acceptance here would establish the stated source sample, not full-document extraction quality or scientific truth. Overbars/subscripts/fraction layout, figures as image evidence and supplementary material remain unverified. Repeated source headers are not merged into scientific entities.
