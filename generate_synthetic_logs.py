import os
import random
import datetime
import pandas as pd

# Try importing Faker; fall back gracefully if unavailable
try:
    from faker import Faker
    fake = Faker()
    Faker.seed(42)
    TECH_POOL = [fake.name() for _ in range(8)]
except ImportError:
    TECH_POOL = [
        "Marcus Vance",
        "Elena Rostova",
        "David Chen",
        "Sarah Jenkins",
        "Carlos Ramirez",
        "Priya Patel",
        "Jameson Thorne",
        "Hannah Abbott"
    ]

# -------------------------------------------------------------------------
# CLUSTERED DATE CONFIGURATION (Jan 2023 - Dec 2024)
# -------------------------------------------------------------------------
# We assign weights to each month to simulate natural clustering of work orders
# (e.g., summer cooling stress, seasonal plant overhauls in spring/autumn, winter freezes)
MONTHS_2023_2024 = [
    f"{year}-{month:02d}" for year in [2023, 2024] for month in range(1, 13)
]

MONTH_WEIGHTS = [
    # 2023: Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
            1.1, 0.7, 1.6, 1.0, 1.2, 1.9, 2.4, 2.2, 1.3, 1.8, 0.8, 1.4,
    # 2024: Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec
            1.2, 0.8, 1.7, 1.1, 1.3, 2.1, 2.6, 2.3, 1.4, 1.9, 0.9, 1.5
]

# -------------------------------------------------------------------------
# RELATIONSHIP PHRASES FOR NLP VARIETY
# -------------------------------------------------------------------------
# When related_asset_ids is populated (20-30% of rows for assets with parents/children),
# these templates inject realistic field references to the related equipment.
RELATIONSHIP_PHRASES = [
    " Note: Vibration and harmonic resonance appear transmitted from {rel_id}.",
    " Ops reported load fluctuations on {rel_id} coinciding with this fault.",
    " Checked mechanical alignment and interlocks with coupled unit {rel_id} during inspection.",
    " Suspect binding or restriction here caused elevated current draw on {rel_id}.",
    " Issue first noticed after high-temperature trip occurred on {rel_id}.",
    " Tech observed abnormal acoustic noise propagating across the coupling from {rel_id}.",
    " Also inspected {rel_id} to rule out secondary mechanical strain or electrical feed anomalies.",
    " High load demand from driven equipment ({rel_id}) suspected of accelerating component wear.",
    " Unit overdrawing current when {rel_id} operates at peak capacity.",
    " Field diagnostics indicate misalignment at shaft coupling connecting directly to {rel_id}.",
    " Maintenance triggered after unusual process flow/pressure drop noted on primary process unit {rel_id}.",
    " Inspected power and control interconnects running to {rel_id} during diagnostic routine."
]

# -------------------------------------------------------------------------
# COMPREHENSIVE FAILURE MODE KNOWLEDGE BASE
# -------------------------------------------------------------------------
# Structured by exact equipment type and failure mode.
# Contains rich symptom templates, root causes, actions taken, parts used, and downtime bounds.
FAILURE_MODE_KB = {
    "Centrifugal Pump": {
        "cavitation": {
            "symptoms": [
                "Noticeable {adj} crackling and popping sounds heard from pump suction casing. Discharge pressure is {degree} erratic under normal load (`+/- {press_drop} PSI`).",
                "Ops reported {adj} gravel-like {noise} inside pump housing during peak flow (`{gpm} GPM`). Suction gauge fluctuating +/- {press} PSI.",
                "Found pump exhibiting {degree} casing vibration (`{vibe}` in/sec RMS) and {obs} near inlet manifold. Possible flow restriction or NPSH margin drop (`< {npsh_margin}`).",
                "Pump making loud {noise} right after morning startup. Discharge flow dropping intermittently (`{percent}` drop) with high casing vibration (`{vibe}` in/sec RMS).",
                "Severe cavitation noise (`{noise}`) detected across pump volute with suction pressure dropping by `{press_drop} PSI` under maximum load.",
                "Discharge pressure unstable and dropping `{percent}` below curve. Acoustic inspection revealed {adj} vapor bubble collapse within impeller eye."
            ],
            "root_causes": [
                "Insufficient Net Positive Suction Head Available (NPSHA) caused by partially clogged suction basket strainer (`{clog_pct}` flow restriction, suction drop of `{press_drop} PSI`).",
                "Air entrainment in suction pipe due to degraded suction valve stem packing and low feed tank level (`< {percent}` capacity remaining).",
                "Operating pump excessively far out beyond its Best Efficiency Point (BEP) by `{percent}` during high production demand (`{gpm} GPM`).",
                "Suction pipe restriction from sediment accumulation (`{thickness} inch` buildup) causing localized vapor bubble formation and collapse at `{press_drop} PSI` vacuum.",
                "Excessive fluid temperature (`{temp_rc}`\u00b0C) raising vapor pressure above available NPSH margin by `{npsh_margin}`.",
                "Inlet bellmouth vortexing and turbulence caused by low liquid level (`{percent}` submerged) and degraded baffle plates after `{hours}` hours of service."
            ],
            "actions": [
                "Cleaned suction inlet basket strainer (`{mesh}`), removed `{debris_amt}` of debris, and throttled discharge valve to restore `{npsh_margin}` of NPSH margin.",
                "Replaced suction valve stem packing (`{part_num}`), purged air from suction manifold, and verified tank minimum level interlock setpoint (`> {percent}`).",
                "Adjusted VFD speed profile (`{hz}`) and trimmed discharge flow to keep pump operating within optimal BEP parameters (`+/- {percent}` curve).",
                "Flushed suction piping line with high-pressure water, cleared `{thickness} inch` scale, and inspected impeller eye for early pitting signs (`{clearance} gap`).",
                "Lowered feed fluid operating temperature by adjusting heat exchanger bypass, increasing effective NPSHA by `{npsh_margin}` under `{gpm} GPM` flow.",
                "Installed vortex suppressor baffle inside suction tank, topped off level above `{percent}`, and verified steady suction pressure (`+{press_drop} PSI`)."
            ],
            "parts": [
                ["Suction Strainer Mesh Basket", "Flange Gasket Kit"],
                ["Suction Valve Packing Rings", "O-Ring Kit"],
                ["None"],
                ["Flange Gasket 3-inch", "Stainless Steel Bolt Set"],
                ["Heat Exchanger Gasket Pack", "Thermocouple Probe"],
                ["Vortex Baffle Plate Assembly", "Tank Mounting Hardware"]
            ],
            "downtime": (2.0, 5.5)
        },
        "seal leakage": {
            "symptoms": [
                "Found {adj} fluid dripping constantly from pump stuffing box area (`~{debris_amt}/hr`). Pool of process fluid accumulating on baseplate.",
                "Ops flagged {obs} (`{temp}`\u00b0C) near mechanical seal gland during walkaround. Seal flush line appears restricted (`{percent}` flow reduction).",
                "Heavy fluid dripping from lower seal chamber (`{press_drop} PSI` barrier pressure loss). Tech observed {degree} {obs} and vapor formation around shaft sleeve.",
                "Mechanical seal weeping {adj} volume of fluid onto skid plate. Seal reservoir pressure dropping steadily (`{press_drop} PSI/hr`) over 24 hrs.",
                "Continuous leakage (`{percent}` barrier oil loss) detected across tandem seal assembly with {adj} thermal buildup (`{temp}`\u00b0C).",
                "Primary seal weeping process liquid across gland plate (`{clearance} clearance`). High frequency acoustic emission (`{vibe}` in/sec RMS) measured."
            ],
            "root_causes": [
                "Mechanical seal faces scored due to abrasive particles (`{ppm}` solids) in process fluid and inadequate seal flush filtration (`{microns} micron filter blinded`).",
                "Thermal shock (`{temp_rc}`\u00b0C spike) and lack of lubrication caused carbon seal face blistering and O-ring degradation after `{hours}` operating hours.",
                "Shaft runout exceeding `{runout} inch` caused uneven wear and opening on mechanical seal stationary face under `{press} PSI` pressure.",
                "Failure of external seal flush cyclone separator (`{clog_pct}` blocked) leading to abrasive solids accumulation inside stuffing box chamber.",
                "Excessive axial shaft end-play (`{clearance} inch` float) from worn thrust bearing overloaded mechanical seal spring tension (`{torque}`).",
                "Chemical attack from aggressive pH excursions (`pH {ph_val}`) degraded secondary elastomeric Viton O-rings after `{time_period}` of continuous service."
            ],
            "actions": [
                "Removed pump casing, replaced cartridge mechanical seal assembly (`{part_num}`), renewed `{microns} micron` flush filter, and flushed seal supply piping.",
                "Replaced mechanical seal faces and O-rings (`{part_num}`); cleaned seal flush line orifice and verified cooling flow (`{gpm} GPM` at `{temp}`\u00b0C).",
                "Realigned motor and pump shaft (`{runout} inch` runout achieved), torqued hold-down bolts (`{torque}`), and installed new single cartridge mechanical seal.",
                "Replaced damaged seal faces, flushed `{debris_amt}` of accumulated solids, and installed upgraded cyclone separator in seal flush loop.",
                "Disassembled pump rotating assembly, adjusted thrust bearing end-play to `{clearance} inch`, and installed new balanced cartridge mechanical seal (`{part_num}`).",
                "Upgraded seal secondary elastomers to chemical-resistant Kalrez (`{part_num}`), renewed seal faces, and verified zero leakage on 30-min hydro test (`{press} PSI`)."
            ],
            "parts": [
                ["Cartridge Mechanical Seal Assembly", "Casing Gasket", "Flush Filter Element"],
                ["Mechanical Seal Repair Kit", "Viton O-Ring Set"],
                ["Single Mechanical Seal", "Shaft Sleeve", "Gasket Kit"],
                ["Seal Faces Set", "Cyclone Separator Element"],
                ["Balanced Cartridge Seal Kit", "Thrust Bearing Shim Pack"],
                ["Kalrez O-Ring Upgrade Kit", "Silicon Carbide Seal Face Set"]
            ],
            "downtime": (3.0, 6.5)
        },
        "impeller wear": {
            "symptoms": [
                "Pump unable to maintain rated head (`{press_drop} PSI` drop from curve). Motor amp draw is `{percent}` lower than baseline (`{amps} Amps`).",
                "Gradual degradation in discharge flow (`{percent}` reduction to `{gpm} GPM`). Casing inspection revealed {adj} internal turbulence and {noise}.",
                "Ops noted pump running smoothly but failing to meet process target gpm (`{percent}` deficit). Hydraulic performance curve shift suspected.",
                "Excessive recirculation noise (`{noise}`) inside casing and {adj} pressure drop (`{press_drop} PSI`) across pump discharge flange.",
                "Loss of pump efficiency (`{percent}` drop) over `{time_period}`. High frequency flow turbulence (`{vibe}` in/sec RMS) measured across volute.",
                "Discharge head decreased steadily (`-{press_drop} PSI`). Motor current drawing `{percent}` below rated full load amps (`{amps} Amps`)."
            ],
            "root_causes": [
                "Severe erosive wear (`{thickness} inch` metal loss) on impeller vanes due to entrained abrasive solid particulates (`{ppm}`) over `{hours}` runtime hours.",
                "Cavitation erosion over past `{time_period}` eroded vane tips and widened wear ring clearances to `{gap} inch` (`normal < 0.012 inch`).",
                "Chemical corrosion (`pH {ph_val}`) thinned outer shroud of bronze impeller by `{percent}`, leading to severe internal recirculation.",
                "Normal mechanical degradation of wear rings (`{gap} inch` gap) and impeller shroud after `{hours}` hours of continuous high-load service.",
                "High-velocity slurry impingement (`{gpm} GPM`) eroded leading edge of impeller vanes, reducing effective outer diameter by `{thickness} inch`.",
                "Foreign object impact (`{debris_amt}` solid piece ingested) chipped outer impeller vane tips and bent front shroud by `{runout} inch`."
            ],
            "actions": [
                "Disassembled pump rotating element, installed new 316SS trimmed impeller (`{part_num}`) and casing wear rings, setting clearance to `{clearance} inch`.",
                "Replaced eroded impeller assembly (`{part_num}`), renewed front/rear wear rings (`{gap} inch` gap restored), and balanced rotor dynamically (`G2.5`).",
                "Upgraded impeller to hardened duplex alloy (`{part_num}`), applied ceramic wear coating (`{thickness} inch`), and set proper clearances (`{clearance} inch`).",
                "Swapped out worn impeller assembly (`{part_num}`), renewed casing wear rings to `{clearance} inch` spec, and replaced shaft locking nut and key (`{torque}`).",
                "Installed heavy-duty chrome-iron impeller (`{part_num}`), renewed volute liners (`{thickness} inch`), and verified rated head recovery (`+{press_drop} PSI`).",
                "Extracted damaged impeller, cleared debris from volute casing, installed new dynamically balanced impeller (`{part_num}`), and torqued casing bolts (`{torque}`)."
            ],
            "parts": [
                ["316SS Impeller", "Casing Wear Ring", "Impeller Key"],
                ["Impeller Assembly", "Front and Rear Wear Rings", "Casing Gasket"],
                ["Duplex Stainless Impeller", "Ceramic Coating Kit", "Wear Ring Set"],
                ["Replacement Impeller", "Lock Washer", "Shaft Nut"],
                ["Chrome-Iron Slurry Impeller", "Volute Liner Set"],
                ["Dynamically Balanced Impeller Assembly", "Casing O-Ring", "Shaft Key"]
            ],
            "downtime": (5.5, 10.0)
        },
        "bearing failure": {
            "symptoms": [
                "Elevated bearing housing temperature (`{temp}`\u00b0C measured via infrared gun) along with {adj} {noise} sound (`{vibe}` in/sec RMS) from thrust end.",
                "High frequency vibration (`{vibe}` in/sec RMS) detected during routine condition monitoring survey on pump outboard bearing (`BPFI peak`).",
                "Loud {noise} and metallic clattering from bearing pedestal (`{temp}`\u00b0C). Oil level check showed {adj} discoloration and `{ppm}` metal debris.",
                "Bearing housing running extremely hot (`{temp}`\u00b0C) and vibrating `{degree}` (`{vibe}` in/sec RMS). Unit shut down immediately by maintenance roundsman.",
                "Acoustic emission levels spiked `{percent}` across thrust bearing housing. Oil sampling showed elevated iron and copper wear particles (`{ppm}`).",
                "Inboard bearing temperature reached `{temp}`\u00b0C (`alarm setpoint 85\u00b0C`). Severe {adj} whining sound (`{noise}`) audible at `{hz}` operating speed."
            ],
            "root_causes": [
                "Lube oil contamination with process fluid/water (`{ppm}` moisture) caused breakdown of oil film and subsequent spalling of bearing races after `{hours}` hours.",
                "Fatigue failure and flaking of rolling elements due to prolonged operation with `{runout} inch` angular misalignment and `{press} PSI` load.",
                "Lack of lubrication following oil ring hangup inside bearing housing reservoir (`oil level dropped {thickness} inch` below minimum sight glass mark).",
                "Improper bearing preload and excessive axial thrust load (`{percent}` above design) caused premature cage fracture and rolling element skidding.",
                "Thermal degradation and hardening of bearing grease (`{temp_rc}`\u00b0C operating environment) over `{time_period}`, resulting in severe metal-to-metal friction.",
                "Shaft journal scoring (`{runout} inch` taper) and improper fitting tolerance during previous overhaul allowed bearing inner race to spin on shaft."
            ],
            "actions": [
                "Replaced both inboard and outboard radial/thrust bearings (`{part_num}`), flushed bearing housing of `{ppm}` debris, and added synthetic ISO VG 68 oil.",
                "Pulled bearing frame, pressed on new SKF angular contact bearings (`{part_num}`), replaced lip seals, and realigned shaft within `{clearance} inch`.",
                "Replaced damaged bearing set (`{part_num}`), polished shaft journals (`{clearance} inch` fit), and installed new constant level oiler assembly (`{part_num}`).",
                "Replaced thrust bearing housing assembly (`{part_num}`), renewed oil seals, adjusted axial preload shims (`{thickness} inch`), and verified dynamic balance (`{vibe}` in/sec).",
                "Cleaned grease cavities, installed precision C3 clearance roller bearings (`{part_num}`), packed with Polyrex EM grease (`{percent}` fill), and verified low vibration (`{vibe}` in/sec).",
                "Re-metallized and ground shaft journal to exact tolerance (`{clearance} inch`), installed new precision bearing set (`{part_num}`), and torqued housing bolts (`{torque}`)."
            ],
            "parts": [
                ["SKF Outboard Angular Contact Bearing", "Inboard Roller Bearing", "ISO VG 68 Lube Oil"],
                ["Bearing Kit 6309-C3", "Lip Seal Set", "Shim Pack"],
                ["Thrust Bearing Assembly", "Constant Level Oiler", "Oil Sight Glass"],
                ["Radial Bearing", "Thrust Bearing Set", "Housing Gasket"],
                ["Precision Roller Bearing Set C3", "Polyrex EM Grease (1 Tube)", "Lip Seal Kit"],
                ["Bearing Journal Sleeve", "Deep Groove Ball Bearing Set", "Housing Fasteners"]
            ],
            "downtime": (6.0, 11.5)
        },
        "misalignment": {
            "symptoms": [
                "1X and 2X RPM vibration peaks (`{vibe}` in/sec RMS) observed across pump and motor coupling. Noticeable {adj} axial vibration (`{vibe}` in/sec RMS).",
                "Coupling insert wearing rapidly (`{degree}` shedding of elastomeric dust, `{thickness} inch` wear). High radial vibration (`{vibe}` in/sec RMS) on inboard bearing pads.",
                "Elevated temperatures on both motor and pump inboard bearing housings (`{temp}`\u00b0C) with {adj} humming noise (`{hz}` frequency).",
                "Unit exhibiting {degree} vibration (`{vibe}` in/sec RMS) across coupling guard after recent pipework modification (`{press} PSI` line).",
                "High axial vibration (`{vibe}` in/sec RMS) and abnormal phase relationship (`{percent}` phase shift across coupling) detected during vibration survey.",
                "Coupling bolts loosening (`{degree}` play) with {adj} rattling (`{noise}`). Temperature across coupling guard elevated to `{temp}`\u00b0C."
            ],
            "root_causes": [
                "Thermal growth differential (`{thickness} inch` vertical expansion) between pump and motor not compensated for during initial cold alignment (`{temp_rc}`\u00b0C operating delta).",
                "Pipe strain from improperly supported discharge piping (`{press} PSI` line) exerting `{torque}` twisting torque on pump suction flange (`{gap} inch` deflection).",
                "Soft foot condition under motor baseplate (`{gap} inch` gap on right rear foot) causing structural distortion during anchor bolt torquing (`{torque}`).",
                "Foundation settling and normal vibration shifting over `{time_period}` degraded precision laser alignment (`{runout} inch` parallel offset, `{gap} inch/10 inch` angular).",
                "Coupling elastomeric element failure (`{percent}` degradation) due to operating in high ambient temperature (`{temp_rc}`\u00b0C) and minor angular offset (`{runout} inch`).",
                "Anchor bolt relaxation (`{torque}` under-torqued) on pump skid allowed frame shifting during heavy surge flow (`{gpm} GPM`)."
            ],
            "actions": [
                "Performed precision laser alignment between pump and driving motor, bringing angular and parallel offset within `{clearance} inch` (`{torque}` hold-down torque).",
                "Corrected motor soft foot using `{thickness} inch` stainless shims, adjusted piping spring hangers to relieve `{press_drop} PSI` pipe strain, and realigned shafts (`{clearance} inch`).",
                "Replaced worn elastomeric coupling insert (`{part_num}`) and re-laser aligned pump/motor train to tight tolerance (`< {clearance} inch` offset).",
                "Loosened flange bolts to relieve `{torque}` pipe strain, re-torqued baseplate hold-down bolts (`{torque}`), and completed full alignment (`{clearance} inch`).",
                "Installed upgraded high-temperature urethane coupling element (`{part_num}`), shimmed motor base (`{thickness} inch`), and verified vibration dropped to `{vibe}` in/sec RMS.",
                "Re-torqued anchor bolts (`{torque}`), re-grouted baseplate void (`{thickness} inch`), and laser aligned coupling shafts (`{clearance} inch` tolerance)."
            ],
            "parts": [
                ["Elastomeric Coupling Insert", "Precision Stainless Steel Shim Pack"],
                ["Coupling Element", "Shim Kit 2x2", "Spring Hanger Adjusting Rods"],
                ["Omega Coupling Half and Element"],
                ["None"],
                ["High-Temp Urethane Coupling Element", "Stainless Shim Assortment Kit"],
                ["Baseplate Epoxy Grout Kit", "Anchor Bolt Lock Washer Set"]
            ],
            "downtime": (2.5, 5.0)
        }
    },
    "Submersible Pump": {
        "motor winding failure": {
            "symptoms": [
                "Submersible pump tripped main circuit breaker upon startup. Megger insulation resistance test showed `{mg_ohm}` to ground.",
                "Severe short circuit current surge (`{amps} Amps` spike) tripped upstream breaker. Tech noted {adj} burnt electrical smell from terminal junction box.",
                "Pump fails to start (`{current}` Amps inrush trip). Phase-to-phase resistance imbalance (`{percent}` difference) detected at control cabinet (`{volts}`).",
                "Continuous tripping of thermal/magnetic overload relays (`{amps} Amps`). Field check confirmed dead short between phase B and ground (`{mg_ohm}`).",
                "Stator winding ground fault triggered ground fault interrupter at `{amps} Amps`. IR scan showed localized casing hot spot (`{temp}`\u00b0C).",
                "High current draw (`{percent}` above rated `{amps} Amps`) prior to thermal trip. Insulation resistance dropped from >100M to `{mg_ohm}` across all phases."
            ],
            "root_causes": [
                "Moisture ingress (`{ppm}` water detected in oil chamber) into motor enclosure through degraded cable entry seal caused stator winding insulation breakdown after `{hours}` hours.",
                "Prolonged operation in overheated condition (`{temp_rc}`\u00b0C internal temp) due to low sump liquid level (`{percent}` submerged) leading to thermal aging of winding varnish.",
                "Voltage surges (`> {volts} peak`) from utility grid switching transients degraded turn-to-turn Class F winding insulation after `{time_period}` of service.",
                "Stator winding ground fault (`{mg_ohm}` resistance) caused by internal magnetic vibration (`{vibe_rc}` in/sec) chafing insulation against stator core slots.",
                "Thermal runaway caused by deadhead running (`0 GPM` flow for `{hours}` hours), melting stator slot insulation and shorting phase coils (`{volts}`).",
                "Corrosive gas ingress from wet well (`pH {ph_val}` atmosphere) permeated lower motor housing seals, attacking stator copper magnet wire over `{time_period}`."
            ],
            "actions": [
                "Pulled submersible pump from sump, sent to certified rewind shop for full Class H stator rewinding (`{part_num}`) and double VPI epoxy dip (`{tan_delta}` test).",
                "Replaced complete submersible motor assembly (`{part_num}`), renewed cable entry seal assembly (`{part_num}`), and tested megger resistance (`> 500 Mega-ohms`) before dropping into pit.",
                "Replaced stator core assembly (`{part_num}`), baked and dipped windings, and installed upgraded moisture sensing relay (`{part_num}`) in cabinet (`{volts}`).",
                "Installed spare submersible motor unit (`{part_num}`), renewed mechanical seals (`{clearance} gap`) and power cable gland, and verified proper rotation and current (`{amps} Amps`).",
                "Rewound stator coils (`{part_num}`), replaced thermal protection switches (`setpoint 140\u00b0C`), filled housing with fresh dielectric oil, and verified insulation (`{mg_ohm}`).",
                "Upgraded motor to epoxy-sealed submersible stator (`{part_num}`), renewed Viton housing O-rings (`{part_num}`), and verified balanced phase currents (`{amps} Amps` at `{volts}`)."
            ],
            "parts": [
                ["Submersible Stator Rewind Kit Class H", "Upper/Lower Mechanical Seals", "O-Ring Rebuild Set"],
                ["Submersible Motor Assembly", "Cable Entry Seal Kit", "Terminal Terminal Lugs"],
                ["Replacement Stator Core Assembly", "Moisture Sensor Module", "Housing Gasket"],
                ["Submersible Motor Unit Spare", "Lower Mechanical Seal Assembly", "Dielectric Oil 1 Gal"],
                ["Stator Coil Rewind Set", "Thermal Switch Pack", "Dielectric Oil Fill Kit"],
                ["Epoxy-Sealed Submersible Stator", "Viton Housing O-Ring Pack", "Cable Lead Seal"]
            ],
            "downtime": (8.0, 12.0)
        },
        "seal leakage": {
            "symptoms": [
                "Moisture sensor in pump oil chamber triggered high humidity/water interlock alarm (`{percent}` water content) on main control panel (`{volts}`).",
                "Routine inspection of oil chamber sampling port revealed milky, emulsified oil (`{degree}` water contamination, `{ppm}` moisture).",
                "Submersible pump seal chamber leak detector alarm active. Small {obs} noticed during pull test along with {adj} oil slick.",
                "High water content (`{ppm}`) in barrier oil reservoir. No external leak visible yet but lower mechanical seal compromised (`{press_drop} PSI` drop).",
                "Oil chamber moisture probe resistance dropped to `{mg_ohm}` (`alarm < 30 kOhm`). Dielectric oil level elevated (`+{thickness} inch`) due to water ingress.",
                "Lower seal weeping process liquid into barrier chamber (`{percent}` water concentration). Tech noted {adj} emulsified foam during sampling."
            ],
            "root_causes": [
                "Lower mechanical seal faces scored due to solid grit and abrasive slurry (`{ppm}` solids) passing through pump volute over `{hours}` operating hours.",
                "Thermal expansion cycles (`{temp_rc}`\u00b0C swings) degraded elastomeric bellows of lower mechanical seal after `{time_period}` of submerged duty.",
                "Improper tension (`{torque}` spring load) on seal spring during previous overhaul allowed fluid separation across stationary face (`{clearance} gap`).",
                "Corrosion (`pH {ph_val}`) of lower seal housing lip due to aggressive wastewater chemistry thinned seal retainer by `{percent}` after `{time_period}`.",
                "Vibration from unbalanced impeller (`{vibe_rc}` in/sec RMS) induced micro-fretting and chipping on tungsten carbide stationary seal face.",
                "Dry running during low wet-well level (`{percent}` submerged) caused extreme frictional heating (`{temp_rc}`\u00b0C) and thermal cracking of ceramic seal rings."
            ],
            "actions": [
                "Pulled pump, drained emulsified oil (`{ppm}` water), replaced both upper and lower tandem mechanical seals (`{part_num}`), and refilled dielectric oil.",
                "Disassembled lower end, renewed double mechanical seal assembly (`{part_num}`) and O-rings, and pressure tested oil chamber (`{press} PSI` for 30 min).",
                "Replaced lower silicon carbide seal faces (`{part_num}`) and upper lip seal; flushed and refilled barrier fluid reservoir with fresh dielectric oil.",
                "Renewed tandem mechanical seals (`{part_num}`), replaced corroded seal retainer ring (`{part_num}`), and verified zero drop on 30-minute pressure decay test (`{press} PSI`).",
                "Installed upgraded tungsten carbide seal cartridge (`{part_num}`), realigned shaft (`{runout} inch` runout), and filled seal chamber with dielectric oil (`{lbs_charge}`).",
                "Replaced thermal-cracked seal faces with silicon carbide/silicon carbide seal (`{part_num}`), renewed float switch setpoints, and pressure tested chamber (`{press} PSI`)."
            ],
            "parts": [
                ["Tandem Mechanical Seal Kit", "Dielectric Barrier Oil (2 Gal)", "Viton O-Ring Pack"],
                ["Double Mechanical Seal Assembly", "Seal Chamber Gasket Set"],
                ["Silicon Carbide Lower Seal Set", "Upper Carbon Seal", "Dielectric Oil"],
                ["Seal Repair Kit", "Retainer Ring", "O-Ring Set"],
                ["Tungsten Carbide Seal Cartridge", "Shaft Sleeve", "Dielectric Oil Fill"],
                ["SiC/SiC Mechanical Seal Kit", "Float Switch Assembly", "Chamber Gasket"]
            ],
            "downtime": (4.0, 7.5)
        },
        "clogging": {
            "symptoms": [
                "Sump pit level rising above high-water alarm setpoint (`+{thickness} inch`) despite pump running continuously at `{current}` Amps (`{volts}`).",
                "Pump motor current drop (`{percent}` below normal load amps to `{amps} Amps`) accompanied by zero flow discharge (`0 GPM`) and {adj} casing vibration.",
                "Loud {noise} and churning sound coming from submerged pump volute. Discharge check valve showing zero pressure (`{press_drop} PSI`).",
                "Ops reported pump running hot (`{temp}`\u00b0C) with severely restricted output flow (`{percent}` flow drop). Suspect ragball or solid debris blockage in volute.",
                "Flow rate degraded (`{gpm} GPM`, down `{percent}` from design). Pump cycling on high level alarm every `{hours}` minutes with {adj} churning noise.",
                "Submersible pump drawing fluctuating current (`{amps} Amps +/- {percent}`) with severe acoustic chattering (`{noise}`) inside intake bellmouth."
            ],
            "root_causes": [
                "Accumulation of fibrous wipes, rags, and solid debris (`{debris_amt}`) wrapped tightly around multi-vane impeller leading edges after `{hours}` hours.",
                "Sump bottom sludge and heavy silt ingestion (`{percent}` solids concentration) plugged volute discharge channel during heavy storm inflow (`{gpm} GPM`).",
                "Large solid debris (`{thickness} inch` diameter block) wedged between impeller shroud and volute tongue, locking impeller partially (`{torque}` stall torque).",
                "Inlet suction screen (`{mesh}`) completely blinded off (`{clog_pct}` blocked) by floating debris and grease buildup in wet well (`pH {ph_val}`).",
                "Check valve flapper downstream of pump jammed shut by calcified grease deposits (`{thickness} inch` thick), creating `{press} PSI` backpressure.",
                "Vortexing and air binding in volute chamber caused by improper baffle placement and heavy foam buildup (`{percent}` entrained air) during low inflow."
            ],
            "actions": [
                "Pulled pump out of wet well, manually cleared `{debris_amt}` fibrous ragball from impeller vanes, and flushed volute chamber with high-pressure hose (`{press} PSI`).",
                "Extracted pump unit, dislodged solid wooden debris wedged inside volute, cleared `{clog_pct}` blockage, and verified free manual rotation of impeller.",
                "Cleared clogged `{mesh}` suction screen and impeller passage; hydro-blasted wet well sump walls (`{press} PSI` water) to remove grease accumulation.",
                "Disassembled volute casing, removed `{debris_amt}` heavy silt/rag blockage, and checked impeller wear ring clearances (`{clearance} gap`).",
                "Removed discharge check valve, scraped `{thickness} inch` calcified grease deposits, freed flapper hinge (`{part_num}`), and flushed discharge piping (`{gpm} GPM`).",
                "Installed anti-vortex baffle plate (`{part_num}`) in wet well, cleared volute air lock, topped off level to `{percent}`, and verified steady pumping (`{gpm} GPM`)."
            ],
            "parts": [
                ["Suction Screen Fasteners", "Volute O-Ring"],
                ["None"],
                ["Volute Gasket Set", "Suction Screen Bolts"],
                ["Wear Ring Set", "Casing O-Ring"],
                ["Check Valve Flapper Rebuild Kit", "Flange Gasket 4-inch"],
                ["Anti-Vortex Baffle Plate", "Stainless Mounting Bolts"]
            ],
            "downtime": (1.5, 4.0)
        },
        "cable damage": {
            "symptoms": [
                "Intermittent phase loss alarms and grounding trips (`{amps} Amps`) on pump feed (`{volts}`). Cable outer sheath shows {adj} abrasion near wet well lip.",
                "Submersible power cable jacket split near guide rail clamp (`{thickness} inch` tear). Insulation resistance between conductors fluctuating severely (`{mg_ohm}`).",
                "Control panel showing earth fault (`{volts}`). Inspection of power cable drop revealed {adj} cuts and exposed copper armor (`{percent}` jacket loss).",
                "Pump lost power suddenly (`0 Amps` draw). Cable strain relief failed allowing cable weight (`{lbs_charge}`) to rub against concrete pit wall (`{vibe}` in/sec vibration).",
                "Ground fault leakage (`{mg_ohm}` insulation) tripped GFCI at `{amps} Amps`. Visual inspection showed swelling (`+{percent}` diameter) and blistering on outer neoprene cable sheath.",
                "Voltage drop across power drop cable (`{volts} loss`). Cable temperature near wet well entry gland elevated to `{temp}`\u00b0C (`normal < 45\u00b0C`)."
            ],
            "root_causes": [
                "Continuous vibration (`{vibe_rc}` in/sec RMS) and turbulence caused power cable to chafe against concrete edge of sump pit access hatch over `{hours}` hours.",
                "Improper clamping (`{torque}` torque) of cable strain relief allowed cable weight (`{lbs_charge}`) to pull on terminal entry gland, tearing outer polyurethane jacket.",
                "Accidental pinch damage (`{thickness} inch` indentation) during previous pump lifting and lowering operation along guide rail brackets.",
                "Chemical degradation (`pH {ph_val}` attack) and hardening of outer cable jacket from `{time_period}` immersion in industrial hydrocarbon effluent.",
                "Repeated flexing from pump starting torque (`{torque}` kick) cracked outer cable jacket near submersible cable entry gland (`{clearance} gap`).",
                "Thermal overload (`{amps} Amps` sustained draw) in ambient sunlight (`{temp_rc}`\u00b0C outside air) melted inner PVC conductor insulation inside conduit drop."
            ],
            "actions": [
                "Replaced damaged 50-foot section of submersible power cable (`{part_num}`), installed new heavy-duty cable entry gland (`{torque}` torque), and secured strain relief.",
                "Spliced and potted cable using marine-grade resin splice kit (`{part_num}`), and installed protective stainless abrasion sleeve (`{part_num}`) over guide rail area.",
                "Installed new multi-conductor submersible power drop cable (`{part_num}`), renewed terminal gland assembly (`{part_num}`), and tested continuity (`> 500 Mega-ohms`).",
                "Renewed power cable assembly (`{part_num}`), installed rubber guide rail chafing protectors (`{thickness} inch`), and re-torqued strain relief clamp (`{torque}`).",
                "Cut back damaged `{thickness} inch` jacket section, re-terminated leads with epoxy cable gland kit (`{part_num}`), and secured cable to guide chain using neoprene clamps.",
                "Replaced power cable run from disconnect (`{volts}` rating) to submersible gland (`{part_num}`), installed UV-resistant conduit jacket, and megger tested (`{mg_ohm}`)."
            ],
            "parts": [
                ["50ft Submersible Power Cable 4/0 AWG", "Cable Entry Gland Kit", "Strain Relief Grip"],
                ["Marine Resin Cable Splice Kit", "Stainless Abrasion Sleeve"],
                ["Submersible Power Drop Cable Assembly", "Terminal Gland O-Ring Set"],
                ["Power Cable Assembly", "Rubber Chafing Guard", "Gland Kit"],
                ["Epoxy Cable Gland Kit", "Neoprene Cable Clamps (4x)", "Terminal Lugs"],
                ["Submersible Power Cable (75ft)", "UV Conduit Jacket", "Entry Gland Assembly"]
            ],
            "downtime": (3.5, 6.5)
        }
    },
    "Induction Motor": {
        "bearing wear": {
            "symptoms": [
                "Motor drive-end bearing housing temperature reaching `{temp}`\u00b0C (`alarm > 85\u00b0C`). High frequency acoustic vibration (`{vibe}` in/sec RMS) detected.",
                "Loud {adj} whining and {noise} sound emanating from motor non-drive end bearing during operation at `{hz}`.",
                "Vibration analysis indicates severe inner race defect frequencies (BPFI) on motor drive-end bearing (`{vibe}` in/sec RMS) with `{degree}` harmonics.",
                "Tech noted {adj} grease discoloration (`{ppm}` iron debris) leaking from bearing grease relief tube and metallic clattering (`{noise}`).",
                "Severe {noise} audible near drive coupling. Motor bearing temperature elevated (`{temp}`\u00b0C) with `{degree}` radial vibration (`{vibe}` in/sec RMS).",
                "High envelope acceleration (`g-E`) detected across drive-end bearing. Oil/grease sampling confirmed `{ppm}` particulate wear debris."
            ],
            "root_causes": [
                "Grease dry-out and thermal degradation due to operating in elevated ambient temperature environment (`{temp_rc}`\u00b0C housing temp) after `{hours}` hours.",
                "Over-greasing by maintenance personnel caused excessive churning heat (`{temp_rc}`\u00b0C) and blown grease retainer seals (`{thickness} inch` gap).",
                "Shaft voltage discharge (EDM currents of `{volts}`) from VFD switching transients caused fluting and micro-pitting on bearing raceways.",
                "Normal fatigue wear of deep groove ball bearings (`{gap} inch` race play) after exceeding `{hours}` hours of continuous operating life.",
                "Improper drive belt tension (`{torque}` over-tension) applied radial load exceeding bearing C values, causing premature race spalling.",
                "Contamination of bearing grease with ambient chemical dust (`{ppm}` solids) through defective shaft labyrinth seal (`{clearance} gap`)."
            ],
            "actions": [
                "De-coupled motor, removed bearing end shields, replaced both DE and NDE bearings with C3 clearance ball bearings (`{part_num}`), and packed with Polyrex EM (`{percent}` fill).",
                "Replaced drive-end and non-drive-end bearings (`{part_num}`), installed shaft grounding ring (`{part_num}`) to mitigate VFD bearing currents, and realigned unit within `{clearance} gap`.",
                "Replaced worn bearing set (`{part_num}`), cleaned grease cavities of `{ppm}` debris, installed new grease relief valves, and balanced rotor assembly (`G2.5`).",
                "Disassembled motor, installed insulated NDE bearing and standard DE bearing (`{part_num}`), verified proper clearance (`{clearance} gap`), and tested smooth running (`{vibe}` in/sec).",
                "Pulled motor end shield, pressed on new roller bearing set (`{part_num}`), adjusted belt tension to `{torque}`, and verified temperature stabilized at `{temp}`\u00b0C.",
                "Replaced DE/NDE bearings (`{part_num}`), installed upgraded non-contact INPRO labyrinth shaft seals (`{part_num}`), and greased with Polyrex EM (`{percent}` fill)."
            ],
            "parts": [
                ["SKF 6312-C3 Drive-End Bearing", "SKF 6310-C3 NDE Bearing", "Polyrex EM Grease (1 Tube)"],
                ["DE Ball Bearing", "NDE Insulated Bearing", "AEGIS Shaft Grounding Ring Kit"],
                ["Bearing Kit (DE & NDE)", "Lip Seals", "Bearing Housing Gasket"],
                ["SKF Deep Groove Ball Bearing Set", "Grease Valve Kit", "End Shield Gasket"],
                ["Heavy Duty Roller Bearing Set", "Belt Tensioning Bolts", "Lip Seal Kit"],
                ["Precision Ball Bearing C3 Set", "INPRO Labyrinth Seal Kit", "Polyrex EM Grease"]
            ],
            "downtime": (4.0, 7.5)
        },
        "winding insulation failure": {
            "symptoms": [
                "Motor tripped main overload and instantaneous ground fault protection (`{amps} Amps`). Stator shows `{temp}`\u00b0C localized hotspot on IR scan.",
                "Strong {adj} smell of burnt varnish from motor cooling fan shroud. Megger test reads `{mg_ohm}` between Phase A and ground (`{volts}`).",
                "Phase current imbalance exceeding `{percent}` (`{current}` Amps Phase A vs normal Phase B/C). Motor running extremely rough (`{vibe}` in/sec RMS).",
                "Main breaker tripped instantly (`{amps} Amps` fault) upon energization at `{volts}`. Stator surge comparison test confirmed turn-to-turn short in phase coil.",
                "High leakage current (`{mg_ohm}` insulation resistance) to earth. Stator winding temperature RTD spiked abruptly to `{temp}`\u00b0C before trip.",
                "Stator phase winding failed during high-load ramp (`{amps} Amps`). Polarization Index (PI) dropped to `{tan_delta}` with {adj} smoke from terminal box."
            ],
            "root_causes": [
                "Age-related thermal brittleness of Class F winding insulation accelerated by frequent motor start/stop cycles over `{hours}` operating hours.",
                "Voltage spikes (`> {volts} peak`) from VFD switching transients exceeded insulation dielectric breakdown threshold (`{mg_ohm}` remaining resistance).",
                "Contamination of stator coils with airborne conductive dust (`{ppm}`) and moisture (`RH > {percent}`) due to missing terminal box gasket.",
                "Overloading motor beyond `1.15` service factor (`drawing {percent}` above rated `{amps} Amps`) during peak production caused sustained copper heating (`{temp_rc}`\u00b0C).",
                "Partial discharge (corona) degradation inside stator end turns under `{volts}` operation, eroding slot insulation over `{time_period}`.",
                "Localized stator core lamination short (`{temp_rc}`\u00b0C hotspot) burnt through adjacent winding slot liner during `{hours}` hours of high-load running."
            ],
            "actions": [
                "Removed motor from base plate, transported to electrical rebuild facility for complete Class H stator rewind (`{part_num}`) and VPI resin dip (`{tan_delta}` test).",
                "Swapped out failed motor with certified warehouse spare unit (`{part_num}`); sent damaged stator for rewind and core loss testing (`{tan_delta}`).",
                "Replaced motor with premium efficiency spare (`{part_num}`), installed line reactor (`{part_num}`) on VFD output (`{volts}`), and renewed terminal box seals.",
                "Performed complete motor replacement (`{part_num}`), renewed lead lugs (`{torque}` torque), and verified dynamic balance (`{vibe}` in/sec) and laser alignment (`{clearance} gap`).",
                "Rewound stator coils with corona-resistant inverter-grade magnet wire (`{part_num}`), applied double epoxy VPI dip, and megger tested (`> 1000 Mega-ohms`).",
                "Disassembled motor, performed lamination core restacking and acid burn, completed Class H rewind (`{part_num}`), and tested under full load (`{amps} Amps` at `{volts}`)."
            ],
            "parts": [
                ["Class H Stator Rewind Service", "Motor Lead Lug Kit", "Terminal Box Gasket"],
                ["Complete Replacement Induction Motor 50HP", "Coupling Key", "Shim Pack"],
                ["Stator Rewind Kit", "VFD Output Line Reactor", "Terminal Gasket Set"],
                ["Warehouse Spare Induction Motor Assembly", "Mounting Bolt Set", "Lead Connectors"],
                ["Inverter-Grade Magnet Wire Set", "Class H Slot Liners", "VPI Epoxy Resin"],
                ["Stator Lamination Restack Kit", "Rewind Coil Set Class H", "Lead Wire Assembly"]
            ],
            "downtime": (8.0, 12.0)
        },
        "overheating": {
            "symptoms": [
                "Motor frame temperature exceeding `{temp}`\u00b0C measured across cooling fins. RTD sensors indicating winding temp near `{temp_rc}`\u00b0C (`alarm limit 140\u00b0C`).",
                "Thermal overload relay tripped after `{hours}` hours of continuous running (`{amps} Amps`). Cooling fan shroud feels {adj} hot to the touch.",
                "Ops reported strong heat waves radiating from motor frame (`{temp}`\u00b0C) and `{percent}` drop in operating speed (`RPM`).",
                "Stator RTD temperature alarm active (`{temp}`\u00b0C). Motor drawing `{current}` Amps (`{percent}` FLA) with {adj} thermal buildup on frame.",
                "Motor casing temperature elevated (`+{temp}`\u00b0C above ambient). Winding resistance increased due to excessive copper temperature (`{temp_rc}`\u00b0C).",
                "Continuous thermal cycling alarms (`{temp}`\u00b0C trip setpoint). Cooling airflow exiting fan cover feels severely restricted (`{percent}` drop)."
            ],
            "root_causes": [
                "External cooling fins heavily caked (`{thickness} inch` thick layer) with thick industrial dust and grease, reducing convective heat transfer by `{percent}`.",
                "External cooling fan cover grid clogged (`{clog_pct}` blocked) with lint and debris, blocking cooling airflow across motor frame after `{time_period}`.",
                "Voltage unbalance of `{percent}` across supply lines (`{volts}`) caused `{percent}` increase in localized rotor and stator copper heating (`{temp_rc}`\u00b0C).",
                "Running motor at low RPM (`< {hz}`) via VFD without auxiliary blower forced-air cooling, leading to severe thermal stagnation (`{temp_rc}`\u00b0C).",
                "Broken external cooling fan blade (`{percent}` fan area lost) caused loss of turbulent airflow across cooling ribs under `{amps} Amps` load.",
                "High ambient air temperature (`{temp_rc}`\u00b0C inside enclosure) combined with heavy duty cycle (`{percent}` load) exceeded thermal dissipation capacity."
            ],
            "actions": [
                "De-energized motor, removed fan cover, and thoroughly cleaned cooling fins (`{thickness} inch` buildup removed) and fan blades using dry compressed air and degreaser.",
                "Cleared `{clog_pct}` blockage from cooling fan intake grid, washed frame fins, and verified balanced supply voltage (`{volts}` +/- 1%).",
                "Installed auxiliary cooling blower unit (`{part_num}`) for low-speed VFD operation (`< {hz}`) and cleaned existing motor frame cooling channels (`{percent}` airflow restored).",
                "Corrected upstream tap settings on transformer to balance phase voltage (`{volts}`), deep cleaned motor heat sink fins, and verified winding temp dropped (`-{temp}`\u00b0C).",
                "Replaced damaged polypropylene cooling fan (`{part_num}`), straightened bent fan cowl (`{clearance} gap`), and verified full airflow restoration (`{temp}`\u00b0C housing).",
                "Installed ventilation louver fans in enclosure (`{part_num}`), washed motor frame (`{ppm}` debris cleared), and verified operating temperature stabilized (`{temp}`\u00b0C)."
            ],
            "parts": [
                ["Industrial Degreaser Solvent (2 Cans)", "Replacement Fan Guard Screws"],
                ["None"],
                ["Auxiliary Forced-Air Blower Kit 460V", "Fan Shroud Mounting Brackets"],
                ["Cooling Fan Blade Assembly", "Shroud Fasteners", "Fan Guard Grid"],
                ["Polypropylene Replacement Cooling Fan", "Cowl Hardware Kit"],
                ["Enclosure Exhaust Fan Unit", "Motor Frame Cleaning Kit"]
            ],
            "downtime": (1.5, 4.0)
        },
        "rotor imbalance": {
            "symptoms": [
                "1X RPM radial vibration (`{vibe}` in/sec RMS) dominant across both motor bearing housings. Vibration amplitude increases with motor speed (`{hz}`).",
                "High horizontal vibration measured at motor drive-end (`{vibe}` in/sec RMS, `{percent}` above ISO 10816 alarm threshold). Unit humming loudly (`{noise}`).",
                "Strong physical vibration (`{vibe}` in/sec RMS) felt on motor baseplate. Spectrum analysis confirms pure once-per-revolution (`1X`) imbalance frequency.",
                "Motor shaking severely (`{vibe}` in/sec RMS) right after routine cleaning. No electrical anomalies detected on phase currents (`{amps} Amps`).",
                "Radial vibration velocity (`{vibe}` in/sec RMS) peaking at `1X` running speed (`{hz}`). Phase angle steady across drive-end bearing pedestal.",
                "Elevated 1X rotational vibration (`{vibe}` in/sec RMS) causing structural looseness (`{gap} inch` play) on motor foot shims."
            ],
            "root_causes": [
                "Loss of balancing weight (`{debris_amt}` mass detached) from cooling fan or rotor end ring due to vibration fatigue (`{vibe_rc}` in/sec) over `{hours}` hours.",
                "Uneven accumulation of heavy dried process cake and dirt (`{thickness} inch` layer) inside rotor cooling channels and external fan blades.",
                "Thermal bowing (`{runout} inch` deflection) of rotor shaft caused by previous localized stator winding hotspot (`{temp_rc}`\u00b0C) during high load run.",
                "Slight bending of motor shaft (`{runout} inch` runout at journal) resulting from historical mechanical jam (`{torque}` spike) on driven equipment coupling.",
                "Porosity and casting voids (`{thickness} inch` void) inside aluminum rotor short-circuit rings that shifted after `{hours}` thermal cycles (`{temp_rc}`\u00b0C).",
                "Improper key length (`{gap} inch` excess key protruding) installed on drive coupling extension during previous coupling replacement."
            ],
            "actions": [
                "Disassembled cooling fan shroud, cleaned rotor assembly (`{debris_amt}` dirt cleared), and performed in-situ two-plane dynamic field balancing using trim weights (`{part_num}`).",
                "Removed rotor from stator, cleaned debris from cooling slots, checked shaft runout on lathe (`{runout} inch`), and dynamically balanced rotor to G2.5 grade (`{vibe}` in/sec).",
                "Replaced cracked external cooling fan (`{part_num}`), cleaned rotor end rings, and applied trim balance weights (`{part_num}`) to drive-end balance plane.",
                "Re-balanced rotor assembly in field using dual-channel vibration analyzer, applying `{debris_amt}` balance correction and reducing 1X peak below `{vibe}` in/sec RMS.",
                "Extracted rotor, machined end rings to true balance plane (`{clearance} tolerance`), balanced dynamically (`G1.0`), and verified smooth running (`{vibe}` in/sec RMS).",
                "Replaced half-key on coupling shaft extension with precision stepped key (`{part_num}`), re-laser aligned (`{clearance} gap`), and verified 1X vibration dropped (`{vibe}` in/sec)."
            ],
            "parts": [
                ["Dynamic Balancing Trim Weight Kit", "Fan Shroud Fasteners"],
                ["Replacement Cooling Fan Assembly", "Shaft Key", "Balancing Weights"],
                ["Rotor Balancing Clip Set", "External Cooling Fan"],
                ["None"],
                ["Precision Dynamic Balancing Weight Set", "End Ring Clip Kit"],
                ["Precision Stepped Shaft Key", "Coupling Shim Pack"]
            ],
            "downtime": (4.5, 8.5)
        }
    },
    "Air Compressor": {
        "valve failure": {
            "symptoms": [
                "Compressor unable to build discharge pressure above `{press}` PSI (`target {press} PSI`). High interstage temperature (`{temp}`\u00b0C) on stage 1 cylinder.",
                "Loud {adj} metallic clicking and {noise} inside compressor cylinder head during compression stroke. Capacity down by `{degree}` (`{percent}` drop).",
                "High discharge temperature trip (`> {temp_rc}\u00b0C`) activated. Air blowing back through intake air filter assembly during unloader cycle (`{press_drop} PSI`).",
                "Ops noted compressor running continuously without unloading (`{current}` Amps draw) and failing to reach header setpoint (`{press} PSI`).",
                "Stage 2 intercooling pressure fluctuating (`{press} PSI +/- {percent}`). Severe acoustic impact (`{noise}`) detected inside discharge valve pocket.",
                "Discharge temperature differential spiked (`+{temp}`\u00b0C across stage 2). Compressor output flow reduced (`-{percent}` SCFM) with {adj} clattering."
            ],
            "root_causes": [
                "Fatigue fracture of stainless steel valve plate/reed inside discharge valve assembly due to billions of cyclic flexures over `{hours}` hours.",
                "Carbon deposit buildup (`{thickness} inch` thick) on valve seat caused by oil carryover (`{ppm}`) and high operating temperatures (`{temp_rc}`\u00b0C).",
                "Broken valve spring (`{part_num}`) allowed valve disc to flutter and slam against guard, cracking valve seating surface under `{press} PSI` cycling.",
                "Ingestion of particulate grit (`{ppm}` concentration) through torn air intake filter element (`{mesh}`) eroded suction valve sealing face.",
                "Over-torquing of valve cover hold-down bolts (`{torque}`) warped valve seat assembly by `{runout} inch`, causing internal blow-by.",
                "Corrosive chemical vapor (`pH {ph_val}`) drawn through intake air stream pitted stainless reed valves during `{hours}` hours of runtime."
            ],
            "actions": [
                "Isolated compressor, removed cylinder head, and replaced complete suction and discharge valve assemblies (`{part_num}`) and gaskets (`{part_num}`).",
                "Disassembled valve pockets, cleaned carbon buildup using chemical solvent (`{ppm}` cleared), and installed new reed valve rebuild kits (`{part_num}`).",
                "Replaced broken stage 1 and stage 2 discharge valve assemblies (`{part_num}`), renewed head gaskets, and replaced intake air filter element (`{part_num}`).",
                "Installed new valve plates, springs, and seats (`{part_num}`); torqued head bolts to factory specification (`{torque}`) and tested capacity (`{press} PSI`).",
                "Rebuilt concentric valve assemblies (`{part_num}`), honed valve seating pockets (`{clearance} tolerance`), and verified interstage pressure (`{press} PSI`).",
                "Swapped out stage 1 and 2 valve packs (`{part_num}`), replaced O-ring seals (`{part_num}`), and verified volumetric efficiency (`+{percent}` flow)."
            ],
            "parts": [
                ["Suction and Discharge Valve Assembly Kit", "Cylinder Head Gasket Set"],
                ["Valve Rebuild Kit (Plates, Springs, Seats)", "High-Temp Head Gaskets"],
                ["Stage 1 Discharge Valve Assembly", "Stage 2 Valve Kit", "Intake Filter Element"],
                ["Reed Valve Replacement Pack", "Valve Cover O-Ring Set", "Fastener Kit"],
                ["Concentric Valve Rebuild Kit", "Valve Pocket O-Rings", "Synthetic Lubricant"],
                ["Suction Valve Pack Stage 1", "Discharge Valve Pack Stage 2", "Gasket Kit"]
            ],
            "downtime": (3.5, 6.5)
        },
        "oil contamination": {
            "symptoms": [
                "Oil sight glass shows {adj} dark, foamy oil with heavy sludge formation. Compressor running `{temp}`\u00b0C above normal discharge temp (`alarm 105\u00b0C`).",
                "High differential pressure alarm (`> {press_drop} PSI`) triggered across air/oil separator element. Excessive oil carryover (`{ppm}` aerosol) into plant air header.",
                "Oil analysis report indicates high acid number (`TAN > {tan_delta}`) and severe particulate depletion (`{ppm}` wear metals) of anti-wear additives.",
                "Compressor oil filter bypass indicator tripped red (`{press_drop} PSI` differential). Tech observed `{degree}` oil varnish buildup inside reservoir sampling port.",
                "Oil reservoir foaming alarm triggered (`+{thickness} inch` foam layer). Air/oil separator pressure drop climbed from 3 PSI to `{press_drop} PSI`.",
                "Oil sampling revealed `{ppm}` moisture content (`cloudy emulsion`). Discharge air carryover exceeding `{ppm}` oil concentration downstream."
            ],
            "root_causes": [
                "Operating compressor past recommended `{hours}` hour oil change interval caused thermal oxidation (`TAN {tan_delta}`) and breakdown of synthetic lubricant.",
                "Ingestion of humid, chemically contaminated intake air (`RH > {percent}`, `pH {ph_val}`) from chemical bath accelerated oil sludge formation.",
                "Mixing of incompatible lubricant brands (`polyglycol vs PAO`) during top-off by operations caused chemical precipitation and heavy foaming (`{percent}` volume increase).",
                "Failure of thermostatic bypass valve (`stuck at {temp_rc}\u00b0C`) caused oil to run continuously chilled, allowing condensate moisture (`{ppm}`) to emulsify.",
                "Air/oil separator element rupture (`{thickness} inch` tear) caused by differential pressure spikes (`> {press} PSI`) during rapid load/unload cycling.",
                "Overheating of oil (`{temp_rc}`\u00b0C sump temp) caused accelerated thermal coking and heavy varnish deposition across separator filter media."
            ],
            "actions": [
                "Drained degraded compressor oil, flushed oil sump with cleaning solvent (`{part_num}`), replaced air/oil separator (`{part_num}`) and oil filter, and refilled with synthetic ISO VG 46 (`{lbs_charge}`).",
                "Performed complete oil system flush, replaced spin-on oil filter and separator cartridge (`{part_num}`), and verified thermostatic valve operation (`{temp}`\u00b0C).",
                "Drained contaminated fluid (`{ppm}` moisture), replaced thermostatic mixing valve element (`{part_num}`), renewed filters, and filled with certified compressor lubricant (`{part_num}`).",
                "Flushed reservoir, replaced oil filter and separator element (`{part_num}`), cleaned thermal bypass valve (`{clearance} gap`), and took fresh baseline oil sample.",
                "Installed upgraded coalescence separator element (`{part_num}`), drained emulsified oil (`{lbs_charge}`), flushed sump, and verified `< 2 ppm` carryover.",
                "Replaced separator element (`{part_num}`), cleaned reservoir interior (`{thickness} inch` varnish stripped), renewed spin-on filter (`{part_num}`), and recharged synthetic oil."
            ],
            "parts": [
                ["Synthetic Compressor Oil ISO VG 46 (5 Gal)", "Air/Oil Separator Element", "Spin-On Oil Filter"],
                ["Oil Filter Cartridge", "Separator Kit", "Compressor Flushing Fluid (2 Gal)", "Synthetic Lube Oil"],
                ["Thermostatic Bypass Valve Element", "Oil Filter Assembly", "Separator Element", "ISO VG 46 Lube"],
                ["Complete Maintenance Filter & Oil Kit (Separator, Oil Filter, Air Filter, Oil)"],
                ["Coalescing Air/Oil Separator", "Synthetic PAO Oil (10 Gal)", "Flushing Solvent"],
                ["Separator Element Kit", "Spin-On Lube Filter", "Varnish Cleaner (2 Gal)", "ISO 46 Oil"]
            ],
            "downtime": (2.0, 4.5)
        },
        "overheating": {
            "symptoms": [
                "High air discharge temperature trip (`{temp}`\u00b0C) shut down compressor package. Oil cooler radiator feels {adj} hot across all passes (`{temp_rc}`\u00b0C).",
                "Compressor cycling on high temp interlock (`> {temp_rc}\u00b0C`). Cooling fan running (`{hz}`) but `{degree}` temperature drop across aftercooler (`{temp}`\u00b0C out).",
                "Thermal warning alarm active on compressor controller (`{temp}`\u00b0C). Unit operating at `{current}` Amps with {adj} heat buildup inside acoustic enclosure.",
                "Air discharge temp steadily climbing over past `{hours}` operating hours, reaching `{temp}`\u00b0C during peak shift demands (`{press} PSI`).",
                "Oil injection temperature reaching `{temp}`\u00b0C (`normal < 85\u00b0C`). Thermal bypass valve indicator showing maximum cooling flow without temperature drop.",
                "Compressor cabinet temperature high (`{temp}`\u00b0C). Discharge air temp exceeding `{temp_rc}`\u00b0C with {adj} heat radiation from cooler core."
            ],
            "root_causes": [
                "External fins of air/oil cooler core heavily fouled (`{clog_pct}` blocked) with industrial airborne dust and oily mist accumulation after `{time_period}`.",
                "Thermal bypass valve failed in closed position (`stuck at {temp_rc}\u00b0C`), preventing hot oil from circulating through external cooler core under `{current}` Amps load.",
                "Internal oil cooler passages partially plugged with oil varnish deposits (`{thickness} inch` layer), reducing heat transfer efficiency by `{percent}`.",
                "Low oil level (`-{percent}` volume) in compressor sump due to gradual carryover past aging separator element over `{hours}` hours.",
                "Cooling fan blade angle distortion (`{runout} inch` runout) reduced airflow velocity across heat exchanger matrix by `{percent}`.",
                "Acoustic enclosure ventilation exhaust duct plugged (`{clog_pct}` blocked), trapping `{temp_rc}`\u00b0C hot air inside compressor package."
            ],
            "actions": [
                "Pressure washed air/oil cooler radiator exterior fins (`{clog_pct}` dirt cleared) with biodegradable degreaser (`{part_num}`) and blown dry with low-pressure air (`{press} PSI`).",
                "Replaced faulty thermostatic oil bypass valve assembly (`{part_num}`), topped off compressor oil level (`{lbs_charge}`), and cleaned cooler core exterior.",
                "Circulated chemical descaling/de-varnishing agent (`{part_num}`) through internal cooler passages, flushed system (`{gpm} GPM`), and replaced oil filter (`{part_num}`).",
                "Cleaned cooler core fins, adjusted cabinet ventilation louvers (`{clearance} gap`), and verified discharge temperature stabilized at `{temp}`\u00b0C under full load (`{press} PSI`).",
                "Replaced cooling fan assembly (`{part_num}`), straightened bent cooler fins (`{clearance} gap`), and verified temperature differential (`{temp}`\u00b0C delta).",
                "Cleared acoustic cabinet exhaust ducting (`{clog_pct}` obstruction removed), washed cooler radiator (`{part_num}`), and verified steady discharge (`{temp}`\u00b0C)."
            ],
            "parts": [
                ["Coil Cleaning Degreaser (2 Gallons)", "Replacement Cooler Core Gaskets"],
                ["Thermostatic Oil Bypass Valve Kit", "Compressor Oil (1 Gal)", "O-Ring Set"],
                ["De-Varnishing Chemical Flush (5 Gal)", "Spin-On Oil Filter", "Cooler Gasket Kit"],
                ["Cabinet Ventilation Filter Pad", "Oil Top-off Bottle", "Louver Linkage"],
                ["Replacement Cooling Fan Blade", "Fin Comb Tool", "Cooler Hardware"],
                ["Enclosure Exhaust Duct Louvers", "Radiator Degreaser (2 Cans)", "Filter Pad"]
            ],
            "downtime": (2.5, 5.0)
        },
        "belt wear": {
            "symptoms": [
                "Loud {adj} squealing and {noise} sound from compressor drive belt guard during startup (`{current}` Amps inrush) and loading cycles (`{press} PSI`).",
                "Belt slip alarm triggered (`{degree}` RPM mismatch between motor and compressor end). Black rubber dust accumulating under drive guard (`{thickness} inch` pile).",
                "Drive belts show {adj} side wear (`{thickness} inch` width loss), fraying cords, and glazing across pulley contact surfaces. Tension significantly degraded.",
                "Tech observed visual vibration and whipping of drive belts across sheaves (`{vibe}` in/sec RMS on bearing frame at `{hz}`).",
                "Compressor speed dropping during load cycle (`{percent}` slip). Severe {noise} audible near drive sheave with {adj} burnt rubber smell.",
                "Belt tension sensor alarm (`< {torque}` static tension). Visual inspection revealed cracked cogs (`{percent}` cracked) across matched V-belt set."
            ],
            "root_causes": [
                "Normal mechanical wear and stretching (`+{thickness} inch` elongation) of V-belts after exceeding `{hours}` hours of continuous loading/unloading duty.",
                "Improper initial belt tensioning (`{torque}` loose) allowed slippage (`{percent}` slip) and frictional glazing during high torque starts (`{current}` Amps).",
                "Misalignment between motor drive sheave and compressor driven sheave (`{runout} inch` offset, `> 0.5 degrees` angular) caused rapid sidewall abrasion.",
                "Oil mist drip (`{ppm}` contamination) from minor shaft seal leak contaminated V-belt rubber, causing softening and loss of friction grip (`{percent}` grip loss).",
                "Worn sheave grooves (`{gap} inch` dished profile) allowed V-belt bottoming out, reducing wedging clamping force by `{percent}`.",
                "Thermal degradation (`{temp_rc}`\u00b0C ambient inside guard) caused premature elastomer hardening and cross-cracking across belt ribs."
            ],
            "actions": [
                "Locked out unit, removed belt guard, replaced matched set of 4 V-belts (`{part_num}`), laser aligned sheaves (`{clearance} gap`), and tensioned to sonic gauge spec (`{hz}`).",
                "Replaced worn drive belt set (`{part_num}`), realigned motor sheave using precision laser tool (`{runout} inch` tolerance), and re-tensioned after 24-hour run-in.",
                "Cleaned oil mist off sheave grooves using solvent (`{part_num}`), installed new matched V-belt set (`{part_num}`), and adjusted motor slide base tension (`{torque}`).",
                "Swapped out glazed V-belts with new matched set (`{part_num}`), verified pulley groove profiles for wear (`{clearance} tolerance`), and torqued slide rail bolts (`{torque}`).",
                "Replaced both drive and driven sheaves (`{part_num}`) due to groove wear, installed cogged V-belt pack (`{part_num}`), and laser aligned (`{clearance} gap`).",
                "Replaced drive belt set (`{part_num}`), installed shaft seal repair kit (`{part_num}`) to stop oil drip, and tensioned belts to sonic frequency (`{hz}`)."
            ],
            "parts": [
                ["Matched Set of 4 V-Belts (VX-120)", "Sheave Bushing Kit"],
                ["Heavy Duty V-Belt Set (3-Pack)", "Solvent Cleaner (1 Can)", "Laser Target"],
                ["Cogged V-Belt Matched Set (BX-68)", "Slide Base Bolt Set"],
                ["Replacement Drive Belt Kit", "Sheave Lock Bushings", "Tension Bolts"],
                ["Drive Sheave Assembly", "Driven Pulley Sheave", "Cogged V-Belt Set (4x)"],
                ["Matched V-Belt Pack", "Compressor Shaft Lip Seal", "Belt Degreaser"]
            ],
            "downtime": (1.5, 3.5)
        }
    },
    "Refrigerated Air Dryer": {
        "refrigerant leak": {
            "symptoms": [
                "Air dryer dew point gauge reading `{temp}`\u00b0C (high dew point alarm active). Suction pressure on refrigerant compressor reading near `0` PSI (`target {press} PSI`).",
                "Compressor short cycling (`{hz}`) on low-pressure cutout switch (`< {press} PSI`). Tech observed {adj} oil residue on copper brazed joint near evaporator.",
                "Compressed air exiting dryer feels humid (`{degree}` moisture present, `{percent}` RH). Refrigerant sight glass shows bubbles and low charge indicator.",
                "Dryer refrigeration compressor hot to touch (`{temp}`\u00b0C) and tripping on low suction pressure cutoff (`{press_drop} PSI`) during afternoon shift.",
                "Evaporator approach temperature expanded to `{temp}`\u00b0C (`normal < 3\u00b0C`). Discharge line frost (`{thickness} inch` buildup) indicating starved evaporator coil.",
                "Hot gas bypass valve fully open (`{percent}`) but dew point remains high (`{temp}`\u00b0C). Leak detection dye visible near condenser return bend."
            ],
            "root_causes": [
                "Vibration fatigue (`{vibe_rc}` in/sec RMS) cracked copper capillary tube at brazed connection to hot gas bypass valve manifold after `{hours}` hours.",
                "Corrosion pinhole (`{gap} inch` diameter) developed inside air-to-refrigerant heat exchanger due to acidic condensate (`pH {ph_val}`) accumulation.",
                "Fretting wear between rubbing copper refrigerant lines (`{thickness} inch` worn away) inside cabinet wore through tubing wall over `{time_period}`.",
                "Degraded Schrader access valve core O-ring (`{part_num}`) allowed slow loss of R-134a/R-407C refrigerant charge (`-{percent}` loss) over past 6 months.",
                "Thermal expansion stress fractured condenser coil U-bend brazed joint (`{clearance} gap` crack) due to blocked cooling fan (`{temp_rc}`\u00b0C).",
                "Compressor discharge line vibration (`{hz}` frequency) work-hardened and cracked the copper stub-out at the hermetic shell weld."
            ],
            "actions": [
                "Recovered remaining refrigerant charge, repaired cracked capillary tube brazed joint with 15% silver solder (`{part_num}`), evacuated to 500 microns, and weighed in factory charge of R-134a (`{lbs_charge}`).",
                "Located leak using electronic leak detector, repaired rubbed copper tubing section, replaced liquid line filter drier (`{part_num}`), evacuated system, and recharged with R-407C (`{lbs_charge}`).",
                "Replaced leaking Schrader valve cores and service caps (`{part_num}`), pulled deep vacuum to verify holding, and recharged refrigerant to nameplate specification (`{lbs_charge}`).",
                "Repaired pinhole braze leak at evaporator inlet header, installed new bi-flow filter drier (`{part_num}`), and charged unit with precise weight of R-134a (`{lbs_charge}`).",
                "Brazed fractured condenser U-bend (`{part_num}`), pressure tested with nitrogen (`{press} PSI`), evacuated to 300 microns, and weighed in `{lbs_charge}` of R-134a.",
                "Cut out cracked discharge line section, silver-brazed new vibration loop (`{part_num}`), changed liquid line drier, and pulled vacuum before recharging `{lbs_charge}`."
            ],
            "parts": [
                ["R-134a Refrigerant (5 lbs)", "Liquid Line Filter Drier", "15% Silver Braze Rods"],
                ["R-407C Refrigerant Charge (8 lbs)", "Hermetic Filter Drier", "Copper Tubing Section"],
                ["Schrader Valve Cores & Brass Caps", "R-134a Refrigerant (4 lbs)", "Filter Drier Element"],
                ["Filter Drier Core Assembly", "Braze Alloy", "R-134a Refrigerant Bottle"],
                ["Condenser U-Bend Fitting", "Nitrogen Test Gas (1 Cyl)", "R-134a (6 lbs)"],
                ["Vibration Absorber Loop 3/8\"", "Silver Solder Kit", "R-407C (5 lbs)"]
            ],
            "downtime": (3.5, 7.0)
        },
        "condensate drain clog": {
            "symptoms": [
                "Liquid water blowing down downstream compressed air lines (`{degree}` moisture in plant header). Dryer automatic drain valve silent (`{hz}`).",
                "Water sight level glass on moisture separator bowl completely full of liquid (`{percent}` capacity). Electronic drain solenoid clicking but no water discharging.",
                "High condensate water level alarm triggered on air dryer separator basin. Water pooling (`{thickness} inch` depth) around bottom cabinet base.",
                "Ops noted heavy liquid water spray (`{gpm} GPM`) when blowing down downstream pneumatic regulator bowls. Dryer separator drain stuck closed.",
                "Compressed air dew point reading normal (`{temp}`\u00b0C) but downstream coalescing filters rapidly flooding with liquid condensate (`{percent}` saturation).",
                "Zero-loss drain trap displaying fault code (`drain fault {hz}`). Manual override button fails to discharge any condensate from separator bowl."
            ],
            "root_causes": [
                "Accumulation of rust scales, pipe dope, and oily emulsion sludge (`{thickness} inch` thick) clogged inlet strainer of electronic zero-loss drain valve.",
                "Solenoid coil burnout (`{volts}` supply spike) on automatic condensate drain valve (`open circuit` measured across coil terminals).",
                "Internal float mechanism of pneumatic zero-loss drain jammed shut due to heavy rust particles (`{ppm}`) from aging inlet piping.",
                "Degradation of drain valve internal diaphragm/seal (`{percent}` torn) preventing pilot opening during timed drain discharge cycles (`{hz}`).",
                "Control board failure inside electronic drain trap housing (`{volts}` component burnout) stopped firing the discharge solenoid valve.",
                "Winter freeze-up (`ambient < 0\u00b0C`) of condensate drain discharge line (`{length} ft` run) caused ice blockage, backing up water into separator."
            ],
            "actions": [
                "Isolated and bypassed drain line, disassembled electronic zero-loss drain valve (`{part_num}`), cleaned strainer mesh of rust sludge, and rebuilt solenoid valve.",
                "Replaced burned-out 24V solenoid coil (`{part_num}`) and internal diaphragm repair kit on automatic condensate drain assembly; tested manual blowdown (`{press} PSI`).",
                "Replaced jammed internal float assembly with upgraded heavy-duty electronic zero-loss condensate drain trap (`{part_num}`) and flushed separator bowl (`{gpm} GPM`).",
                "Disassembled and cleaned moisture separator sump, installed new drain solenoid valve rebuild kit (`{part_num}`), and verified timed discharge cycles (`{hz}`).",
                "Replaced failed zero-loss drain control module (`{part_num}`), cleaned internal capacitance sensor probes (`{clearance} gap`), and verified auto-discharge.",
                "Thawed frozen discharge line with heat gun, installed self-regulating heat trace cable (`{part_num}`) over `{length} ft` run, and insulated drain piping."
            ],
            "parts": [
                ["Electronic Zero-Loss Drain Solenoid Valve Rebuild Kit", "Drain Strainer Mesh"],
                ["24V Drain Solenoid Coil", "Diaphragm Repair Kit", "Bowl O-Ring"],
                ["Heavy-Duty Electronic Drain Trap Assembly", "Strain Mesh Filter"],
                ["Automatic Drain Rebuild Kit", "Separator Bowl Gasket"],
                ["Drain Trap Control Module PCB", "Capacitance Probe Cleaning Pad"],
                ["Heat Trace Cable Kit (10ft)", "Pipe Insulation", "Zip Ties"]
            ],
            "downtime": (1.0, 3.0)
        },
        "compressor fault": {
            "symptoms": [
                "Refrigeration compressor tripped internal thermal overload switch. Hermetic shell burning hot (`{temp}`\u00b0C) with zero cooling output (`{percent}` flow).",
                "Loud {adj} humming and `{current}` Amps locked rotor current (`LRA`) when compressor attempts to start. Main breaker trips after 3 seconds.",
                "Hermetic compressor making severe {adj} internal clattering {noise}. Suction and discharge pressures equalized (`{press} PSI`) while running.",
                "Dryer refrigeration compressor failing to start (`{current}` Amps draw). High dew point alarm (`> {temp}\u00b0C`) active on panel.",
                "Compressor contactor chatting rapidly (`{hz}`). Hermetic dome temperature normal but unit drawing `{amps} Amps` (`target {current} Amps`).",
                "Megger test of compressor windings shows dead short to ground (`{mg_ohm}` insulation resistance). Distinct {adj} electrical burn smell from terminal box."
            ],
            "root_causes": [
                "Mechanical seizure (`{torque}` lockup) of hermetic scroll/reciprocating compressor internal bearings due to prolonged loss of oil return (`{percent}` oil loss) from system.",
                "Electrical burnout of compressor start/run capacitor (`capacitance measured 0 uF vs {hz} uF rating`) preventing motor start phase shift.",
                "Internal discharge valve reed fracture inside hermetic shell (`{debris_amt}`) causing complete loss of pumping capacity (`{press_drop} PSI` differential).",
                "Single-phasing or severe voltage dip (`{percent}` drop on `{volts}` feed) damaged hermetic compressor start winding over `{hours}` hours.",
                "Pitted and welded contacts (`{clearance} gap` melted) inside main compressor contactor prevented clean power delivery to compressor terminals.",
                "Liquid slugging (`{percent}` liquid refrigerant return) destroyed scroll compressor involute plates during abrupt hot gas bypass failure."
            ],
            "actions": [
                "Replaced start and run capacitors (`{part_num}`) along with potential relay; tested hermetic compressor windings (`{mg_ohm} OK`) and successfully restarted unit.",
                "Recovered refrigerant, cut out mechanically seized hermetic compressor (`{part_num}`), brazed in exact replacement compressor and filter drier, evacuated, and weighed in fresh R-134a charge (`{lbs_charge}`).",
                "Replaced failed compressor start kit (`{part_num}` capacitor + relay), checked contactor tips, and verified smooth compressor running draw (`{amps} Amps`).",
                "Replaced internal hermetic refrigeration compressor assembly (`{part_num}`), installed new suction/liquid line filter driers (`{part_num}`), pulled deep vacuum, and recharged system (`{lbs_charge}`).",
                "Swapped out burned compressor contactor (`{part_num}`), replaced wiring lugs (`{torque}` torque), and verified phase-to-phase voltage (`{volts}`).",
                "Cut out failed compressor shell, flushed system of acidic burnout oil (`{part_num}` solvent), installed suction filter drier, brazed new scroll (`{part_num}`), and charged (`{lbs_charge}`)."
            ],
            "parts": [
                ["Compressor Run Capacitor 45uF", "Start Relay Kit", "Contactor"],
                ["Replacement Hermetic Refrigeration Compressor Assembly", "Bi-Flow Filter Drier", "R-134a Charge (6 lbs)"],
                ["Hard Start Capacitor Kit", "Compressor Contactor 24V"],
                ["Hermetic Scroll Compressor Unit", "Liquid Line Drier", "R-407C Refrigerant (8 lbs)"],
                ["3-Pole Compressor Contactor 30A", "Terminal Lug Kit"],
                ["Scroll Compressor Core", "Burnout Cleanup Filter", "RX-11 Flush Solvent (1 Can)", "R-407C (6 lbs)"]
            ],
            "downtime": (4.0, 8.5)
        }
    },
    "Centrifugal Chiller": {
        "refrigerant leak": {
            "symptoms": [
                "Chiller low refrigerant charge warning alarm triggered. Condenser approach temperature `{degree}` elevated (`> {temp}\u00b0C`).",
                "Purge unit running excessively (`> {hours} minutes per hour` exhausting non-condensables). Tech noted {adj} oil film near rupture disc flange (`{clearance} gap`).",
                "Chiller tripped on low evaporator pressure cutout (`{press} PSI`) during pull-down. Sight glass on liquid line shows continuous stream of bubbles (`{percent}` flash gas).",
                "Evaporator level sensor indicating low charge (`-{percent}` drop in sight glass). Purge pump-out frequency increased `300%` over baseline (`{hz}` cycles).",
                "Compressor discharge superheat abnormally high (`+{temp}`\u00b0C). Leak detector picked up `{ppm}` R-134a concentration near evaporator water box.",
                "Chiller unable to reach `100%` capacity (`stalled at {percent}` load). Oil recovery system fault indicating high `{ppm}` refrigerant in oil sump."
            ],
            "root_causes": [
                "Degraded elastomeric O-ring seal (`{part_num}`) on condenser relief/rupture disc flange assembly allowing gradual low-pressure refrigerant seepage (`{lbs_charge}` loss).",
                "Corrosion pinhole (`{thickness} inch` diameter) in evaporator copper tube sheet bundle caused by winter freeze-thaw or aggressive chilled water treatment (`pH {ph_val}`).",
                "Thermal expansion cycles (`{temp_rc}`\u00b0C swings) loosened flange bolts (`{torque}` under-torqued) on compressor suction elbow connection O-ring groove.",
                "Leaking shaft seal on open-drive centrifugal compressor assembly caused by drying out of seal face carbon (`{gap} inch` wear) during `{time_period}` winter shutdown.",
                "Stress fracture (`{runout} inch` crack length) on oil return line brazed joint due to excessive compressor vibration (`{vibe_rc}` in/sec RMS).",
                "Porous casting defect in cast iron compressor volute (`{thickness} inch` void) opened up after `{hours}` hours of high-pressure (`{press} PSI`) surging."
            ],
            "actions": [
                "Performed thorough leak search using heated diode detector, located leak at rupture disc flange (`{part_num}`), recovered charge, replaced rupture disc and O-ring gasket, evacuated to 300 microns, and re-trimmed R-134a charge (`{lbs_charge}`).",
                "Eddy current tested evaporator tube bundle, identified 2 leaking copper tubes, plugged tubes using brass tapered drive plugs (`{part_num}`), evacuated chiller shell, and restored virgin R-134a charge (`{lbs_charge}`).",
                "Replaced degraded compressor suction elbow O-ring seal (`{part_num}`) and rupture disc assembly, pulled 24-hour deep vacuum test, and charged unit with 120 lbs of R-134a (`{lbs_charge}`).",
                "Replaced open-drive compressor mechanical shaft seal assembly (`{part_num}`), renewed oil separation filters (`{part_num}`), evacuated system, and verified zero leak rate (`< {ppm} ppm`).",
                "Recovered `{lbs_charge}` refrigerant, silver-brazed cracked oil return line (`{part_num}`), replaced filter drier (`{part_num}`), and leak checked with `{press} PSI` nitrogen.",
                "Installed specialized mechanical seal clamp (`{part_num}`) over casting defect, pressure tested shell (`{press} PSI`), evacuated, and recharged (`{lbs_charge}`)."
            ],
            "parts": [
                ["Carbon Steel Rupture Disc Assembly", "Neoprene Flange O-Ring", "R-134a Refrigerant (120 lbs)"],
                ["Brass Tapered Tube Plugs (4-Pack)", "Epoxy Sealer", "R-134a Top-off Charge (85 lbs)"],
                ["Suction Elbow O-Ring Kit", "Rupture Disc Gasket", "R-134a Refrigerant (100 lbs)"],
                ["Centrifugal Compressor Shaft Seal Assembly", "Oil Filter Element", "R-134a (65 lbs)"],
                ["Vibration Absorber Loop", "Filter Drier Core Kit", "15% Silver Solder", "Nitrogen Cylinder"],
                ["Mechanical Flange Repair Clamp", "Epoxy Sealant Paste", "R-134a Bottle (50 lbs)"]
            ],
            "downtime": (8.0, 12.0)
        },
        "compressor bearing wear": {
            "symptoms": [
                "High oil temperature alarm (`{temp}`\u00b0C) and `{degree}` drop (`-{press_drop} PSI`) in differential oil pressure across centrifugal compressor thrust bearing.",
                "High frequency vibration (`{vibe}` in/sec RMS) detected on compressor gear case housing. Oil analysis confirms elevated copper (`> {ppm} ppm`).",
                "Loud {adj} high-pitched whining and {noise} inside compressor housing during guide vane modulation (`{percent}` open).",
                "Compressor bearing oil delta-P low warning (`{press} PSI`). Tech noted {adj} metal shimmer (`{ppm}` particulate) in oil sump sight glass during run.",
                "Thrust bearing proximity probe indicated severe axial displacement (`+{gap} inch`). Oil filter delta-P spiked to `{press_drop} PSI`.",
                "Journal bearing RTD temperature spiked (`{temp}`\u00b0C, `alarm > 90\u00b0C`). Distinct {adj} grinding {noise} observed during compressor coast-down."
            ],
            "root_causes": [
                "Loss of hydrodynamic oil film stability due to refrigerant dilution (`{percent}` R-134a in oil) in oil sump during low-load surge operation (`< {percent}` load).",
                "Normal fatigue wear (`{gap} inch` babbit loss) of journal and thrust hydrodynamic babbitt bearings after `{hours}` hours of high-speed centrifugal duty.",
                "Partial restriction (`{clog_pct}` blocked) in bearing oil supply pressure regulator valve starved thrust bearing during rapid load changes (`{torque}` torque spikes).",
                "Repeated compressor surging (`{hz}` cycles) over past cooling season subjected thrust bearing to severe axial shock loads (`{lbs_charge}` thrust force).",
                "Particulate contamination (`{ppm}` dirt) from degraded internal oil filter scored babbitt bearing surfaces, increasing clearance to `{clearance} gap`.",
                "Oil heater element failure (`{volts}` circuit open) allowed cold, high-viscosity oil (`{temp_rc}`\u00b0C) to cavitate oil pump during cold starts."
            ],
            "actions": [
                "Locked out chiller, recovered charge, opened compressor housing, replaced high-speed journal and thrust babbitt bearings (`{part_num}`), cleaned oil sump, and renewed oil filters and synthetic charge (`{lbs_charge}`).",
                "Disassembled compressor drive end, installed new precision babbitt bearing set (`{part_num}`), calibrated oil pressure regulating valve (`{press} PSI`), and performed full oil flush.",
                "Replaced worn high-speed thrust bearing pad assembly (`{part_num}`), renewed internal oil filter element (`{part_num}`), and filled compressor with fresh POE oil (`{lbs_charge}`).",
                "Performed complete compressor top-end overhaul, replacing high-speed shaft bearings (`{part_num}`) and thrust collar; inspected impeller clearances (`{clearance} gap`) and renewed gaskets.",
                "Installed upgraded tilting-pad thrust bearing assembly (`{part_num}`), cleaned oil galleries (`{ppm}` debris removed), replaced high-efficiency oil filter (`{part_num}`), and flushed sump.",
                "Replaced scored journal bearings (`{part_num}`), installed new oil sump heater element (`{part_num}`), verified oil pressure (`{press} PSI`), and test run compressor."
            ],
            "parts": [
                ["High-Speed Babbitt Journal Bearing Set", "Thrust Bearing Assembly", "POE Compressor Oil (10 Gal)", "Oil Filter Element"],
                ["Precision Thrust Bearing Pad Kit", "Internal Oil Filter Cartridge", "Compressor Gasket Set", "Synthetic POE Lube"],
                ["Centrifugal Bearing Rebuild Kit (Journal & Thrust)", "Oil Sump Gasket Set", "POE Oil Charge (8 Gal)"],
                ["Thrust Collar Assembly", "High-Speed Bearings", "O-Ring Overhaul Kit", "POE Refrigeration Oil"],
                ["Tilting-Pad Thrust Bearing Kit", "High-Efficiency Oil Filter", "Sump Flushing Solvent", "POE Oil"],
                ["Journal Bearing Set (Front/Rear)", "Sump Heater Element 1000W", "Compressor O-Ring Kit"]
            ],
            "downtime": (10.0, 12.0)
        },
        "tube fouling": {
            "symptoms": [
                "Condenser approach temperature elevated to `{temp}`\u00b0C (`normal < 1.5\u00b0C`). Chiller head pressure running `{press}` PSI above design.",
                "Chiller efficiency degraded (`kW/ton up by {percent}`). Condenser water inlet/outlet delta-T reduced to `{temp}`\u00b0C (`normal 5.5\u00b0C`).",
                "High condenser pressure warning alarm active on panel (`{press} PSI`). Compressor running at `100%` guide vane opening to satisfy chilled water loop.",
                "Ops noted chiller struggling to maintain `7\u00b0C` chilled water setpoint (`+{temp}`\u00b0C deficit) during afternoon peak load due to high head pressure (`{press} PSI`).",
                "Condenser water flow rate dropped (`-{percent}` GPM). Water box delta-P increased to `{press_drop} PSI` (`normal < 8 PSI`).",
                "Evaporator approach temperature expanded (`{temp}`\u00b0C). Chiller surging repeatedly (`{hz}`) due to high lift requirements from fouled tubes."
            ],
            "root_causes": [
                "Heavy calcium carbonate mineral scale (`{thickness} inch` thickness) and biological slime deposition inside copper condenser tubes due to cooling tower water chemical treatment lapse (`pH {ph_val}`).",
                "Accumulation of mud, silt, and cooling tower scale debris (`{debris_amt}`) blocking water flow across passes inside condenser water boxes (`{clog_pct}` blocked).",
                "Bio-fouling and algae growth inside condenser tubes forming insulating biofilm layer (`{thickness} inch`) after chemical biocide dosing pump failure (`{time_period}` lapse).",
                "Corrosion oxide layer and scale buildup on internally enhanced copper tube rifling reducing overall heat transfer coefficient by `{percent}`.",
                "Sacrificial zinc anodes in condenser water box depleted entirely after `{hours}` hours, allowing galvanic corrosion tubercules (`{thickness} inch`) to form in tubes.",
                "Ingestion of plastic debris and leaves (`{debris_amt}`) past cooling tower strainers partially plugged `{percent}` of condenser tube inlets."
            ],
            "actions": [
                "Isolated condenser water loop, removed end covers, performed mechanical rotary brush tube cleaning (`{part_num}`) across all 450 condenser tubes, and flushed out scale debris (`{debris_amt}`).",
                "Circulated inhibited acid descaling solution (`{part_num}`) through condenser bundle for `{hours}` hours, neutralized loop (`pH {ph_val}`), and mechanically brushed tubes to bare copper.",
                "Removed condenser water heads, cleared heavy silt/debris (`{debris_amt}`) from pass ribs, brushed tube bundle with nylon/copper brushes (`{part_num}`), and renewed end cover gaskets.",
                "Performed full mechanical tube brushing of condenser and evaporator tube sheets (`{part_num}`), flushed bundles with clean water (`{press} PSI`), and calibrated automatic water treatment controller.",
                "Replaced depleted zinc anodes (`{part_num}`), acid-washed condenser tubes (`{part_num}`), hydro-blasted water boxes (`{press} PSI`), and applied epoxy coating to tube sheet.",
                "Removed water box covers, manually rodded out `{clog_pct}` tube blockage (`{debris_amt}` removed), installed upgraded strainer baskets (`{part_num}`), and reassembled with new gaskets."
            ],
            "parts": [
                ["Condenser Water Box Gaskets (Set of 2)", "Rotary Tube Brushes 3/4-inch (6-Pack)"],
                ["Inhibited Acid Descaling Chemical (20 Gallons)", "Neutralizer Powder", "Head Gasket Set"],
                ["Water Box End Cover Gaskets", "Nylon Replacement Tube Brushes (10-Pack)"],
                ["Neoprene Head Gaskets (Set of 4)", "Heavy-Duty Tube Cleaning Brushes"],
                ["Zinc Sacrificial Anodes (Set of 6)", "Tube Sheet Epoxy Coating", "Acid Cleaner"],
                ["Water Box Gasket Set", "Inlet Strainer Baskets (2x)", "Tube Cleaning Rods"]
            ],
            "downtime": (6.0, 9.5)
        }
    },
    "Cooling Tower": {
        "fan motor failure": {
            "symptoms": [
                "Cooling tower fan motor tripped VFD/overload breaker (`{amps} Amps` overcurrent). Motor frame burning hot (`{temp}`\u00b0C) with `{degree}` smoke from terminal box.",
                "Loud {adj} grinding {noise} sound from cooling tower fan gearbox/motor coupling. Fan blades spinning erratically (`{hz}` speed fluctuations).",
                "VFD indicating ground fault trip on cooling tower fan feed. Megger test shows dead short (`{mg_ohm}` insulation resistance) on motor leads.",
                "Cooling tower basin water temperature rising above `32\u00b0C` alarm setpoint (`+{temp}`\u00b0C spike). Fan motor stationary (`0 Amps` draw, `{volts}` at terminals).",
                "Severe vibration (`{vibe}` in/sec) detected on fan deck. Motor cooling fins packed solidly with `{thickness} inch` of cooling tower mineral scale.",
                "Gearbox low oil level alarm triggered (`{percent}` remaining). Input shaft seal leaking oil (`{degree}`) onto fan motor housing."
            ],
            "root_causes": [
                "Moisture and corrosive cooling tower mist penetrated motor terminal enclosure, causing insulation breakdown (`{mg_ohm}` resistance) across stator leads.",
                "Severe bearing seizure (`{torque}` lockup) due to water wash-out of grease (`{clog_pct}` loss) in vertical fan motor lower bearing during heavy monsoon/spray conditions.",
                "Phase loss (`{volts}` dropped on Phase B) on incoming feed caused single-phasing thermal burnout (`{temp_rc}`\u00b0C) of cooling tower induction motor windings.",
                "Prolonged operation in saturated 100% humidity environment degraded Class F insulation varnish beyond dielectric limit after `{hours}` hours.",
                "Cooling fan blade imbalance (`{runout} inch` pitch deviation) destroyed motor output shaft bearings (`{clearance} gap`) over `{time_period}`.",
                "Gearbox input shaft lip seal failure (`{thickness} inch` gap) allowed moisture ingress, turning lubricating gear oil into an emulsion (`{percent}` water)."
            ],
            "actions": [
                "Removed failed cooling tower fan motor using crane, installed severe-duty TEFC replacement motor (`{part_num}`), renewed shaft alignment (`{runout} inch`), and sealed terminal box with RTV.",
                "Swapped out burned cooling tower fan motor with spare severe-duty VFD-rated motor (`{part_num}`), replaced flexible shaft coupling (`{part_num}`), and verified fan pitch balance (`{clearance} gap`).",
                "Installed new vertical fan drive motor (`{part_num}`), renewed motor shaft seal and rain canopy, greased bearings with waterproof grease (`{part_num}`), and tested VFD speed steps (`{hz}`).",
                "Replaced fan motor and gearbox shaft coupling element (`{part_num}`), sealed conduit connections against moisture ingress, and performed laser alignment (`{clearance} tolerance`).",
                "Replaced fan motor (`{part_num}`), adjusted fan blade pitch angle (`{torque}` bolt torque), rebalanced hub assembly, and verified vibration (`< {vibe} in/sec`).",
                "Drained emulsified gearbox oil, replaced input shaft seal (`{part_num}`), installed new severe-duty motor (`{part_num}`), and refilled with `{lbs_charge} gal` synthetic gear lube."
            ],
            "parts": [
                ["Severe-Duty TEFC Cooling Tower Motor 25HP", "Composite Coupling Element", "RTV Silicone Sealant"],
                ["Replacement Cooling Tower Induction Motor", "Flexible Drive Shaft Coupling", "Motor Rain Canopy"],
                ["Inverter-Duty Fan Motor Assembly", "Lower Bearing Waterproof Lip Seal", "Mounting Hardware Kit"],
                ["Severe-Duty Fan Motor 30HP", "Shaft Coupling Kit", "Waterproof Conduit Gland Set"],
                ["TEAO Cooling Tower Motor 40HP", "Fan Hub Balancing Kit", "Pitch Protractor Tool"],
                ["Gearbox Input Seal", "Synthetic Gear Oil ISO 220 (5 Gal)", "Severe-Duty Motor 20HP"]
            ],
            "downtime": (5.0, 9.0)
        },
        "scale buildup": {
            "symptoms": [
                "Heavy white/brown mineral scale (`{thickness} inch` crust thickness) visible on PVC fill media and drift eliminators during weekly inspection.",
                "Cooling tower water distribution nozzles partially clogged (`{clog_pct}` blocked) with lime crust, causing uneven water channeling across fill pack.",
                "Elevated approach temperature (`+{temp}`\u00b0C) between tower basin water and wet-bulb temp (`> 5.5\u00b0C`). Fill media sagging under weight (`{lbs_charge} lbs`) of scale deposits.",
                "Ops noted {adj} scale shedding from drift eliminators into cold water basin (`{degree}` debris accumulation near suction screen).",
                "Cooling tower blowdown line restricted (`{percent}` flow capacity) by hard calcium carbonate scaling. Basin conductivity reading `{hz} uS/cm` (very high).",
                "Basin heater elements heavily coated in `{thickness} inch` scale, causing them to trip on internal high limit (`{temp}`\u00b0C)."
            ],
            "root_causes": [
                "High cycles of concentration (`> 6.0`) operated without adequate bleed-off rate (`{gpm} GPM` deficit) due to stuck automatic conductivity blowdown valve (`{part_num}`).",
                "Failure of chemical scale inhibitor/dispersant dosing pump (`{volts}` power loss) allowed calcium carbonate hardness to exceed saturation index (`LSI > +1.5`).",
                "Seasonal evaporation concentration combined with hard makeup water (`> {ppm} ppm calcium`) in absence of softening pretreatment over `{time_period}`.",
                "Improper pH control (`pH > {ph_val}`) caused rapid precipitation of calcium and magnesium scale across warm PVC fill surfaces (`{temp_rc}`\u00b0C).",
                "Conductivity controller probe fouling (`{thickness} inch` coating) caused false low readings (`{hz} uS/cm`), preventing automatic blowdown initiation.",
                "Solenoid valve on makeup water line stuck open (`{clearance} gap` debris), causing constant overflow and dilution of expensive chemical scale inhibitors."
            ],
            "actions": [
                "Pressure washed PVC fill pack and drift eliminators with low-pressure wide-fan nozzle (`{press} PSI`), repaired conductivity blowdown valve (`{part_num}`), and calibrated chemical dosing (`{gpm} ml/min`).",
                "Circulated bio-dispersant and mild descaling agent (`{part_num}`) through tower loop for `{hours}` hours, flushed cold water basin, and serviced bleed-off solenoid (`{part_num}`).",
                "Manually cleaned clogged distribution nozzles (`{part_num}`), pressure washed top deck and fill media (`{press} PSI`), replaced broken fill sections, and reset blowdown conductivity controller to `{hz} uS/cm`.",
                "Descaled distribution header and nozzles, vacuumed scale debris (`{debris_amt}`) from cold water basin, and repaired chemical scale inhibitor dosing pump tubing (`{part_num}`).",
                "Removed and acid-cleaned conductivity controller probe (`{part_num}`), verified calibration (`{hz} uS/cm`), manually triggered blowdown (`{gpm} GPM`), and flushed basin.",
                "Replaced makeup water solenoid valve (`{part_num}`), drained basin, pressure washed `{thickness} inch` scale from heater elements, and shock-dosed scale inhibitor (`{lbs_charge} gal`)."
            ],
            "parts": [
                ["Cooling Tower Spray Nozzles (12-Pack)", "Conductivity Blowdown Solenoid Valve Rebuild Kit"],
                ["Cooling Tower Descaling Chemical (15 Gal)", "Bio-Dispersant (5 Gal)", "Replacement PVC Fill Block Sections (4 Bundles)"],
                ["Distribution Nozzle Replacement Set (20-Pack)", "Conductivity Controller Probe", "Chemical Pump Peristaltic Tubing"],
                ["Replacement Fill Media Bundles (2 Packs)", "Drift Eliminator Sections", "Basin Strainer Screen"],
                ["Conductivity Probe Cleaning Solution", "Blowdown Valve Rebuild Kit", "Calibration Fluid"],
                ["Makeup Water Solenoid 1-1/2\"", "Basin Heater Element 5kW", "Liquid Scale Inhibitor (5 Gal)"]
            ],
            "downtime": (3.5, 6.5)
        },
        "water distribution blockage": {
            "symptoms": [
                "Dry patches (`{percent}` un-wetted area) visible across top of PVC fill media. Hot water basin overflowing (`{gpm} GPM`) around distribution basin edges.",
                "Multiple distribution target nozzles completely plugged (`{clog_pct}` blocked) with debris, causing heavy localized channeling and splashing inside tower.",
                "Cooling efficiency degraded (`+{temp}`\u00b0C higher leaving water temp). Inspection showed `{vibe}` in/sec vibration from water hammering in header.",
                "Ops reported water splashing outside tower louvers (`{degree}` drift loss). Top deck distribution basin nozzles 40% blocked with algae/silt (`{thickness} inch`).",
                "Tower basin water level dropping rapidly (`-{percent}` volume). Makeup valve wide open (`{gpm} GPM`) but cannot keep up due to massive splash-out.",
                "Pump cavitation {noise} sound from condenser water pump (`{hz}` frequency) due to air entrainment from severe channeling through tower fill."
            ],
            "root_causes": [
                "Accumulation of wind-blown leaves, plastic wrappers, and organic debris (`{debris_amt}`) in hot water distribution basin plugging nozzle orifices (`{clearance} gap`).",
                "Severe algae and biological slime mats (`{thickness} inch` thick) broke loose from distribution header piping and lodged inside target spray nozzles.",
                "Rust flakes and pipe corrosion scales (`{ppm}` particulate) from upstream carbon steel condenser water piping carried into tower distribution header.",
                "Broken distribution basin covers (`{gap} inch` gap) allowed direct sunlight ingress, accelerating rapid algae growth (`pH {ph_val}`) that blinded distribution target nozzles.",
                "Failure of bypass valve linkage (`{torque}` broken) dumped full condenser flow (`{gpm} GPM`) over one cell, overwhelming the distribution basin capacity.",
                "Structural collapse of fiberglass distribution header pipe (`{length} ft` section) due to winter freeze damage, dumping water straight into basin."
            ],
            "actions": [
                "Removed hot water basin covers, manually cleared leaves/debris (`{debris_amt}`) from all distribution nozzles, pressure washed basin (`{press} PSI`), and chlorinated loop.",
                "Disassembled and cleaned 36 target spray nozzles (`{part_num}`), flushed main distribution header piping, installed new coarse inlet strainer baskets (`{part_num}`), and shock-chlorinated tower.",
                "Replaced 14 broken or missing distribution nozzles (`{part_num}`), removed heavy algae mats (`{debris_amt}`) from hot water basin deck, and installed opaque UV-blocking basin covers (`{part_num}`).",
                "Manually rodded out plugged distribution basin orifices, flushed piping network with high-pressure hose (`{press} PSI`), and installed upgraded non-clog polypropylene target nozzles (`{part_num}`).",
                "Repaired bypass valve mechanical linkage (`{part_num}`), manually cleared `{clog_pct}` blockage from distribution pan, rebalanced cell flow valves, and checked nozzle patterns.",
                "Replaced shattered fiberglass header section (`{part_num}`), installed new target nozzles (`{part_num}`), flushed system of fiberglass shards (`{debris_amt}`), and verified distribution pattern."
            ],
            "parts": [
                ["Polypropylene Target Spray Nozzles (15-Pack)", "Basin Cover Fasteners"],
                ["Replacement Distribution Nozzles (24-Pack)", "Coarse Mesh Inlet Strainer Basket", "Shock Biocide (5 Gal)"],
                ["UV-Blocking Basin Cover Panels (Set of 4)", "Target Nozzle Kit (10-Pack)"],
                ["Non-Clog Distribution Nozzle Assembly (18-Pack)", "Basin Sealing Gasket Strip"],
                ["Bypass Valve Actuator Arm", "Distribution Pan Sweeper Nozzle", "Flow Balancing Valve Kit"],
                ["FRP Header Pipe Section (10ft)", "Flange Gasket Kit", "Target Spray Nozzle Set (12x)"]
            ],
            "downtime": (2.0, 4.5)
        }
    },
    "Scroll Chiller": {
        "scroll compressor wear": {
            "symptoms": [
                "Scroll compressor making loud {adj} metallic rattling and {noise} sound (`{vibe}` in/sec RMS on frame). Compressor drawing `{percent}` low amps (`45%` FLA).",
                "Chiller circuit B unable to build differential pressure (`discharge/suction pressures nearly equal` at `{press} PSI`). Scroll compressor running hot (`{temp}`\u00b0C).",
                "Internal discharge temperature trip on scroll compressor (`> {temp}\u00b0C`). Unit making distinct {adj} grinding sound during shutdown spindown.",
                "Scroll compressor amp draw fluctuating erratically (`{current}` Amps). Chiller failing to pull down process loop temperature (`+{temp}`\u00b0C deficit).",
                "Compressor trips on high discharge pressure (`{press} PSI`) but gauge shows low lift. Thermal imaging shows internal bypass heating (`{temp}`\u00b0C shell).",
                "Oil sight glass empty (`{percent}` level). Acoustic analysis indicates severe scroll flank wear (`{hz}` harmonic noise profile)."
            ],
            "root_causes": [
                "Scroll tip seal wear (`{gap} inch` gap) and flank wear caused by liquid refrigerant slugging (`{percent}` floodback) during low-ambient startup without crankcase heater energized.",
                "Fatigue fracture (`{length} inch` crack) of internal Oldham coupling ring inside scroll set due to thousands of thermal/pressure cycles (`{hz}` short cycles).",
                "Prolonged operation with marginal oil return (`< {clog_pct}%` level) caused metal-to-metal scoring (`{thickness} inch` deep) between orbiting and fixed scroll wraps.",
                "Reverse rotation event (`{time_period}` duration) caused by incorrect phase sequence during temporary generator power feed damaged scroll involute tips.",
                "Liquid wash-out of bearing lubrication (`{ppm}` oil dilution) during extended periods of low superheat (`< 1\u00b0C`) destroyed upper orbital bearing.",
                "Overheating (`{temp_rc}`\u00b0C) due to blocked condenser airflow caused breakdown of synthetic POE oil, leading to varnish buildup (`{thickness} inch`) on scroll flanks."
            ],
            "actions": [
                "Recovered refrigerant circuit B, cut out worn scroll compressor, brazed in exact replacement scroll compressor assembly (`{part_num}`), replaced liquid line drier, evacuated to 400 microns, and weighed in R-410A charge (`{lbs_charge}`).",
                "Replaced failed hermetic scroll compressor unit (`{part_num}`), renewed crankcase heater and contactor (`{part_num}`), flushed piping (`{part_num}`), installed new bi-flow filter drier, and recharged system (`{lbs_charge}`).",
                "Swapped out damaged scroll compressor with factory replacement (`{part_num}`), installed new phase monitor relay (`{part_num}`) to prevent reverse rotation, pulled deep vacuum, and recharged R-410A (`{lbs_charge}`).",
                "Replaced scroll compressor assembly, renewed suction accumulator (`{part_num}`) and filter drier, verified crankcase heater continuity (`{mg_ohm} ohms`), and charged circuit precisely by weight (`{lbs_charge}`).",
                "Cut out destroyed tandem scroll pair (`{part_num}`), installed new manifolds and compressors, flushed acid oil with RX-11 (`{part_num}`), and verified superheat (`{temp}\u00b0C`).",
                "Replaced locked-up scroll (`{part_num}`), installed oversized suction filter drier (`{part_num}`) to catch debris (`{debris_amt}`), and ran system for 48 hours before oil change."
            ],
            "parts": [
                ["Replacement Tandem Scroll Compressor Assembly (15HP)", "Bi-Flow Filter Drier Core", "R-410A Refrigerant (25 lbs)"],
                ["Hermetic Scroll Compressor 20HP", "Crankcase Heater Band 240V", "Liquid Line Filter Drier", "R-410A Charge (30 lbs)"],
                ["Scroll Compressor Unit", "Phase Monitor Protection Relay", "Filter Drier", "R-410A Refrigerant Bottle"],
                ["Scroll Compressor Replacement Assembly", "Suction Accumulator Vessel", "Filter Drier Element", "R-410A (28 lbs)"],
                ["Tandem Scroll Compressor Set", "RX-11 Flush Solvent (2 Cans)", "Suction Filter Core", "R-410A (45 lbs)"],
                ["Single Scroll Compressor 10HP", "Oversized Suction Drier", "Liquid Drier", "POE Oil (2 Gal)"]
            ],
            "downtime": (6.0, 9.5)
        },
        "refrigerant undercharge": {
            "symptoms": [
                "Chiller circuit A short cycling (`{hz}` cycles/hr) on low-pressure switch (`cutout at {press} PSI`). Clear sight glass showing continuous rapid bubbles.",
                "High superheat reading (`> {temp}\u00b0C` at compressor suction) and low subcooling (`< 2\u00b0C`). Chiller running `100%` capacity but leaving water `{temp}`\u00b0C high.",
                "Electronic expansion valve (`EEV`) at `100%` open position but evaporator temperature remaining {degree} elevated (`+{temp}\u00b0C`) above setpoint.",
                "Low refrigerant charge alarm active on scroll chiller controller. Tech noted {adj} oil residue on condenser header braze joint (`{clearance} gap`).",
                "Compressor discharge temperature unusually high (`{temp}`\u00b0C). Circuit B shutting down on internal thermal overload (`{hz}` times per day).",
                "Evaporator freezing up (`{thickness} inch` frost on shell). Saturated suction temperature dropped below freezing (`-{temp}\u00b0C`)."
            ],
            "root_causes": [
                "Micro-leak (`{gap} inch` pinhole) at copper U-bend braze joint on air-cooled condenser coil due to continuous fan vibration (`{vibe_rc}` in/sec) and thermal cycling.",
                "Loose flare nut connection (`{torque}` under-torqued) on sight glass or filter drier fitting allowing slow loss (`-{percent}` volume) of R-410A/R-407C over past cooling season.",
                "Schrader service access valve core (`{part_num}`) failed to seal completely (`{clearance} gap`) after previous preventive maintenance pressure check.",
                "Pinhole corrosion leak (`{thickness} inch` diameter) on evaporator brazed plate heat exchanger refrigerant channel caused by aggressive local humidity (`pH {ph_val}`).",
                "Rub-through on capillary tube (`{length} inch` wear) against compressor discharge line due to missing vibration dampener.",
                "Thermal stress crack (`{runout} inch` long) on electronic expansion valve body braze joint (`{clog_pct}` leak rate)."
            ],
            "actions": [
                "Performed electronic leak check, located micro-leak at condenser coil U-bend, recovered remaining charge, silver brazed repair (`{part_num}`), evacuated to 350 microns, and weighed in factory charge of R-410A (`{lbs_charge}`).",
                "Tightened sight glass and filter drier flare nuts (`{torque}` torque), replaced Schrader valve cores (`{part_num}`), pulled 12-hour deep vacuum, and recharged circuit A with precise weight of R-410A (`{lbs_charge}`).",
                "Repaired leaking braze joint on liquid line header, installed new hermetic filter drier (`{part_num}`), pulled vacuum, and charged unit with 22 lbs of R-410A (`{lbs_charge}`).",
                "Located pinhole leak at condenser inlet header using nitrogen/hydrogen tracer gas (`{press} PSI`), brazed joint, renewed filter drier, and recharged system (`{lbs_charge}`).",
                "Brazed rubbed capillary tube (`{part_num}`), installed rubber vibration isolation dampeners (`{part_num}`), evacuated circuit, and weighed in `{lbs_charge}` R-410A.",
                "Replaced cracked EEV assembly (`{part_num}`), wrapped valve body with wet rag during brazing, pulled deep vacuum to 250 microns, and charged `{lbs_charge}` of R-407C."
            ],
            "parts": [
                ["R-410A Refrigerant Charge (22 lbs)", "Liquid Line Filter Drier", "Silver Braze Alloy"],
                ["Schrader Valve Cores & Brass Seal Caps (4-Pack)", "R-410A Refrigerant (18 lbs)", "Flare Gasket Set"],
                ["Hermetic Filter Drier Assembly", "Braze Rods", "R-410A Refrigerant Cylinder"],
                ["Bi-Flow Filter Drier", "R-410A Top-off Charge (25 lbs)", "Service Port Caps"],
                ["Capillary Tube Section", "Rubber Vibration Dampener", "R-410A (15 lbs)", "Filter Drier"],
                ["Electronic Expansion Valve (EEV)", "Valve Braze Kit", "R-407C Cylinder (30 lbs)"]
            ],
            "downtime": (3.5, 6.0)
        },
        "sensor fault": {
            "symptoms": [
                "Chiller controller displaying erratic leaving chilled water temperature (`reading jumps rapidly between {temp}\u00b0C and -15\u00b0C`). Unit locked out on freeze protection.",
                "Evaporator pressure transducer reading `{press}` PSI offset compared to calibrated mechanical manifold gauge. EEV hunting wildly (`{percent}` open).",
                "Scroll chiller locked out on false high discharge temperature alarm (`sensor reading 155\u00b0C` while actual pipe temp is `{temp}\u00b0C`).",
                "Ops reported chiller not loading past `50%` capacity due to faulty return water temperature thermistor reading `{degree}` out of calibration.",
                "Low suction pressure lockout (`{press} PSI`) triggered, but mechanical gauges read normal (`{current} PSI`). Transducer output stuck at `0.5 VDC`.",
                "Condenser fan cycling erratically (`{hz}` cycles/min). Liquid line temperature sensor reading `-40\u00b0C` (open circuit)."
            ],
            "root_causes": [
                "Moisture ingress (`{percent}` RH) into immersion thermistor sensor probe pocket/well caused internal short (`{mg_ohm}` resistance) across NTC thermistor element.",
                "Calibration drift (`-{press_drop} PSI`) and internal bridge resistor failure (`{volts}` VDC output error) inside high-pressure/low-pressure 4-20mA pressure transducer.",
                "Vibration chafing (`{thickness} inch` insulation worn) of sensor shielded wiring harness against chiller steel frame caused intermittent ground fault on sensor loop.",
                "Corrosion on multi-pin plug connection (`{gap} inch` pitting) at chiller microprocessor board resulting from high ambient cabinet humidity (`{ppm}` airborne salts).",
                "Lightning strike induced surge (`{volts}` peak) destroyed 5V reference circuit on pressure transducer PCB.",
                "Thermal cycling (`{temp_rc}`\u00b0C swings) fractured the delicate lead wire soldering inside the epoxy-potted temperature probe head (`{part_num}`)."
            ],
            "actions": [
                "Replaced leaving chilled water NTC thermistor probe (`{part_num}`), applied thermal paste (`{part_num}`) inside sensor well, and calibrated sensor offset in controller menu.",
                "Replaced faulty suction and discharge pressure transducers (`{part_num}`), renewed wiring harness connectors (`{part_num}`), and verified calibration against digital manifold (`{press} PSI`).",
                "Replaced defective discharge temperature thermistor (`{part_num}`), repaired chafed sensor wiring harness with heat shrink, and cleared controller lockout (`{hz}`).",
                "Installed new return water temperature sensor assembly (`{part_num}`), cleaned microprocessor board edge connectors with contact cleaner (`{part_num}`), and tested staging.",
                "Installed new 0-500 PSI pressure transducer (`{part_num}`), verified 5VDC reference voltage (`{volts}`), and confirmed EEV step modulation stabilized.",
                "Spliced in new liquid line temperature probe (`{part_num}`), sealed connection with marine-grade heat shrink (`{part_num}`), and verified fan staging logic."
            ],
            "parts": [
                ["NTC Immersion Thermistor Sensor Probe", "Thermal Conductive Paste"],
                ["Suction/Discharge Pressure Transducer Kit (0-500 PSI)", "Sensor Connector Cable Assembly"],
                ["High Temperature Thermistor Probe", "Heat Shrink Tubing Kit"],
                ["Water Temperature Sensor Assembly", "Electronic Contact Cleaner Spray"],
                ["Pressure Transducer (0-500 PSI)", "5VDC Regulating Module", "Wiring Pigtail"],
                ["Liquid Line Temperature Sensor", "Marine-Grade Heat Shrink", "Zip Ties"]
            ],
            "downtime": (1.0, 3.0)
        }
    },
    "Power Transformer": {
        "oil leakage": {
            "symptoms": [
                "Transformer main oil level gauge showing `{percent}` low level (`near bottom mark`). Noticeable {adj} dielectric oil pooling (`{length} ft` spread) on concrete pad under radiator banks.",
                "Oil dripping steadily (`{hz} drops per min`) from top cover bushing turret gasket area. Transformer tank exterior coated in {adj} dust and oil (`{thickness} inch` thick).",
                "Buchholz relay minor alarm active (`{debris_amt}` gas/air collection in chamber). Inspection revealed {adj} oil seep along main tank cover bolted flange (`{vibe}` vibration on fins).",
                "Ops flagged oil leakage from radiator drain valve and tap changer gasket. Dielectric oil level dropped `{degree}` below normal indicator mark (`-{percent}` volume).",
                "Nitrogen blanket pressure dropping rapidly (`-{press_drop} PSI/day`). Oil weeping (`{gpm} oz/hr`) around LV bushing mounting flange.",
                "Thermal imaging shows cold spot (`{temp}`\u00b0C) on top radiator headers, indicating oil level has dropped below the circulation loops (`{clog_pct}` loss)."
            ],
            "root_causes": [
                "Age-related hardening, shrinkage, and compression set of nitrile rubber gaskets (`{thickness} inch` gap) on main tank cover and bushing flanges after `{years}` years of outdoor exposure.",
                "Thermal expansion and contraction cycles (`{temp_rc}`\u00b0C swings) loosened bolted flange connections (`{torque}` under-torqued) across cooling radiator bank manifolds.",
                "Corrosion pinhole (`{clearance} gap`) developed at bottom weld seam of external cooling radiator fin due to water pooling (`pH {ph_val}`) and debris trapping.",
                "Degraded O-ring seal (`{part_num}`) on no-load tap changer shaft assembly allowing slow weepage of insulating mineral oil under `{press} PSI` static head pressure.",
                "Vibration from core magnetostriction (`{hz}` frequency) fatigued the brass drain valve threads (`{runout} inch` play) over `{time_period}`.",
                "Gasket failure (`{clog_pct}` torn) on the sudden pressure relay (`SPR`) mounting flange allowed pressurized nitrogen and oil mist to escape."
            ],
            "actions": [
                "De-energized and grounded transformer, lowered oil level slightly, re-torqued main cover and bushing flange bolts (`{torque}` torque) in crisscross pattern, and topped off with `{lbs_charge} gal` degassed mineral oil.",
                "Isolated transformer, replaced degraded bushing turret gaskets and radiator flange gaskets using nitrile cork sheets (`{part_num}`), vacuum treated and topped off dielectric oil (`{lbs_charge} gal`).",
                "Repaired leaking radiator weld seam using approved epoxy/brazing procedure (`{part_num}`), replaced tap changer O-ring seal, and refilled transformer with certified Type II dielectric mineral oil (`{lbs_charge} drum`).",
                "Re-torqued all exterior radiator and cover flange bolts to `{torque}`, replaced leaking drain valve assembly (`{part_num}`), topped off insulating oil, and pulled oil sample for DGA test (`{ppm} ppm`).",
                "Replaced defective sudden pressure relay gasket (`{part_num}`), purged headspace with dry nitrogen (`{press} PSI`), and verified leak-tight seal with soap solution.",
                "Drained `{lbs_charge} gal` of oil, removed LV bushing, cleaned sealing surfaces (`{debris_amt}` removed), installed new molded nitrile gasket (`{part_num}`), and reassembled."
            ],
            "parts": [
                ["Nitrile-Cork Transformer Gasket Sheet Kit", "Type II Inhibited Dielectric Mineral Oil (15 Gallons)", "Flange Bolt Set"],
                ["Bushing Turret Gasket Set", "Radiator Flange O-Rings (Pack of 8)", "Dielectric Transformer Oil (25 Gallons)"],
                ["Tap Changer Shaft O-Ring Kit", "Transformer Drain Valve 2-inch", "Inhibited Mineral Oil (10 Gal)"],
                ["Complete Transformer Sealing Gasket Kit", "Dielectric Oil Top-off Drums (20 Gal)"],
                ["Sudden Pressure Relay Gasket", "Nitrogen Cylinder", "Leak Detector Solution"],
                ["LV Bushing Molded Gasket", "Type II Oil (55 Gal Drum)", "Contact Cleaner Spray"]
            ],
            "downtime": (6.0, 10.5)
        },
        "winding insulation degradation": {
            "symptoms": [
                "Dissolved Gas Analysis (DGA) annual oil sample showed elevated acetylene (`> {ppm} ppm`) and hydrogen (`> 300 ppm`), indicating internal arcing/partial discharge.",
                "Power factor / Tan-Delta test on transformer windings increased to `{percent}` (`normal < 0.5%`). Furan analysis indicates severe Kraft paper insulation aging (`DP < {hz}`).",
                "Transformer emitting {adj} buzzing/crackling sound inside tank (`{vibe}` in/sec RMS on shell). Ultrasonic acoustic survey detected partial discharge (`{hz}` pulses/sec) near HV winding.",
                "Megger insulation resistance between HV and LV windings dropped `{percent}` compared to factory baseline (`reading {mg_ohm} Mega-ohms at 5kV`).",
                "Oil moisture content critically high (`{ppm} ppm`). Breakdown voltage (dielectric strength) dropped to `{volts} kV` (`warning < 30kV`).",
                "Buchholz relay tripped transformer off-line. Gas sample from relay analyzed as `{percent}` combustible (fault gases)."
            ],
            "root_causes": [
                "Long-term thermal degradation and chemical depolymerization of Kraft paper winding insulation caused by operating at sustained high load temperatures (`> {temp_rc}\u00b0C`) over `{years}` years.",
                "Moisture ingress into dielectric oil (`water content > {ppm} ppm`) absorbed by cellulose paper insulation, drastically reducing breakdown voltage capacity (`< {volts} kV`).",
                "Transient overvoltages (`{volts}` spike) from switching surges and lightning strikes caused micro-perforations and partial discharge inside inter-turn paper insulation.",
                "Sludge formation (`{thickness} inch` thick) from oxidized dielectric oil deposited onto winding ducts, restricting localized natural oil convection and creating severe thermal hotspots (`{temp_rc}\u00b0C`).",
                "Free water accumulation (`{lbs_charge} gallons`) in tank bottom due to failed silica gel breather (`{time_period}` saturation) and poor tank sealing.",
                "Loose core clamping bolts (`{torque}` under-torqued) caused core lamination vibration (`{hz}`), mechanically abrading the winding insulation (`{clearance} gap`)."
            ],
            "actions": [
                "Scheduled emergency outage, connected mobile vacuum oil purification/dehydration rig, circulated and dried oil to `< {ppm} ppm` moisture, and added metal passivator chemical (`{part_num}`).",
                "Performed on-site vacuum oil processing and Fuller's earth reclamation (`{part_num}`) to remove polar compounds and acids, dried winding cellulose, and re-tested power factor (`Tan-Delta < 0.4%`).",
                "De-energized transformer, performed comprehensive electrical testing (TTR, Winding Resistance, Sweep Frequency Response Analysis), dried oil via vacuum rig, and added antioxidant additives (`{part_num}`).",
                "Processed transformer dielectric oil through vacuum dehydration unit for `{hours}` hours, replaced silica gel breather desiccant (`{part_num}`), and recommended load reduction (`< {percent}`) pending complete core/winding overhaul.",
                "Drained `{lbs_charge} gal` free water from tank bottom, replaced breached explosion vent diaphragm (`{part_num}`), and ran thermo-vacuum oil treatment for `{time_period}`.",
                "Untanked core assembly, tightened loose core clamps (`{torque}` torque), repaired abraded insulation with crepe paper taping (`{part_num}`), and baked core to dry."
            ],
            "parts": [
                ["Fuller's Earth Filter Cartridges (Set of 6)", "Silica Gel Breather Desiccant Charge (10 lbs)", "Oil Passivator Additive (1 Gal)"],
                ["Vacuum Rig Filter Elements", "Type II Dielectric Oil Top-off (30 Gal)", "Indicating Silica Gel Desiccant"],
                ["Inhibited Dielectric Mineral Oil (50 Gal)", "Transformer Breather Assembly", "Antioxidant Oil Additive Package"],
                ["Silica Gel Desiccant Beads (15 lbs)", "Oil Filter Cores", "Gasket Set"],
                ["Explosion Vent Diaphragm", "Vacuum Rig Coalescing Filter", "Type II Oil (5 Gal)"],
                ["Crepe Paper Insulation Tape", "Cotton Tying Cord", "Varnish Coating (1 Gal)"]
            ],
            "downtime": (8.0, 12.0)
        },
        "overheating": {
            "symptoms": [
                "Top oil temperature gauge reading `{temp}`\u00b0C (`high alarm setpoint 85\u00b0C`). Winding hot-spot temperature indicator reaching `102\u00b0C` under `{percent}` load.",
                "Cooling radiator banks extremely hot (`{temp}`\u00b0C measured via IR camera). Multiple forced-air cooling fans not spinning (`0 Amps` fan bank draw).",
                "Transformer tripping on top-stage oil temperature relay (`>{temp}`\u00b0C) during peak afternoon ambient temperature (`+{degree}` above design).",
                "Ops reported strong heat waves radiating from transformer tank. Infrared scan showed `{degree}` localized heating around LV bushing terminations (`115\u00b0C`).",
                "Oil temperature rising rapidly (`+{temp}\u00b0C/hour`). Cooling fan stage 2 failed to engage at `{temp}`\u00b0C setpoint.",
                "Distinct {adj} burning oil smell (`{ppm}` VOCs) near transformer. Dissolved gas analysis shows spike in ethylene and ethane (`hot metal > 300\u00b0C`)."
            ],
            "root_causes": [
                "Cooling fan bank contactor failure (`{volts}` coil open) and tripped motor circuit breakers prevented forced-air cooling (`FA stage`) from engaging during heavy load (`{current} Amps`).",
                "External radiator fins heavily clogged (`{clog_pct}` blocked) with airborne cottonwood fluff, dust, and industrial dirt, reducing convective heat rejection by `> 50%`.",
                "Severe harmonic current loading (`THD > {percent}`) from downstream VFD drives caused elevated eddy current and stray load losses inside transformer core/windings.",
                "Low dielectric oil level (`-{percent}` capacity) in main tank prevented natural circulation (`ONAN`) of hot oil through top radiator headers.",
                "Failed temperature capillary probe (`{part_num}`) on the winding hot-spot simulator preventing the cooling fan control circuit from closing.",
                "Internal circulating currents (`{current} Amps`) between parallel winding strands due to broken transposition crossover (`{gap} inch` arc gap)."
            ],
            "actions": [
                "Replaced defective cooling fan bank contactor (`{part_num}`) and thermal overload relays, pressure washed radiator fins with low-pressure water (`{press} PSI`), and verified all 6 cooling fans operational.",
                "Thoroughly washed exterior radiator cooling fins to remove cottonwood/dirt blockage (`{debris_amt}`), replaced 2 burned-out cooling fan motors (`{part_num}`), and checked oil level indicator.",
                "Replaced faulty cooling fan control thermostat switch (`{part_num}`), serviced fan bank electrical panel, cleaned radiator fins, and verified top oil temperature dropped to `71\u00b0C`.",
                "Topped off dielectric oil level (`{lbs_charge} gal`) to normal operating mark, cleaned radiator fin passages, and replaced loose LV bushing internal terminal palm connections (`{torque}` torque).",
                "Replaced broken temperature capillary tube gauge (`{part_num}`), recalibrated winding hot-spot dial (`{temp}\u00b0C`), and tested fan staging relays (`{hz}` manual cycles).",
                "De-rated transformer capacity to `{percent}`, scheduled offline internal inspection to repair winding transposition, and increased forced cooling duty cycle."
            ],
            "parts": [
                ["Cooling Fan Contactor 3-Pole 240V", "Thermal Overload Relay", "Cooling Fan Motor 1/2 HP TEAO"],
                ["Replacement Cooling Fan Assemblies (Set of 2)", "Fan Control Thermostat Switch", "Radiator Fin Cleaner"],
                ["Fan Bank Control Relay", "Cooling Fan Motor 460V", "Type II Dielectric Oil (10 Gal)"],
                ["LV Bushing Terminal Palm Clamp Kit", "Fan Contactor Kit"],
                ["Capillary Temperature Gauge Assembly", "Control Relay 120V", "Wire Lugs"],
                ["Warning Placard", "Supplemental Box Fan (Temporary)"]
            ],
            "downtime": (3.0, 6.5)
        }
    },
    "Main Distribution Panel": {
        "breaker trip failure": {
            "symptoms": [
                "Main molded case circuit breaker (`MCCB`) failed to trip during downstream short circuit event (`{current} Amps` fault), causing upstream feeder breaker to clear fault.",
                "Electronic trip unit on main breaker showing fault LED flashing (`{hz} Hz`). Breaker fails to close or reset (`{degree}` mechanical binding in handle lever).",
                "Routine secondary injection testing revealed feeder breaker long-time and short-time trip units failed to actuate within specified curve (`> {percent}` time delay).",
                "Ops reported breaker handle stuck in middle/tripped position (`{torque}` resistance). Internal mechanism clicking but contacts will not latch closed.",
                "Arc flash relay initiated trip command (`{time_period}` response) but main ACB failed to open. Backup breaker cleared fault after `{hz}` cycles.",
                "Breaker randomly trips open with no load (`0 Amps`). Spring charge motor continuously hunting (`{noise}`) but won't hold charge."
            ],
            "root_causes": [
                "Mechanical binding and hardening of factory grease (`{thickness} inch` thick buildup) inside breaker operating mechanism due to lack of periodic exercising over `{years}` years.",
                "Electronic trip unit (`ETU`) microprocessor failure caused by voltage surge transients (`{volts}` peak) on control power feed.",
                "Shunt trip coil burnout (`{mg_ohm}` open circuit) preventing remote safety interlock system from opening breaker (`{time_period}` delay).",
                "Contact welding or severe arcing erosion (`{clearance} gap`) across primary moving contact pads following repeated high-current fault interruptions (`> {current} Amps`).",
                "Broken trip latch pin (`{part_num}`) inside the mechanical trip bar assembly prevented ETU solenoid from unlatching the main spring.",
                "Blown control power fuse (`{current}A`) for the electronic trip unit due to a shorted electrolytic capacitor (`{mg_ohm}`) on the trip unit PCB."
            ],
            "actions": [
                "De-energized distribution panel, removed failed molded case breaker, installed new exact-replacement MCCB (`{part_num}`) with calibrated electronic trip unit, and tested via secondary injection.",
                "Replaced defective electronic trip unit (`ETU`) module (`{part_num}`), lubricated mechanical latching mechanism with approved dielectric synthetic grease (`{part_num}`), and verified trip curve timing.",
                "Swapped out jammed circuit breaker assembly, installed new shunt trip accessory coil (`{part_num}`), torqued busbar connections to `{torque}`, and performed insulation resistance test (`{percent}`).",
                "Replaced complete draw-out air circuit breaker (`ACB`) assembly (`{part_num}`), renewed bus terminal stabs (`{part_num}`), and verified all protection settings against engineering coordination study.",
                "Removed ACB from cassette, replaced fractured trip latch assembly (`{part_num}`), relubricated entire mechanism (`{part_num}`), and verified opening time (`{time_period}`).",
                "Installed new ETU board (`{part_num}`), replaced control power fuses (`{current}A`), loaded coordination settings file, and verified primary injection trip points."
            ],
            "parts": [
                ["Replacement Molded Case Circuit Breaker (MCCB 400A)", "Busbar Mounting Hardware Kit"],
                ["Electronic Trip Unit Module (ETU Rebuild Kit)", "Synthetic Breaker Lubricating Grease (1 Tube)"],
                ["Draw-Out Circuit Breaker Assembly 800A", "Shunt Trip Coil 120VAC", "Phase Barrier Kit"],
                ["Replacement MCCB 600A Assembly", "Secondary Injection Test Plug Adapter"],
                ["Mechanical Trip Latch Assembly", "Molykote Lubricant", "ACB Alignment Tool"],
                ["ETU Control Board Replacement", "Control Power Fuses (2A)", "Programming Cable"]
            ],
            "downtime": (4.0, 8.0)
        },
        "loose connections": {
            "symptoms": [
                "Infrared (`IR`) thermography inspection revealed severe hotspot (`{temp}`\u00b0C, `delta-T > {temp_rc}\u00b0C above ambient`) on Phase B main busbar lug termination.",
                "Loud {adj} buzzing and arcing sound (`{noise}`) heard inside distribution panel enclosure. Localized {adj} discoloration on bus connection bolts (`{percent}` torque loss).",
                "Voltage imbalance of `{degree}` across panel busbars under heavy load. Noticeable smell of heated ozone/insulation (`{ppm}` VOCs) near panel vents.",
                "Phase A terminal lug glowing red under peak shift current (`{current}` Amps). Thermal imaging shows `{temp}\u00b0C` temperature at cable-to-bus bolted joint.",
                "Voltage drop of `{volts} V` measured across a single bolted bus splice joint (`normal < 0.1V`). Joint resistance measured at `{mg_ohm}` (high).",
                "Main breaker thermal-magnetic trip unit tripping on Phase C overload (`{current} Amps`), but actual phase current is normal. Heat from loose connection conducting into breaker thermal element."
            ],
            "root_causes": [
                "Thermal expansion and contraction cycles over `{years}` years of fluctuating load current (`{percent}` swings) caused gradual loosening of bolted busbar and cable lug mechanical terminations.",
                "Improper initial torque application during installation (`bolts tightened without calibrated torque wrench` to only `{torque}`) or missing Belleville spring washers.",
                "Vibration transmitted (`{vibe}` in/sec RMS) from nearby heavy manufacturing equipment loosened bolted terminal connections on main bus joints over `{time_period}`.",
                "Galvanic corrosion and oxidation between dissimilar metals (`copper cable to aluminum bus lug`) causing high joint contact resistance (`{mg_ohm}`).",
                "Creep (cold flow) of aluminum feeder cables inside mechanical set-screw lugs (`{part_num}`) reduced contact pressure by `{percent}`.",
                "Overtightening (`{torque}` torque) during previous PM stretched the grade 5 bolt past its yield point, causing loss of clamping force (`{clearance} gap`)."
            ],
            "actions": [
                "Scheduled emergency shutdown, disassembled Phase B cable lug and busbar joint, cleaned oxidized contact faces with Scotch-Brite, applied conductive joint compound (`{part_num}`), and torqued bolts to factory spec (`{torque}`) using Belleville washers.",
                "De-energized main panel, performed complete torquing check across all main bus connections and feeder breaker terminals using calibrated torque wrench (`{torque}`), and applied anti-oxidation paste (`{part_num}`).",
                "Replaced heat-damaged Phase A and B terminal lugs (`{part_num}`), polished copper bus interfaces, applied electrical joint compound, torqued hardware to specification, and re-scanned with IR camera under load (`joint temp stabilized at {temp}\u00b0C`).",
                "Cleaned arced busbar contact surfaces, installed new silver-plated copper splice plates (`{part_num}`) and high-tensile hardware with Belleville washers, and verified micro-ohm contact resistance (`< {mg_ohm}`).",
                "Cut back heat-damaged aluminum cable (`{length} ft`), installed new dual-rated compression lugs (`{part_num}`) using hydraulic crimper, and terminated to bus with new hardware.",
                "Drilled out yielded hardware (`{part_num}`), replaced with Grade 8 bolts and Belleville washers (`{part_num}`), torqued to `{torque}`, and applied torque seal indicator mark."
            ],
            "parts": [
                ["Heavy-Duty Copper Compression Lugs (Set of 3)", "Belleville Spring Washers & Grade 8 Bolts", "Conductive Electrical Joint Compound (1 Tube)"],
                ["Silver-Plated Busbar Splice Plates (2-Pack)", "Anti-Oxidation Compound Paste", "High-Tensile Hardware Kit"],
                ["Replacement Terminal Lugs 500 MCM", "Hardware & Washer Kit", "Electrical Contact Cleaner"],
                ["Bus Splice Hardware Kit", "Silver Plated Splice Plate", "Belleville Washer Set (20-Pack)"],
                ["Dual-Rated Al/Cu Compression Lugs 600MCM (3-Pack)", "Heat Shrink Tubing (Thick Wall)", "No-Ox Paste"],
                ["Grade 8 Bolt Assortment Kit", "Torque Seal Marker (Red)", "Belleville Washers"]
            ],
            "downtime": (2.0, 5.0)
        },
        "insulation breakdown": {
            "symptoms": [
                "Main distribution panel tripped incoming feeder phase-to-ground fault protection (`{current} Amps`). Strong {adj} smell of ionized electrical arc and smoke (`{ppm}` particulates) inside cabinet.",
                "Phase-to-phase flashover occurred across main busbar support insulators during humid morning startup (`{degree}` soot deposits across backplane).",
                "Megger insulation resistance check across panel busbars to ground measured `{mg_ohm}` (`critical hazard threshold < 1.0 M-ohm`).",
                "Loud {adj} tracking and crackling sound (`{noise}`) heard along red/glastic standoff insulators supporting main copper bus (`{vibe}` vibration).",
                "Corona discharge visible (`{percent}` glow) around sharp busbar edges in dark cabinet. Ultrasonic detector reading `{hz}` Hz partial discharge pulses.",
                "Ground fault relay tripped offline (`{time_period}` clearing time). Insulation on Phase B vertical bus shows bubbling/blistering (`{thickness} inch` deep)."
            ],
            "root_causes": [
                "Accumulation of conductive industrial dust, carbon soot, and high ambient moisture (`{percent}` RH) across busbar standoff insulators formed a tracking path to ground (`{mg_ohm}`).",
                "Aging and thermal embrittlement (`{temp_rc}\u00b0C` history) of red Glastic/GPO-3 busbar support insulators caused micro-cracks (`{gap} inch` gap) that tracked under high voltage stress.",
                "Entry of rodents/pests (`{debris_amt}` found) into distribution cabinet through unsealed floor conduits caused direct phase-to-ground short across energized bus.",
                "Transient overvoltage strike (`{volts}` peak) exceeded dielectric breakdown limit of degraded busbar shrink-tubing insulation (`{thickness} inch` remaining).",
                "Corrosive chemical vapor ingress (`pH {ph_val}`) eroded the epoxy coating on the busbars, exposing bare copper to phase-to-phase arc tracking.",
                "Sharp un-chamfered edges on copper busbar splices created high localized electrical field stress (`{percent}` above rating), degrading adjacent insulation."
            ],
            "actions": [
                "Isolated main feed, cleaned soot and carbon tracking (`{debris_amt}`) from panel interior using dielectric solvent (`{part_num}`), replaced all 6 Glastic busbar support standoff insulators, and performed 1000V Megger test (`reading > {mg_ohm}`).",
                "De-energized panel, replaced flashover-damaged bus support insulators (`{part_num}`) and phase barriers, applied heat-shrink insulating tubing over exposed buswork, and sealed conduit entry points with duct seal (`{part_num}`).",
                "Replaced tracked busbar standoff insulators, cleaned copper bus surfaces, installed new polycarbonate phase barriers (`{part_num}`), and verified insulation resistance (`{mg_ohm}`) across all phases before re-energization.",
                "Replaced cracked standoff insulators (`{part_num}`), re-torqued bus supports (`{torque}`), thoroughly vacuumed and solvent cleaned panel cabinet (`{part_num}`), and installed rodent screens on all cabinet ventilation louvers.",
                "Removed chemically degraded epoxy busbars, installed new fully insulated fluid-bed coated busbars (`{part_num}`), and sealed panel penetrations (`{part_num}`).",
                "Disassembled splice joints, radiused sharp copper edges with file (`{clearance} chamfer`), applied corona-suppressing tape (`{part_num}`), and re-meggered at 5kV (`{mg_ohm}`)."
            ],
            "parts": [
                ["Glastic/GPO-3 Busbar Standoff Insulators (6-Pack)", "Dielectric Solvent Cleaner (3 Cans)", "Polycarbonate Phase Barriers (Set of 3)"],
                ["Bus Support Insulator Assembly Kit", "Heavy-Wall Busbar Heat Shrink Tubing (10ft)", "Duct Seal Compound (2 Plugs)"],
                ["Replacement Standoff Insulators (Pack of 8)", "Phase Barrier Kit", "Industrial Contact & Cabinet Cleaner"],
                ["GPO-3 Insulator Set", "Bus Mount Bolts", "Dielectric Cleaning Solvent"],
                ["Epoxy Insulated Busbar Set", "Silicone Cabinet Sealant (2 Tubes)", "GPO-3 Standoffs"],
                ["Semi-Conductive Corona Tape (2 Rolls)", "High-Voltage Splice Tape (3 Rolls)", "Red Insulating Varnish Spray"]
            ],
            "downtime": (6.0, 11.0)
        }
    },
    "Steam Boiler": {
        "tube leak": {
            "symptoms": [
                "Continuous loss of boiler water level requiring `{percent}` excessive makeup water feed (`makeup pump running near 100%`). High chemical consumption noted (`{ppm} ppm`).",
                "Loud {adj} hissing and steam escaping sound (`{noise}`) audible inside furnace firebox when burner cycles off. White steam blowing out of stack.",
                "Acoustic tube leak detection alarm triggered (`{hz} Hz` signature). Boiler pressure dropping `{press_drop}` PSI below setpoint despite burner firing at high fire.",
                "Inspection port reveals water dripping onto refractory hearth (`{length} ft` pooling). Combustion efficiency analyzer shows `{temp}`\u00b0C drop in flue gas temp with high moisture.",
                "Flue gas oxygen (`O2`) levels abnormally low (`< {percent}%`) due to steam displacement. Boiler struggling to maintain `{press} PSI` header pressure.",
                "Conductivity of boiler water unexpectedly low (`{mg_ohm} uS/cm`) despite high chemical feed, indicating massive dilution from makeup water."
            ],
            "root_causes": [
                "Localized waterside oxygen pitting corrosion (`{thickness} inch` deep) inside fire tubes due to intermittent failure of boiler feedwater deaerator (`{temp_rc}\u00b0C` operation) / oxygen scavenger chemical dosing.",
                "Fireside acid dew-point corrosion on outer tube walls caused by burning sulfur-bearing fuel during low-load/low-temperature operation (`< {temp_rc}\u00b0C` stack temp).",
                "Thermal fatigue cracking (`{runout} inch` long) at tube-to-tubesheet rolled/welded joint caused by rapid cold startups (`{time_period}` ramp) and thermal shock.",
                "Waterside scale accumulation (`> {thickness} inch thick`) caused localized insulating effect, leading to tube metal overheating (`{temp_rc}\u00b0C`) and stress rupture.",
                "Soot blower steam impingement (`{press} PSI`) eroded the tube wall thickness over `{years}` years of operation.",
                "Stress corrosion cracking (`SCC`) near the tubesheet weld due to excessive residual rolling stresses (`{torque}`) and high causticity (`pH {ph_val}`)."
            ],
            "actions": [
                "Isolated and cooled down boiler, opened front and rear doors, identified 3 leaking fire tubes using hydrostatic test (`{press} PSI`), reamed out and cut out failed tubes, rolled and beaded in new seamless steel boiler tubes (`{part_num}`), and hydro-tested to 150 PSI.",
                "Opened fireside doors, plugged 2 leaking tubes using certified tapered steel boiler tube plugs (`{part_num}`) as temporary repair, calibrated oxygen scavenger chemical dosing pump, and scheduled full retubing during summer outage.",
                "Performed complete tube replacement of bottom two passes (18 tubes) (`{part_num}`), renewed front and rear refractory door gaskets (`{part_num}`), performed boil-out chemical cleaning, and verified zero drop on `{time_period}` hydro test.",
                "Cut out cracked fire tubes, ground out and re-welded/rolled tube-to-tubesheet joints on adjacent tubes, replaced door gaskets, and adjusted deaerator operating temperature to `105\u00b0C` (`{temp}\u00b0C`).",
                "Replaced steam-eroded tubes (`{part_num}`), recalibrated soot blower steam pressure regulator (`{press} PSI`), and verified impingement angles.",
                "Stress-relieved tubesheet welds using ceramic heating pads (`{temp}\u00b0C`), adjusted blowdown rate to control alkalinity (`pH {ph_val}`), and replaced SCC-damaged tubes (`{part_num}`)."
            ],
            "parts": [
                ["Seamless Steel Boiler Tubes 2.5-inch OD (Bundle of 4)", "Refractory Door Rope Gasket Kit", "Tubesheet Ferrules"],
                ["Tapered Steel Boiler Tube Plugs (Set of 4)", "High-Temperature Door Gasket Rope", "Oxygen Scavenger Chemical (10 Gal)"],
                ["Replacement Fire Tubes SA-178 (18-Pack)", "Front/Rear Boiler Door Refractory & Gasket Kit"],
                ["Boiler Tube Plug Kit", "Refractory Cement Patch (50 lb Bag)", "Door Sealing Gasket"],
                ["Heavy Wall Boiler Tubes", "Soot Blower Valve Rebuild Kit", "Gasket Sheet"],
                ["SA-210 Medium Carbon Tubes", "Ceramic Heating Pads (Rental)", "Alkalinity Test Kit"]
            ],
            "downtime": (10.0, 12.0)
        },
        "burner malfunction": {
            "symptoms": [
                "Flame safeguard controller (`FSG`) locked out on primary flame failure during ignition sequence. Burner blower motor running but zero flame establishment.",
                "Burner flame pulsating and rumbling (`{noise}`) inside combustion chamber (`{vibe}` vibration on front plate). High CO emissions (`> {ppm} ppm`) on stack analyzer.",
                "Intermittent flame failure lockouts during high-to-low fire modulation transitions. Tech observed {adj} yellow, smoky flame instead of tight blue pattern.",
                "Pilot ignition spark clicking (`{noise}`) but main gas valve fails to open. Flame scanner signal strength reading `{percent}` weak (`< {volts} Volts DC`).",
                "Fuel pressure switch (`{press} PSI` setpoint) constantly tripping during high fire. Burner hunting and failing to stabilize.",
                "Loud {adj} harmonic howling (`{hz} Hz`) from combustion air blower. Air-fuel ratio way off (`O2 > {percent}%`)."
            ],
            "root_causes": [
                "UV flame scanner lens heavily fouled (`{thickness} inch` buildup) with soot and oil film, causing weak flame signal that dropped below holding threshold (`{volts} V`) of safety relay.",
                "Gas pressure regulator diaphragm drift (`-{press_drop} PSI`) caused improper air-to-fuel ratio (`excessively rich mixture`) leading to flame instability and high CO.",
                "Ignition electrode spark gap misaligned (`{gap} inch`) or porcelain insulator cracked, preventing reliable high-voltage pilot ignition arc (`{volts} kV`).",
                "Modulating linkage motor actuator slipped (`{runout} inch`) on damper shaft, causing combustion air damper to lag behind fuel valve opening during firing rate changes.",
                "Partially plugged main gas strainer (`{clog_pct}` blocked) restricted flow during high demand, causing dynamic pressure drop.",
                "Combustion air blower squirrel cage impeller heavily coated with shop dust (`{debris_amt}`), reducing air delivery by `{percent}`."
            ],
            "actions": [
                "Cleaned UV flame scanner lens with alcohol swab (`{part_num}`), adjusted ignition electrode spark gap to `1/8 inch`, verified pilot flame signal strength (`3.5V DC`), and checked complete firing sequence.",
                "Replaced defective UV flame scanner head and ignition electrode assembly (`{part_num}`), tightened and recalibrated air/fuel modulating linkage arms (`{part_num}`), and set combustion profile using digital flue gas analyzer.",
                "Replaced main gas solenoid valve coil (`{part_num}`) and faulty modulating servo motor (`{part_num}`), reset gas pressure regulator to `14 inches WC`, and performed multi-point combustion efficiency tuning (`O2 set at 3.5%`).",
                "Cleaned burner diffuser and ignition assembly, replaced cracked pilot electrode ceramic (`{part_num}`), calibrated fuel/air cam profile across all firing rates, and cleared flame safeguard lockout.",
                "Isolated gas train, removed and cleaned primary gas strainer basket (`{debris_amt}` removed), verified dynamic gas pressure (`{press} PSI`), and tuned high-fire rate.",
                "Removed combustion blower housing, pressure washed impeller (`{press} PSI`), verified motor amp draw (`{current} A`), and re-tuned jackshaft linkage."
            ],
            "parts": [
                ["UV Flame Scanner Sensor Head", "Ignition Electrode & Porcelain Assembly", "High-Voltage Ignition Wire"],
                ["Modulating Servo Actuator Motor", "Gas Solenoid Valve Coil 120V", "Burner Diffuser Gasket"],
                ["Flame Scanner Replacement Unit", "Ignition Transformer 10kV", "Linkage Ball Joints (4-Pack)"],
                ["Pilot Electrode Kit", "UV Scanner Lens Cleaning Swabs", "Burner Front Plate Gasket"],
                ["Gas Strainer Replacement Basket", "O-Ring Kit", "Manometer Calibration Fluid"],
                ["Blower Housing Gasket", "Motor Bearings (Set of 2)", "Linkage Arms"]
            ],
            "downtime": (2.5, 5.5)
        },
        "scale buildup": {
            "symptoms": [
                "Boiler stack temperature steadily rising (`reaching {temp}\u00b0C vs design 210\u00b0C at high fire`), indicating severe loss of waterside heat transfer efficiency.",
                "Waterside inspection through handholes reveals `{thickness} inch` thick hard calcium/silicate mineral scale crust on fire tube surfaces and furnace tube sheet.",
                "Boiler making {adj} popping and kettling sounds (`{noise}`) from waterside during high fire operation. Bottom blowdown discharging {adj} heavy scale chips.",
                "Fuel consumption increased by `{percent}%` per ton of steam generated (`{degree}` efficiency drop). Low water cutoff float chamber fouled with sludge accumulation.",
                "Feedwater pump struggling to maintain level (`{current} Amps` high draw). Feedwater piping pressure unusually high (`{press} PSI`).",
                "Visual inspection shows `{percent}%` of tube passes bridged solid with scale. Acid clean required."
            ],
            "root_causes": [
                "Improper functioning of duplex water softener (resin exhausted after `{years}` years or regeneration timer failure) allowed hard water (`> {ppm} ppm total hardness`) directly into boiler feedwater.",
                "Lack of daily bottom blowdown execution by plant operators allowed suspended solids (`{ppm} ppm TDS`) and sludge to bake onto hot tubesheet surfaces.",
                "Under-dosing of internal boiler scale treatment chemical (`phosphate/polymer dispersant`) over past `{time_period}` due to chemical pump air-lock.",
                "High feedwater silica concentration (`> {ppm} ppm`) combined with excessive cycles of concentration formed hard, dense silicate scale (`{thickness} inch`) that cannot be removed by normal blowdown.",
                "Condensate return contaminated with process calcium (`{ppm} ppm hardness`) from a leaking heat exchanger.",
                "Failure of the automatic surface blowdown controller (probe coated with `{thickness} inch` scale) allowed TDS to climb to `{ppm} ppm`."
            ],
            "actions": [
                "Took boiler offline, opened all handholes and manways, performed high-pressure waterside mechanical rodding/flushing (`{press} PSI`) of all tubes, serviced water softener resin, and calibrated chemical feed pumps.",
                "Circulated inhibited sulfamic acid descaling solution (`{part_num}`) through boiler waterside loop for `{hours}` hours, neutralized and flushed until pH neutral, inspected tubes (`scale completely cleared`), and renewed handhole gaskets.",
                "Mechanically scraped tubesheet and lower drum surfaces through handholes, flushed heavy scale debris (`{debris_amt}`) from bottom header, rebuilt automatic surface blowdown controller (`{part_num}`), and replaced water softener resin.",
                "Performed chemical boil-out using alkaline/polymer descaling compound (`{part_num}`), flushed waterside thoroughly, replaced low-water cutoff float bowl assembly (`{part_num}`), and established rigorous daily blowdown schedule.",
                "Located and repaired leaking process heat exchanger (`{part_num}`), acid washed boiler waterside (`{lbs_charge} gal` acid), and re-passivated metal surfaces.",
                "Replaced coated conductivity probe (`{part_num}`), recalibrated auto-blowdown valve (`{hz}` cycles/hr), and mechanically punched all firetubes (`{length} ft` reach)."
            ],
            "parts": [
                ["Inhibited Sulfamic Acid Boiler Descaler (30 Gallons)", "Neutralizing Compound (10 lbs)", "Handhole & Manway Gasket Set (Pack of 12)"],
                ["Water Softener Cation Resin (5 Bags)", "Boiler Handhole Gaskets (Top & Bottom Set)", "Internal Scale Treatment Chemical (15 Gal)"],
                ["Low-Water Cutoff Float Bowl Rebuild Kit", "Manway Spiral Wound Gasket", "Phosphate Scale Inhibitor (10 Gal)"],
                ["Boiler Descaling Acid Flush Kit", "Handhole Gasket Pack (16-Pack)", "Softener Valve Rebuild Kit"],
                ["Process Heat Exchanger Tube Bundle", "Muriatic Acid (55 Gal)", "Passivation Chemical"],
                ["Conductivity Probe", "Blowdown Valve Actuator", "Tube Punching Brushes (Set of 3)"]
            ],
            "downtime": (6.5, 10.0)
        },
        "pressure relief valve failure": {
            "symptoms": [
                "Main safety relief valve weeping/simmering continuously (`{percent}` steam discharge through vent pipe to roof). Steam visible around valve discharge funnel.",
                "Relief valve popped off prematurely at `{press}` PSI during normal operation (`nameplate setpoint 150 PSI`). Valve fails to reseat tightly after blowing down.",
                "Safety relief valve leaking {adj} live steam (`{noise}` hissing) across seat during standby pressure. Valve body running extremely hot (`{temp}`\u00b0C).",
                "Annual boiler safety valve pop test failed: valve stuck closed during lever lifting test (`{torque}` pull) or opened `{press_drop} PSI` above stamped ASME set pressure.",
                "Valve chatters violently (`{hz} Hz`) when lifting, causing pipe hammer (`{vibe}` vibration) on the vent stack.",
                "Constant drip (`{gpm} gpm`) from safety valve drain hole, indicating seat is scored or scale-fouled."
            ],
            "root_causes": [
                "Corrosion, scale, and boiler alkalinity carryover particles (`{thickness} inch` debris) lodged between safety valve disc and stainless steel nozzle seat after previous simmer event.",
                "Fatigue relaxation or corrosion of internal safety valve helical compression spring caused reduction in popping set pressure (`-{press_drop} PSI`) over `{years}` years of continuous service.",
                "Improper pipe support on discharge vent piping exerted mechanical binding twisting strain (`{torque}`) on safety valve body, distorting internal seat alignment.",
                "Normal mechanical seat wear and wire-drawing erosion (`{gap} inch` groove) across sealing faces from prolonged minor steam weeping.",
                "Oversized safety valve for the current boiler load causing rapid cycling/chattering (`{hz} cycles/min`) and seat damage.",
                "Use of unapproved gagging tool during hydrostatic test deformed the valve spindle (`{runout} inch` runout)."
            ],
            "actions": [
                "Isolated boiler, removed leaking safety relief valve, installed certified code-stamped replacement ASME safety relief valve (`{part_num}`) set at 150 PSI, and verified zero leakage under full operating pressure.",
                "Replaced primary and secondary steam safety relief valves with calibrated code-stamped spares (`{part_num}`), adjusted vent piping expansion slip joint to eliminate mechanical strain, and tested pop pressure.",
                "Swapped out defective safety valve with NBBI certified replacement assembly (`{part_num}`), renewed flange gaskets and high-tensile studs, and documented ASME pop test during firing startup.",
                "Installed new factory-calibrated and sealed safety relief valve (`{part_num}`), re-supported discharge vent pipe to ensure zero weight on valve body, and verified reseating tightness.",
                "Replaced damaged valve with correctly sized ASME relief valve (`{part_num}`), secured vent piping with spring hangers, and verified smooth lift and reseat.",
                "Removed deformed valve, installed exact replacement (`{part_num}`), educated contractors on proper gagging procedures, and documented seal numbers."
            ],
            "parts": [
                ["ASME Section I Code-Stamped Safety Relief Valve (1.5x2.5 inch, 150 PSI)", "Spiral Wound Flange Gasket 1.5-inch", "High-Temp Stud Bolt Set"],
                ["Certified Steam Safety Relief Valve Assembly 150 PSI", "Discharge Pipe Drip Pan Elbow", "Flange Gasket Kit"],
                ["NBBI Certified Safety Valve 2-inch", "Spiral Wound Gasket", "High-Tensile Studs & Nuts"],
                ["Replacement ASME Safety Relief Valve", "Flange Mounting Hardware"],
                ["Reduced Capacity ASME Valve", "Spring Pipe Hangers", "Drip Pan"],
                ["Standard Safety Valve", "Test Gag Tool", "Tamper Evident Wire Seals"]
            ],
            "downtime": (2.5, 5.0)
        }
    },
    "Belt Conveyor": {
        "belt misalignment": {
            "symptoms": [
                "Conveyor belt mistracking severely (`{degree}` off-center toward right side). Belt edge rubbing against steel conveyor frame (`{noise}` squealing sound and rubber dust).",
                "Misalignment alignment switch alarm tripped, shutting down conveyor drive. Belt tracking edge frayed (`{degree}` wear) near head pulley area.",
                "Ops noted conveyor belt wandering back and forth (`{hz} cycles/min`) across troughing idlers during load surges. Heavy material spillage (`{degree}`) accumulating under carry side.",
                "Belt running `{length} inches` off-center at tail pulley return idlers. Rubbing noise (`{noise}`) and {adj} smell of hot rubber (`{ppm}` VOCs) near take-up assembly.",
                "Edge damage (`{thickness} inch` chunk missing) on the belt. The belt is folded over on the return side (`{percent}` folded).",
                "Conveyor belt repeatedly tripping the limit switch (`{hz}` times per hour). Visual inspection shows `{degree}` skew at the loading zone."
            ],
            "root_causes": [
                "Material buildup (`{thickness} inch` sticky wet clay/bulk product) frozen or caked onto head pulley and return idler rolls, creating uneven diameter and forcing belt to track to one side.",
                "Improper tension adjustment on gravity screw take-up assembly (`{torque}` uneven tension between left and right take-up bearings).",
                "Structural misalignment or frame skewing (`{degree}` out of square) caused by forklift impact against conveyor side support legs.",
                "Splice joint cut and joined at a slight diagonal angle (`{degree}` improper squareness during belt lacing/vulcanizing), causing rhythmic mistracking every belt revolution.",
                "Failed return idler bearings on one side (`{percent}` seized) causing asymmetric drag on the belt.",
                "Uneven loading (`{percent}` biased to one side) from the feed chute pushing the belt off-center."
            ],
            "actions": [
                "Locked out conveyor, manually scraped and cleaned hardened material buildup (`{debris_amt}`) from head pulley and return idlers, adjusted take-up screw tension equally (`{torque}` torque), and test ran belt to track center.",
                "Installed 3 self-aligning training return idlers (`{part_num}`) along return span, cleaned material off tail pulley wing rolls, squared take-up bearings, and verified belt centered under full load.",
                "Re-squared conveyor structural frame (`{degree}` correction), replaced 4 jammed return idler rollers (`{part_num}`), adjusted head and tail pulley parallelism using laser square, and fine-tuned tracking.",
                "Scraped caked debris from drive and tail pulleys, adjusted gravity take-up counterweight guides (`{clearance} clearance`), realigned troughing idler brackets, and verified straight tracking across all zones.",
                "Modified feed chute diverter plate (`{degree}` angle) to center load, replaced `{part_num}` worn return rollers, and installed edge trackers.",
                "Cut out crooked mechanical splice, re-squared belt ends using transit (`{degree}` tolerance), and installed new mechanical fasteners (`{part_num}`)."
            ],
            "parts": [
                ["Self-Aligning Training Idlers (Set of 3)", "Return Idler Rollers (4-Pack)"],
                ["Heavy-Duty Return Training Roller Assembly (2-Pack)", "Take-up Bearing Adjusting Bolt Kit"],
                ["Troughing Idler Bracket Set", "Replacement Wing Pulley Scraper Blades (2-Pack)"],
                ["Training Idler Set", "Idler Mounting Hardware Kit"],
                ["Deflector Plate Steel", "Return Idler Assemblies", "Edge Tracker Kit"],
                ["Mechanical Splice Kit", "Belt Squaring Tool", "Nylon Splice Pin"]
            ],
            "downtime": (1.5, 4.0)
        },
        "roller bearing failure": {
            "symptoms": [
                "Loud {adj} screeching, grinding, and {noise} sound emanating from carry-side troughing idler roller near Station 14 (`{hz} Hz` signature).",
                "Idler roller completely seized (`0 RPM rotation`). Conveyor belt sliding across stationary steel shell (`{degree}` flat spot worn into roller and hot rubber smell).",
                "Thermal inspection (`IR gun`) showed seized return idler bearing reaching `{temp}`\u00b0C. Sparks visible (`{degree}` hazard) under dark operating conditions.",
                "Multiple troughing idlers making {adj} clicking and metallic clattering sounds (`{vibe}` in/sec vibration on side rails). Bearing end caps pushed out with rusty grease.",
                "Roller shell detached from end disc (`{percent}` separation). Shaft rotating within the bearing inner race (`{clearance} gap`).",
                "Fugitive dust (`{ppm} ppm`) increasing because dropped material is falling on seized `{part_num}` idlers."
            ],
            "root_causes": [
                "Water and abrasive bulk particulate grit (`{thickness} inch` layer) penetrated idler labyrinth seals during high-pressure washdowns (`{press} PSI`), causing bearing grease washout and seizure.",
                "Normal fatigue failure and spalling of internal idler ball bearings after exceeding `{years}` hours of continuous operating life under heavy impact loading.",
                "Material spillage (`{debris_amt}`) burying return idlers completely, preventing rotation and causing bearings to overheat (`{temp_rc}\u00b0C`) and lock up.",
                "Severe impact shock loading (`> {percent}` capacity) at transfer chute drop point overloaded standard idler bearings beyond static load rating.",
                "Incorrect bearing tolerance (`{clearance}`) led to inner race spinning on the shaft, causing friction welding and bearing lockup.",
                "Failure of the labyrinth seal (`{clog_pct}` compromised) due to highly acidic/corrosive product (`pH {ph_val}`)."
            ],
            "actions": [
                "Locked out conveyor, removed 6 seized and noisy troughing idler assemblies along carry span, and installed new sealed-for-life CEMA C heavy-duty idler rollers (`{part_num}`).",
                "Replaced 4 seized return idlers (`{part_num}`) and 2 impact bed idlers under transfer point, cleared spilled material (`{debris_amt}`) from under structure, and verified smooth, quiet rotation.",
                "Swapped out 8 worn troughing and return rollers across Section B (`{part_num}`), upgraded loading zone to heavy-duty rubber-disc impact idlers, and aligned brackets.",
                "Performed complete idler walkaround audit, replacing 12 seized or noisy idler rollers (`{part_num}`) across carry and return spans, and cleared material buildup around tail area.",
                "Replaced seized rollers (`{part_num}`), installed deflector shields (`{part_num}`) to prevent washdown water entry, and verified tracking.",
                "Upgraded transfer point to an impact slider bed (`{part_num}`) to eliminate roller bearings in the high-impact zone, adjusted skirtboards."
            ],
            "parts": [
                ["CEMA C Troughing Idler Rollers 35-Degree (Set of 6)", "Return Idler Rollers 4-inch (4-Pack)"],
                ["Heavy-Duty Impact Troughing Idler Assemblies (Set of 2)", "Return Rollers (4-Pack)", "Idler Mounting Brackets"],
                ["Replacement Sealed Idler Rollers (Pack of 8)", "Impact Roller Kit (4-Pack)"],
                ["CEMA D Heavy-Duty Idler Roller Set (10-Pack)", "Return Idler Mounting Clips"],
                ["CEMA E Rollers", "Water Deflector Shields", "Mounting Hardware"],
                ["Impact Slider Bed Assembly", "UHMW Polyethylene Slider Bars", "Skirtboard Rubber"]
            ],
            "downtime": (2.0, 5.0)
        },
        "belt tear": {
            "symptoms": [
                "Longitudinal rip (`{length} ft` length) gouged into top rubber cover of conveyor belt near loading transfer chute.",
                "Belt edge torn and fraying (`{percent}` internal fabric carcass cords exposed and catching on conveyor frame brackets).",
                "Mechanical belt rip detector interlock tripped, stopping conveyor immediately. Inspection revealed {adj} puncture hole (`{length} inch` diameter) through entire belt thickness.",
                "Ops reported top cover rubber delaminating (`{degree}` separation) and severe edge gouging along `{length} ft` of conveyor belt carrying surface.",
                "A flap of rubber (`{thickness} inch` thick) peeled back on the belt surface, catching on the primary cleaner (`{hz}` impacts/min).",
                "Belt splice pulling apart (`{gap} inch` gap). Fasteners tearing through the belt carcass (`{percent}` failure)."
            ],
            "root_causes": [
                "Sharp piece of tramp metal (`{part_num}`) or structural steel bracket broke off and wedged between skirt board and belt surface at loading chute, gouging belt during transit.",
                "Severe impact from oversized frozen boulders (`> {thickness} inch` diameter) dropped from `{length} ft` height at transfer point exceeded belt carcass puncture resistance.",
                "Mechanical fastener/lacing splice pulled apart (`{percent}` tension) and caught on fixed belt scraper blade, ripping belt edge open.",
                "Skirt board sealing rubber improperly adjusted (`steel backing clamp dropped down {clearance} gap`), cutting into moving belt cover like a chisel.",
                "Belt slipped off pulley due to misalignment and caught on a rigid structural support (`{vibe}` stress), tearing the edge.",
                "Chemical degradation (`pH {ph_val}`) softened the top cover, allowing normal material impact to tear the rubber (`{clog_pct}` degradation)."
            ],
            "actions": [
                "Locked out unit, trimmed frayed belt edges, repaired 4-foot longitudinal top cover gouge using cold-cure urethane repair compound (`{part_num}`) and rubber repair strips, and readjusted skirt board clamps.",
                "Cut out damaged 10-foot section of conveyor belt, installed new belt insert section (`{part_num}`) using heavy-duty mechanical Flexco plate fasteners, and checked skirt board clearance (`{clearance}`).",
                "Performed hot vulcanized splice repair (`{temp}\u00b0C`) on torn belt section, removed jammed tramp metal (`{debris_amt}`) from transfer chute, and installed new heavy-duty urethane skirt board sealing strips.",
                "Repaired puncture and edge tear using cold vulcanizing patch kit (`{part_num}`), ground smooth, replaced damaged belt cleaner blade, and verified `{clearance}` skirt board clearance.",
                "Pulled `{length} ft` of new belt, performed a hot vulcanized splice (`{temp}\u00b0C`), adjusted primary and secondary scrapers, and ran belt unloaded.",
                "Stitched longitudinal tear (`{length} ft`) with rip repair fasteners (`{part_num}`), replaced worn skirt rubber (`{part_num}`), and recalibrated rip detector."
            ],
            "parts": [
                ["Cold-Cure Urethane Belt Repair Compound Kit (2 Packs)", "Heavy-Duty Rubber Patch Strips", "Urethane Skirt Board Sealing Rubber (20ft)"],
                ["Conveyor Belt Replacement Section (3-ply, 12ft)", "Flexco Bolt Solid Plate Fasteners (Box of 25)", "Skirt Clamps"],
                ["Hot Vulcanizing Splice Kit & Gum Rubber", "Primary Belt Cleaner Scraper Blade", "Urethane Skirt Strip"],
                ["Belt Repair Cold Vulcanizing Kit", "Flexco Mechanical Fastener Set", "Rubber Skirt Rubber (15ft)"],
                ["Conveyor Belt Roll (100ft)", "Hot Splice Kit", "Primary Cleaner Blade"],
                ["Rip Repair Fasteners (Box of 100)", "Skirtboard Rubber (50ft)", "Fastener Template"]
            ],
            "downtime": (4.5, 9.0)
        },
        "motor overload": {
            "symptoms": [
                "Conveyor drive motor tripped VFD/thermal overload relay (`motor current spiked to {current} Amps vs 32A FLA`). Drive pulley stationary while motor humming.",
                "High torque alarm active on conveyor drive controller. Motor frame temperature `{temp}`\u00b0C (`{degree}` overheating). Conveyor struggling to start under load.",
                "Conveyor stalled completely during heavy surge loading. Fluid coupling thermal fuse plug melted (`{temp}\u00b0C`), discharging coupling oil (`{percent}` pool on floor).",
                "Drive motor drawing continuous `{current}` Amps (`115%` rating). Gearbox output shaft rotating sluggishly with {adj} laboring noise (`{noise}`).",
                "VFD fault code indicating over-current (`{current} A`). Motor smells of burnt varnish (`{ppm}` VOCs).",
                "Conveyor belt slipping on the drive pulley (`{percent}` slip). Motor running at `{hz} Hz` but belt speed is zero."
            ],
            "root_causes": [
                "Conveyor overloaded beyond maximum design capacity (`surge loading from upstream bin discharge exceeding {percent} TPH`).",
                "Severe mechanical binding and increased drag (`{torque}` required) caused by multiple seized idler rollers and caked material dragging against bottom belt return span.",
                "Tail pulley or take-up assembly jammed with packed solid material (`{debris_amt}`), creating immense frictional drag against belt movement.",
                "Faulty or misadjusted motor thermal overload relay setting (`set too low at {percent}% FLA`) or loose phase connection causing phase current unbalance (`{degree}`).",
                "Loss of lagging (`{percent}` missing) on the drive pulley causing slip. The control system ramps up speed (`{hz} Hz`) to compensate, overloading the motor.",
                "Gearbox internal failure (`{thickness} inch` metal shavings in oil) caused immense mechanical drag (`{torque}`)."
            ],
            "actions": [
                "Cleared excess surge material load (`{debris_amt}`) from belt carrying surface, freed up 6 jammed idler rollers under skirt board, reset motor thermal overload relay, and verified normal running draw (`{current} Amps`).",
                "Shoveled out heavy material spillage (`{debris_amt}`) burying tail pulley and return belt span, replaced 4 locked-up return idlers (`{part_num}`), refilled fluid coupling with fresh ISO VG 32 oil (`{lbs_charge} gal`), and installed new thermal fuse plug.",
                "Cleared mechanical jam inside head pulley discharge chute, re-torqued motor terminal connections (`{torque}`), checked gearbox oil level, and verified VFD current stability across full speed range (`{hz} Hz`).",
                "Excavated packed material from tail take-up frame, lubricated take-up slide ways (`{part_num}`), replaced 5 dragging idler rollers, and tested conveyor startup under standard load.",
                "Re-lagged drive pulley (`{part_num}`) with diamond tread rubber (`{thickness} inch` thick), tightened take-up (`{torque}` tension), and verified zero slip with tachometer.",
                "Replaced failed gearbox (`{part_num}`), aligned motor and gearbox using laser tool (`{clearance} tolerance`), and verified motor current (`{current} A`)."
            ],
            "parts": [
                ["Fluid Coupling Thermal Fuse Plug 140\u00b0C", "ISO VG 32 Fluid Coupling Oil (2 Gallons)", "Replacement Return Idlers (4-Pack)"],
                ["Replacement Return Idlers (Set of 6)", "Motor Terminal Lug Kit"],
                ["Thermal Overload Relay Element", "Take-up Slide Lubricant (1 Can)", "Troughing Idler Rollers (4-Pack)"],
                ["Fluid Coupling Fusible Plug", "Return Rollers (5-Pack)", "Gearbox Top-off Oil"],
                ["Ceramic Lagging Strips", "Cold Vulcanizing Adhesive", "Tensioning Bolts"],
                ["Replacement Gearbox Assembly", "Motor Alignment Shims", "Gear Oil (5 Gal)"]
            ],
            "downtime": (2.0, 5.5)
        }
    }
}

# Fallback generic failure modes if an asset type doesn't match the 12 above exactly
GENERIC_FAILURE_MODES = {
    "general wear": {
        "symptoms": [
            "Routine condition check revealed {adj} component wear and {obs} around primary operating interface (`{vibe}` vibration).",
            "Unit showing signs of {degree} mechanical wear (`{degree}` efficiency drop). Ops noted {adj} {noise} sound during run.",
            "Field inspection identified {adj} wear on moving linkages. Operating temperature around `{temp}`\u00b0C.",
            "Gradual performance degradation (`{percent}` loss of output) and {obs} noted by rounds technician.",
            "Visual inspection identified `{thickness} inch` groove worn into the main drive surface (`{noise}` heard).",
            "Preventive maintenance vibration route flagged `{vibe}` in/sec RMS. Wear particles (`{ppm} ppm`) detected in oil analysis."
        ],
        "root_causes": [
            "Normal mechanical friction and surface fatigue over `{hours}` extended continuous operating hours.",
            "Gradual degradation of lubrication film and accumulation of airborne industrial particulates (`{debris_amt}`) over time.",
            "Cyclic operational stress and minor environmental corrosion (`pH {ph_val}`) after multi-year service life.",
            "Routine wear and tear of consumable elastomeric and mechanical contact elements (`{clearance} clearance`).",
            "Abrasive dust ingress (`{thickness} inch` layer) compromised internal seals, causing accelerated component wear.",
            "Lack of proper lubrication (`{torque}` friction) over the last `{time_period}` led to metal-on-metal contact."
        ],
        "actions": [
            "Disassembled worn subassembly, replaced degraded mechanical wearing elements (`{part_num}`), lubricated moving joints (`{part_num}`), and verified operation.",
            "Renewed worn contact parts, tightened mounting hardware (`{torque}`), performed full lubrication service, and tested unit under load.",
            "Replaced worn mechanical components, cleaned operating assembly, calibrated stroke/linkage (`{runout} tolerance`), and restored to service.",
            "Swapped out worn operating parts with new factory spares (`{part_num}`), renewed seals, and checked running signatures (`{vibe}`).",
            "Installed new wear rings (`{part_num}`), flushed old lubricant, applied new synthetic grease (`{lbs_charge}`), and performed test run.",
            "Rebuilt linkage assembly (`{part_num}`), checked clearances (`{clearance}` gap), painted exposed surfaces, and returned to production."
        ],
        "parts": [
            ["Standard Mechanical Wear Kit", "O-Ring and Seal Set", "Synthetic Grease"],
            ["Replacement Linkage Assembly", "Gasket Kit", "Fastener Set"],
            ["Wear Ring & Seal Kit", "General Maintenance Lubricant"],
            ["Preventative Maintenance Overhaul Kit", "Bearing Set", "Lubricant"],
            ["Seals and Bushings Kit", "Cleaning Solvent", "Hardware"],
            ["Linkage Rebuild Kit", "Grease Cartridges (2)"]
        ],
        "downtime": (1.5, 4.5)
    },
    "sensor malfunction": {
        "symptoms": [
            "Local panel display reading erratic/unstable process values (`reading fluctuating between {temp}\u00b0C and 0\u00b0C`). False interlock trip occurred.",
            "Control system reporting loss of sensor signal (`4-20mA loop current reading {current}mA`). Unit locked out on sensor diagnostic alarm.",
            "Process transmitter reading `{press} PSI` offset from local calibrated mechanical gauge. Controller hunting wildly.",
            "Sensor calibration fault active on PLC interface. Tech observed {adj} corrosion around transmitter field junction box (`{degree}` moisture).",
            "SCADA shows frozen value (`{percent}%`) despite actual process changes. Diagnostic LED flashing `{hz} Hz`.",
            "Signal drops out intermittently (`{vibe}` vibration environment). Wiring check shows `{mg_ohm}` insulation resistance on signal cable."
        ],
        "root_causes": [
            "Moisture and condensation ingress inside sensor field housing caused internal short circuit across transmitter electronic circuitry (`{volts}` spike).",
            "Vibration-induced fatigue breakage (`{hz} Hz` resonance) of sensor internal lead wiring at terminal block inside junction box.",
            "Normal sensor sensing element calibration drift exceeding +/- {percent}% error tolerance after `{years}` years of process exposure.",
            "Corrosion on multi-pin cable connector caused by exposure to ambient washdown chemicals (`pH {ph_val}`) and high humidity.",
            "Physical impact (`{torque}` force) from passing equipment bent the sensor probe (`{runout} inch` deflection).",
            "Electromagnetic interference (EMI) from nearby VFD drive cable (`{amps} Amps`) induced false signal voltage on sensor loop."
        ],
        "actions": [
            "Replaced defective field sensor transmitter (`{part_num}`), renewed waterproof wiring gland and terminal connectors, and calibrated zero/span via HART communicator.",
            "Repaired broken lead wiring inside junction box, installed new moisture-sealed transmitter probe (`{part_num}`), and verified PLC loop reading.",
            "Swapped out faulty sensor element, cleaned cable connector pins with contact cleaner (`{part_num}`), applied dielectric grease, and cleared alarm.",
            "Installed new calibrated process transmitter (`{part_num}`), renewed conduit weather seal, and performed 3-point loop calibration check.",
            "Replaced bent sensor probe (`{part_num}`), installed physical guard bracket (`{part_num}`), and verified readings across operating range.",
            "Re-routed sensor signal cable (`{length} ft`) away from VFD power lines, installed shielded twisted pair wire (`{part_num}`), and grounded shield at PLC."
        ],
        "parts": [
            ["Replacement Process Transmitter Probe", "Waterproof Cable Gland", "Terminal Block"],
            ["Calibrated Sensor Assembly", "Electronic Contact Cleaner", "Dielectric Grease"],
            ["Field Sensor Replacement Unit", "Conduit Sealing Fitting"],
            ["4-20mA Sensor Transmitter", "HART Communication Patch Cable"],
            ["Sensor Probe Kit", "Protective Bracket", "Mounting Hardware"],
            ["Shielded Twisted Pair Cable (50ft)", "Grounding Lugs", "Cable Ties"]
        ],
        "downtime": (0.5, 2.5)
    },
    "overheating": {
        "symptoms": [
            "Unit exterior casing running hot (`{temp}`\u00b0C measured via infrared thermometer). Thermal warning indicator active on local panel.",
            "High temperature alarm tripped unit offline after `{hours}` hours of operation. Cooling airflow feels {adj} weak across ventilation slots.",
            "Ops reported heat waves and {adj} smell of hot metal near unit enclosure (`{degree}` temperature elevation).",
            "Surface temperature reached `{temp}\u00b0C` (`normal < 75\u00b0C`). Current draw normal (`{current}` Amps) but {adj} heat buildup present.",
            "Thermal overload relay tripped (`{current} A`). Enclosure surface measures `{temp_rc}\u00b0C`.",
            "Infrared scan showed `{temp}\u00b0C` hot spot at the bearing housing. Lubricant smells burnt (`{ppm}` fumes)."
        ],
        "root_causes": [
            "External cooling slots and heat sink surfaces heavily blocked with industrial dust (`{thickness} inch`) and lint, preventing adequate convective heat dissipation.",
            "Internal cooling fan motor failure or broken fan blade reduced airflow across operating components by `> {percent}%`.",
            "Operating unit continuously at peak maximum load during high summer ambient temperatures (`> {temp}\u00b0C`).",
            "Partial restriction (`{clog_pct}` blocked) in auxiliary cooling supply line caused elevated operating equilibrium temperatures.",
            "Loss of lubricant (`{lbs_charge}` leaked) caused severe internal friction (`{torque}` drag) and rapid heat generation.",
            "Degraded thermal compound (`{thickness} inch` gap) between internal components and the heat sink compromised heat transfer."
        ],
        "actions": [
            "De-energized unit, thoroughly vacuumed and compressed-air cleaned (`{press} PSI`) cooling slots and internal heat sink surfaces, and verified temperature drop (`{temp}\u00b0C`).",
            "Replaced defective internal cooling fan assembly (`{part_num}`), washed exterior cooling fins with degreaser (`{part_num}`), and verified adequate ventilation.",
            "Cleaned blocked ventilation channels, adjusted enclosure airflow louvers, and verified operating temperature stabilized below `{temp}\u00b0C` under full load.",
            "Flushed auxiliary cooling loop (`{part_num}` chemical), cleaned fan shroud intake grid, and replaced degraded cooling fan blade.",
            "Topped off unit with fresh synthetic lubricant (`{lbs_charge}`), replaced leaking shaft seal (`{part_num}`), and monitored temperature during load test.",
            "Disassembled heat sink, cleaned old compound, applied high-conductivity thermal paste (`{part_num}`), and re-torqued mounting bolts (`{torque}`)."
        ],
        "parts": [
            ["Replacement Cooling Fan Assembly", "Degreaser Solvent (1 Can)"],
            ["Enclosure Cooling Fan 120V", "Filter Media Pad"],
            ["Cooling Fan Shroud & Blade Kit"],
            ["Auxiliary Cooling Line Strainer", "Flushing Chemical", "O-rings"],
            ["Synthetic Lubricant (1 Gal)", "Shaft Seal Kit", "Cleaning Rags"],
            ["Thermal Paste Syringe", "Heat Sink Hardware", "Isopropyl Alcohol"]
        ],
        "downtime": (1.5, 4.0)
    },
    "loose fittings": {
        "symptoms": [
            "Noticed {adj} vibration (`{vibe}` in/sec RMS) and {obs} originating from exterior mounting hardware and connecting pipe/conduit fittings.",
            "Minor fluid weepage and {adj} rattling (`{noise}`) observed at structural and pipe connections (`{degree}` loose play).",
            "Routine walkaround inspection identified loose hold-down bolts and bracket fittings (`{clearance} inch` movement under operating vibration).",
            "Ops flagged {adj} clattering sound (`{noise}`) during unit startup. Inspection showed 3 mounting fasteners backed out significantly.",
            "Visual check revealed `{percent}%` of base plate bolts are loose. Gasket material (`{part_num}`) extruded from joint.",
            "Piping connection weeping fluid (`{gpm} gpm`). Resonance (`{hz} Hz`) is visible on the attached conduit."
        ],
        "root_causes": [
            "Continuous operational vibration (`{vibe_rc}`) over `{hours}` extended runtime caused un-locking and gradual backing out of mechanical threaded fasteners.",
            "Improper torque application during previous maintenance overhauls (`fasteners not tightened to specified {torque} torque values or missing lock washers`).",
            "Thermal expansion and contraction cycles (`{temp}\u00b0C` swings) across dissimilar materials caused clamping force relaxation on bolted connections.",
            "Normal settling of mounting base pads and vibration (`{vibe}` in/sec) transmitted from adjacent heavy rotating machinery.",
            "Yielding of Grade 5 bolts (`{torque}` stress) due to unexpected pressure spikes (`{press} PSI`) in the process line.",
            "Deterioration of rubber isolation mounts (`{percent}` degraded) allowed excessive movement, loosening rigid connections."
        ],
        "actions": [
            "De-energized unit, inspected all structural and pipe fittings, applied medium-strength threadlocker (`{part_num}`), and torqued all hardware to engineering specifications (`{torque}`) using Belleville washers.",
            "Replaced worn/missing fasteners (`{part_num}`), installed split lock washers, re-torqued baseplate hold-down bolts (`{torque}`), and verified zero vibration play (`{vibe}`).",
            "Tightened loose conduit and piping union fittings, replaced damaged gaskets (`{part_num}`), re-torqued mounting brackets, and checked alignment.",
            "Performed complete structural torquing check across unit, installed vibration-damping Belleville spring washers (`{part_num}`), and renewed hardware.",
            "Upgraded fasteners to Grade 8 (`{part_num}`), replaced extruded flange gasket, and torqued in a star pattern to `{torque}`.",
            "Replaced degraded rubber isolation mounts (`{part_num}`), realigned piping connections, installed flexible braided hose sections, and tested."
        ],
        "parts": [
            ["Grade 8 Fastener & Lock Washer Kit", "Loctite 242 Medium Strength Threadlocker (1 Bottle)"],
            ["Belleville Spring Washer Pack (20-Pack)", "Stainless Steel Bolt Set"],
            ["Replacement Union Fittings & Gaskets", "Structural Fastener Assortment Kit"],
            ["Vibration Isolation Mounts (4-Pack)", "Grade 8 Hardware Kit", "Torque Seal"],
            ["Grade 8 Flange Bolts", "Spiral Wound Flange Gasket", "Anti-Seize Compound"],
            ["Rubber Isolation Mounts (Set of 4)", "Flexible Braided Hose", "Pipe Fittings"]
        ],
        "downtime": (1.0, 2.5)
    }
}

# Synonyms and numerical/measurement placeholders for randomized template substitution
SYNONYMS = {
    "{adj}": ["severe", "slight", "intermittent", "excessive", "abnormal", "high", "unusual", "gradual", "heavy", "distinct", "persistent", "significant", "localized", "accelerated", "noticeable"],
    "{obs}": ["vibration", "leaking fluid", "pressure drop", "temperature spike", "rattling sound", "smoke/fumes", "erratic amp draw", "flow reduction", "thermal buildup", "acoustic noise"],
    "{noise}": ["grinding", "high-pitched squealing", "thumping", "metallic clattering", "buzzing/humming", "cavitation crackling", "hissing", "rumbling", "screeching", "clicking", "chattering", "growling"],
    "{degree}": ["moderate", "severe", "slight", "noticeable", "extreme", "marked", "drastic", "minor", "sharp", "concerning", "progressive"],
    "{temp}": [lambda: str(random.randint(75, 118)), lambda: str(random.randint(82, 125)), lambda: str(random.randint(90, 135))],
    "{temp_rc}": [lambda: str(random.randint(85, 145)), lambda: str(random.randint(95, 160)), lambda: str(random.randint(110, 175))],
    "{press}": [lambda: str(random.randint(12, 48)), lambda: str(random.randint(15, 65)), lambda: str(random.randint(20, 85))],
    "{press_drop}": [lambda: f"{random.uniform(3.5, 12.0):.1f}", lambda: f"{random.uniform(8.0, 18.5):.1f}", lambda: f"{random.uniform(14.0, 26.0):.1f}"],
    "{vibe}": [lambda: f"{random.uniform(0.18, 0.55):.2f}", lambda: f"{random.uniform(0.22, 0.65):.2f}", lambda: f"{random.uniform(0.35, 0.75):.2f}"],
    "{vibe_rc}": [lambda: f"{random.uniform(0.25, 0.60):.2f}", lambda: f"{random.uniform(0.38, 0.85):.2f}", lambda: f"{random.uniform(0.45, 1.10):.2f}"],
    "{current}": [lambda: str(random.randint(38, 185)), lambda: str(random.randint(45, 160)), lambda: str(random.randint(65, 240))],
    "{amps}": [lambda: str(random.randint(25, 85)), lambda: str(random.randint(90, 210)), lambda: str(random.randint(115, 320))],
    "{volts}": [lambda: f"{random.choice([460, 480, 230, 4160])}V", lambda: f"{random.choice([460, 480])}V +/- {random.randint(1, 4)}%"],
    "{gap}": [lambda: f"{random.uniform(0.006, 0.018):.3f}", lambda: f"{random.uniform(0.010, 0.025):.3f}", lambda: f"{random.uniform(0.015, 0.032):.3f}"],
    "{runout}": [lambda: f"{random.uniform(0.003, 0.009):.3f}", lambda: f"{random.uniform(0.005, 0.014):.3f}"],
    "{clearance}": [lambda: f"{random.uniform(0.004, 0.012):.3f}", lambda: f"{random.uniform(0.008, 0.020):.3f}"],
    "{thickness}": [lambda: f"{random.uniform(0.04, 0.16):.2f}", lambda: f"{random.uniform(0.10, 0.28):.2f}"],
    "{hours}": [lambda: str(random.randint(8000, 16000)), lambda: str(random.randint(14000, 28000)), lambda: str(random.randint(25000, 45000))],
    "{time_period}": [lambda: f"{random.randint(4, 11)} months", lambda: f"{random.randint(1, 4)} years", lambda: f"{random.randint(12, 36)} months"],
    "{clog_pct}": [lambda: f"{random.randint(25, 55)}%", lambda: f"{random.randint(50, 85)}%", lambda: f"{random.randint(65, 92)}%"],
    "{percent}": [lambda: f"{random.randint(12, 35)}%", lambda: f"{random.randint(28, 62)}%", lambda: f"{random.randint(45, 85)}%"],
    "{torque}": [lambda: f"{random.randint(35, 85)} ft-lbs", lambda: f"{random.randint(90, 165)} ft-lbs", lambda: f"{random.randint(220, 380)} in-lbs"],
    "{mesh}": [lambda: f"{random.choice([40, 60, 80, 100])}-mesh"],
    "{microns}": [lambda: str(random.choice([250, 300, 400, 500])), lambda: str(random.choice([150, 200, 350]))],
    "{ppm}": [lambda: f"{random.randint(15, 45)} ppm", lambda: f"{random.randint(60, 180)} ppm", lambda: f"{random.randint(220, 480)} ppm"],
    "{tan_delta}": [lambda: f"{random.uniform(0.8, 1.9):.1f}%", lambda: f"{random.uniform(1.6, 3.4):.1f}%"],
    "{mg_ohm}": [lambda: f"{random.uniform(0.02, 0.25):.2f} Mega-ohms", lambda: f"{random.uniform(0.15, 0.65):.2f} Mega-ohms"],
    "{debris_amt}": [lambda: f"{random.uniform(1.2, 4.5):.1f} lbs", lambda: f"{random.uniform(3.0, 8.5):.1f} lbs"],
    "{npsh_margin}": [lambda: f"{random.uniform(2.5, 5.5):.1f} feet", lambda: f"{random.uniform(4.0, 9.2):.1f} feet"],
    "{gpm}": [lambda: str(random.randint(180, 450)), lambda: str(random.randint(350, 850))],
    "{hz}": [lambda: f"{random.randint(18, 28)} Hz", lambda: f"{random.randint(42, 58)} Hz"],
    "{part_num}": [lambda: f"P/N {random.randint(1000, 9999)}-{random.choice(['A', 'B', 'C', 'X', 'REV2'])}", lambda: f"Spec-{random.randint(100, 999)}"],
    "{lbs_charge}": [lambda: f"{random.randint(8, 28)} lbs", lambda: f"{random.randint(35, 95)} lbs", lambda: f"{random.randint(110, 180)} lbs"],
    "{ph_val}": [lambda: f"{random.uniform(8.4, 9.6):.1f}", lambda: f"{random.uniform(5.2, 6.4):.1f}"]
}

def generate_log_text(template, rel_id=None, append_rel=False):
    """
    Substitutes placeholders with randomized synonyms and numerical values across all templates.
    Optionally appends a relationship phrase if append_rel is True and rel_id is present.
    """
    text = template
    for key, values in SYNONYMS.items():
        while key in text:
            choice = random.choice(values)
            val_str = choice() if callable(choice) else choice
            text = text.replace(key, val_str, 1)
            
    if "{rel_id}" in text:
        text = text.replace("{rel_id}", str(rel_id) if rel_id else "adjacent connected unit")
            
    if append_rel and rel_id and random.random() < 0.95:
        phrase = random.choice(RELATIONSHIP_PHRASES).format(rel_id=rel_id)
        text = text.rstrip(".") + "." + phrase
    return text

def generate_symptom_text(template, rel_id=None):
    """
    Backward-compatible wrapper for generating symptom text with relationship phrases.
    """
    return generate_log_text(template, rel_id=rel_id, append_rel=True)

def get_equipment_kb(asset_type):
    """
    Performs exact match or case-insensitive/fuzzy match against FAILURE_MODE_KB.
    Falls back to GENERIC_FAILURE_MODES if no close match is found.
    """
    if asset_type in FAILURE_MODE_KB:
        return FAILURE_MODE_KB[asset_type]
    
    # Case insensitive check
    for key, kb in FAILURE_MODE_KB.items():
        if key.lower() == str(asset_type).lower():
            return kb
        if str(asset_type).lower() in key.lower() or key.lower() in str(asset_type).lower():
            return kb
            
    return GENERIC_FAILURE_MODES

def generate_random_date():
    """
    Generates a random YYYY-MM-DD date clustered across Jan 2023 - Dec 2024.
    """
    chosen_ym = random.choices(MONTHS_2023_2024, weights=MONTH_WEIGHTS, k=1)[0]
    year, month = map(int, chosen_ym.split("-"))
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:
        max_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    day = random.randint(1, max_day)
    return f"{year}-{month:02d}-{day:02d}"

def main():
    # Ensure data directory and output directory exist
    output_dir = os.path.join("data", "synthetic_logs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Locate asset_registry.xlsx (check data/ first, then fallback to current directory)
    registry_path = os.path.join("data", "asset_registry.xlsx")
    if not os.path.exists(registry_path):
        if os.path.exists("asset_registry.xlsx"):
            registry_path = "asset_registry.xlsx"
        else:
            raise FileNotFoundError("Could not find asset_registry.xlsx in data/ or current directory.")
            
    print(f"Reading asset registry from: {registry_path}")
    df_registry = pd.read_excel(registry_path)
    
    # Build parent-child relationships map
    # For every asset, gather related asset IDs (parents or children)
    asset_relations = {row['asset_id']: [] for _, row in df_registry.iterrows()}
    for _, row in df_registry.iterrows():
        aid = row['asset_id']
        pid = row['parent_asset_id']
        if pd.notna(pid) and str(pid).strip() != "" and str(pid).strip() != "nan":
            pid_str = str(pid).strip()
            if pid_str in asset_relations:
                asset_relations[aid].append(pid_str)
                asset_relations[pid_str].append(aid)
                
    # Deduplicate relationship lists
    for aid in asset_relations:
        asset_relations[aid] = list(set(asset_relations[aid]))
        
    all_work_orders = []
    
    # Generate 15-20 work orders per individual asset_id
    for _, row in df_registry.iterrows():
        asset_id = row['asset_id']
        asset_type = row['asset_type']
        
        n_orders = random.randint(15, 20)
        kb = get_equipment_kb(asset_type)
        failure_modes_list = list(kb.keys())
        
        rel_ids = asset_relations.get(asset_id, [])
        
        for _ in range(n_orders):
            date_str = generate_random_date()
            tech = random.choice(TECH_POOL)
            failure_mode = random.choice(failure_modes_list)
            
            fm_data = kb[failure_mode]
            
            # Determine if related_asset_ids should be populated (~25% chance if related assets exist)
            rel_asset_id_val = ""
            selected_rel_id = None
            if rel_ids and random.random() < 0.26:
                selected_rel_id = random.choice(rel_ids)
                rel_asset_id_val = selected_rel_id
                
            # Pick templates and substitute
            symptom_template = random.choice(fm_data["symptoms"])
            symptom_desc = generate_symptom_text(symptom_template, rel_id=selected_rel_id)
            
            # Coupled index selection for root_cause, action_taken, and parts
            idx = random.randrange(len(fm_data["root_causes"]))
            
            rc_template = fm_data["root_causes"][idx]
            root_cause = generate_log_text(rc_template, rel_id=selected_rel_id)
            
            action_template = fm_data["actions"][idx]
            action_taken = generate_log_text(action_template, rel_id=selected_rel_id)
            
            parts_choice = fm_data["parts"][idx]
            parts_used = ", ".join(parts_choice) if isinstance(parts_choice, list) else str(parts_choice)
            
            min_dt, max_dt = fm_data["downtime"]
            # Add slight random perturbation inside bounds and round to 1 decimal place
            downtime = round(random.uniform(min_dt, max_dt), 1)
            
            all_work_orders.append({
                "work_order_id": "", # Will assign sequentially after chronological sorting
                "asset_id": asset_id,
                "asset_type": asset_type,
                "date": date_str,
                "technician_name": tech,
                "failure_mode": failure_mode,
                "symptom_description": symptom_desc,
                "root_cause": root_cause,
                "action_taken": action_taken,
                "parts_used": parts_used,
                "downtime_hours": downtime,
                "related_asset_ids": rel_asset_id_val
            })
            
    # Convert to DataFrame
    df_logs = pd.DataFrame(all_work_orders)
    
    # Sort chronologically across the entire dataset so dates and WO numbers align naturally
    df_logs.sort_values(by=["date", "asset_id"], inplace=True)
    df_logs.reset_index(drop=True, inplace=True)
    
    # Assign unique work_order_id: WO-0001, WO-0002, ...
    df_logs["work_order_id"] = [f"WO-{i+1:04d}" for i in range(len(df_logs))]
    
    # Reorder columns explicitly to match SCHEMA exact requirement
    schema_cols = [
        "work_order_id", "asset_id", "asset_type", "date", "technician_name",
        "failure_mode", "symptom_description", "root_cause", "action_taken",
        "parts_used", "downtime_hours", "related_asset_ids"
    ]
    df_logs = df_logs[schema_cols]
    
    # Save combined CSV using explicit utf-8 encoding
    combined_csv_path = os.path.join(output_dir, "all_work_orders.csv")
    try:
        df_logs.to_csv(combined_csv_path, index=False, encoding="utf-8")
        print(f"\nSuccessfully saved combined work orders CSV to: {combined_csv_path}")
    except PermissionError:
        print(f"\n[ERROR] PermissionError: Could not save to {combined_csv_path}. Is the file open in Excel?")
        return
    
    # Save one CSV per asset_id
    rows_per_asset = {}
    try:
        for aid, group in df_logs.groupby("asset_id"):
            # Sort each asset's CSV chronologically as well
            group_sorted = group.sort_values(by="date")
            asset_csv_path = os.path.join(output_dir, f"{aid}_logs.csv")
            group_sorted.to_csv(asset_csv_path, index=False, encoding="utf-8")
            rows_per_asset[aid] = len(group_sorted)
    except PermissionError as e:
        print(f"\n[ERROR] PermissionError saving individual asset CSVs: {e}. Are they open in Excel?")
        return
        
    # Print summary
    print("\n" + "="*60)
    print("SYNTHETIC MAINTENANCE WORK ORDER GENERATION SUMMARY")
    print("="*60)
    print(f"Total Work Orders Generated across entire dataset: {len(df_logs)}")
    print(f"Total distinct Assets processed: {len(rows_per_asset)}")
    print("-" * 60)
    print(f"{'Asset ID':<15} | {'Asset Type':<25} | {'Rows Generated':<15}")
    print("-" * 60)
    
    for _, row in df_registry.iterrows():
        aid = row['asset_id']
        atype = row['asset_type']
        count = rows_per_asset.get(aid, 0)
        print(f"{aid:<15} | {atype:<25} | {count:<15}")
    print("="*60 + "\n")
    
    # Validation report logic
    print("VALIDATION REPORT (Duplicate Counts)")
    print("-" * 60)
    total_rc = len(df_logs)
    unique_rc = df_logs["root_cause"].nunique()
    rc_dupes = total_rc - unique_rc
    
    total_ac = len(df_logs)
    unique_ac = df_logs["action_taken"].nunique()
    ac_dupes = total_ac - unique_ac
    
    print(f"Total Rows: {total_rc}")
    print(f"Duplicate root_cause instances: {rc_dupes}")
    print(f"Duplicate action_taken instances: {ac_dupes}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
