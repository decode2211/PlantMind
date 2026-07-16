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
                "Noticeable {adj} crackling and popping sounds heard from pump suction casing. Discharge pressure is {degree} erratic under normal load.",
                "Ops reported {adj} gravel-like {noise} inside pump housing during peak flow. Suction gauge fluctuating +/- {press} PSI.",
                "Found pump exhibiting {degree} casing vibration (`{vibe}` in/sec RMS) and {obs} near inlet manifold. Possible flow restriction or NPSH margin drop.",
                "Pump making loud {noise} right after morning startup. Discharge flow dropping intermittently with high casing vibration."
            ],
            "root_causes": [
                "Insufficient Net Positive Suction Head Available (NPSHA) caused by partially clogged suction basket strainer.",
                "Air entrainment in suction pipe due to degraded suction valve stem packing and low feed tank level.",
                "Operating pump excessively far out beyond its Best Efficiency Point (BEP) during high production demand.",
                "Suction pipe restriction from sediment accumulation causing localized vapor bubble formation and collapse."
            ],
            "actions": [
                "Cleaned suction inlet basket strainer and throttled discharge valve to restore adequate NPSH margin.",
                "Replaced suction valve stem packing, purged air from suction manifold, and verified tank minimum level interlock settings.",
                "Adjusted VFD speed profile to keep pump operating within optimal BEP parameters.",
                "Flushed suction piping line with high-pressure water and inspected impeller eye for early pitting signs."
            ],
            "parts": [
                ["Suction Strainer Mesh Basket", "Flange Gasket Kit"],
                ["Suction Valve Packing Rings", "O-Ring Kit"],
                ["None"],
                ["Flange Gasket 3-inch", "Stainless Steel Bolt Set"]
            ],
            "downtime": (2.0, 5.5)
        },
        "seal leakage": {
            "symptoms": [
                "Found {adj} fluid dripping constantly from pump stuffing box area. Pool of process fluid accumulating on baseplate.",
                "Ops flagged {obs} (`{temp}`\u00b0C) near mechanical seal gland during walkaround. Seal flush line appears restricted.",
                "Heavy fluid dripping from lower seal chamber. Tech observed {degree} {obs} and vapor formation around shaft sleeve.",
                "Mechanical seal weeping {adj} volume of fluid onto skid plate. Seal reservoir pressure dropping steadily over 24 hrs."
            ],
            "root_causes": [
                "Mechanical seal faces scored due to abrasive particles in process fluid and inadequate seal flush filtration.",
                "Thermal shock and lack of lubrication caused carbon seal face blistering and O-ring degradation.",
                "Shaft runout exceeding 0.003 inches caused uneven wear on mechanical seal stationary face.",
                "Failure of external seal flush cyclone separator leading to solids accumulation in stuffing box."
            ],
            "actions": [
                "Removed pump casing, replaced cartridge mechanical seal assembly, and flushed seal supply piping.",
                "Replaced mechanical seal and O-rings; cleaned seal flush line orifice and verified cooling flow.",
                "Realigned motor and pump shaft to reduce runout, then installed new single cartridge mechanical seal.",
                "Replaced damaged seal faces and installed upgraded cyclone separator in seal flush loop."
            ],
            "parts": [
                ["Cartridge Mechanical Seal Assembly", "Casing Gasket"],
                ["Mechanical Seal Repair Kit", "Viton O-Ring Set"],
                ["Single Mechanical Seal", "Shaft Sleeve", "Gasket Kit"],
                ["Seal Faces Set", "Cyclone Separator Element"]
            ],
            "downtime": (3.0, 6.5)
        },
        "impeller wear": {
            "symptoms": [
                "Pump unable to maintain rated head (`{press}` PSI drop from curve). Motor amp draw is {degree} lower than baseline.",
                "Gradual degradation in discharge flow (`{degree}` reduction). Casing inspection revealed {adj} internal turbulence and {noise}.",
                "Ops noted pump running smoothly but failing to meet process target gpm. Hydraulic performance curve shift suspected.",
                "Excessive recirculation noise inside casing and {adj} pressure drop across pump discharge flange."
            ],
            "root_causes": [
                "Severe erosive wear on impeller vanes due to entrained abrasive solid particulates over extended runtime.",
                "Cavitation erosion over past 12 months eroded vane tips and widened wear ring clearances.",
                "Chemical corrosion thinned outer shroud of bronze impeller, leading to internal recirculation.",
                "Normal mechanical degradation of wear rings and impeller shroud after 15,000 hours of continuous service."
            ],
            "actions": [
                "Disassembled pump rotating element, installed new 316SS trimmed impeller and casing wear rings.",
                "Replaced eroded impeller assembly, renewed front/rear wear rings, and balanced rotor assembly dynamically.",
                "Upgraded impeller to hardened duplex alloy and set proper impeller-to-casing clearances.",
                "Swapped out worn impeller assembly and renewed shaft locking nut and key."
            ],
            "parts": [
                ["316SS Impeller", "Casing Wear Ring", "Impeller Key"],
                ["Impeller Assembly", "Front and Rear Wear Rings", "Casing Gasket"],
                ["Duplex Stainless Impeller", "Wear Ring Kit"],
                ["Replacement Impeller", "Lock Washer", "Shaft Nut"]
            ],
            "downtime": (5.5, 10.0)
        },
        "bearing failure": {
            "symptoms": [
                "Elevated bearing housing temperature (`{temp}`\u00b0C measured via infrared gun) along with {adj} {noise} sound from thrust end.",
                "High frequency vibration (`{vibe}` in/sec RMS) detected during routine condition monitoring survey on pump outboard bearing.",
                "Loud {noise} and metallic clattering from bearing pedestal. Oil level check showed {adj} discoloration and metal debris.",
                "Bearing housing running extremely hot and vibrating {degree}. Unit shut down immediately by maintenance roundsman."
            ],
            "root_causes": [
                "Lube oil contamination with process fluid/water caused breakdown of oil film and subsequent spalling of bearing races.",
                "Fatigue failure of rolling elements due to prolonged operation with slight angular misalignment.",
                "Lack of lubrication following oil ring hangup inside bearing housing reservoir.",
                "Improper bearing preload and excessive axial thrust load caused premature cage fracture."
            ],
            "actions": [
                "Replaced both inboard and outboard radial/thrust bearings, flushed bearing housing, and added fresh synthetic ISO VG 68 oil.",
                "Pulled bearing frame, pressed on new SKF angular contact bearings, replaced lip seals, and realigned shaft.",
                "Replaced damaged bearing set, polished shaft journals, and installed new constant level oiler assembly.",
                "Replaced thrust bearing housing assembly, renewed oil seals, and verified dynamic balance."
            ],
            "parts": [
                ["SKF Outboard Angular Contact Bearing", "Inboard Roller Bearing", "ISO VG 68 Lube Oil"],
                ["Bearing Kit 6309-C3", "Lip Seal Set", "Shim Pack"],
                ["Thrust Bearing Assembly", "Constant Level Oiler", "Oil Sight Glass"],
                ["Radial Bearing", "Thrust Bearing Set", "Housing Gasket"]
            ],
            "downtime": (6.0, 11.5)
        },
        "misalignment": {
            "symptoms": [
                "1X and 2X RPM vibration peaks (`{vibe}` in/sec RMS) observed across pump and motor coupling. Noticeable {adj} axial vibration.",
                "Coupling insert wearing rapidly (`{degree}` shedding of elastomeric dust). High radial vibration measured on inboard bearing pads.",
                "Elevated temperatures on both motor and pump inboard bearing housings (`{temp}`\u00b0C) with {adj} humming noise.",
                "Unit exhibiting {degree} vibration across coupling guard after recent pipework modification nearby."
            ],
            "root_causes": [
                "Thermal growth differential between pump and motor not compensated for during initial cold alignment.",
                "Pipe strain from improperly supported discharge piping exerting torque forces on pump suction flange.",
                "Soft foot condition under motor baseplate (`0.012` inch gap) causing shifting during anchor bolt torquing.",
                "Foundation settling and normal vibration shifting over time degraded precision laser alignment."
            ],
            "actions": [
                "Performed precision laser alignment between pump and driving motor, bringing angular and parallel offset within 0.002 inches.",
                "Corrected motor soft foot using stainless shims, adjusted piping hangers to relieve pipe strain, and realigned shafts.",
                "Replaced worn elastomeric coupling insert and re-laser aligned pump/motor train to tight tolerance.",
                "Loosened flange bolts to relieve pipe strain, re-torqued baseplate hold-down bolts, and completed full alignment."
            ],
            "parts": [
                ["Elastomeric Coupling Insert", "Precision Stainless Steel Shim Pack"],
                ["Coupling Element", "Shim Kit 2x2"],
                ["Omega Coupling Half and Element"],
                ["None"]
            ],
            "downtime": (2.5, 5.0)
        }
    },
    "Submersible Pump": {
        "motor winding failure": {
            "symptoms": [
                "Submersible pump tripped main circuit breaker upon startup. Megger insulation resistance test showed `< 0.5` Mega-ohms to ground.",
                "Severe short circuit current surge tripped upstream breaker. Tech noted {adj} burnt electrical smell from terminal junction box.",
                "Pump fails to start (`{current}` Amps inrush trip). Phase-to-phase resistance imbalance (`> 15%`) detected at control cabinet.",
                "Continuous tripping of thermal/magnetic overload relays. Field check confirmed dead short between phase B and ground."
            ],
            "root_causes": [
                "Moisture ingress into motor enclosure through degraded cable entry seal caused stator winding insulation breakdown.",
                "Prolonged operation in overheated condition due to low sump liquid level leading to thermal aging of winding varnish.",
                "Voltage surges from utility grid transients degraded turn-to-turn winding insulation.",
                "Stator winding ground fault caused by internal vibration chafing insulation against stator core slots."
            ],
            "actions": [
                "Pulled submersible pump from sump, sent to certified rewind shop for full stator rewinding and vacuum pressure impregnation (VPI).",
                "Replaced complete submersible motor assembly, renewed cable entry seal assembly, and tested megger resistance before dropping into pit.",
                "Replaced stator assembly, baked and dipped windings, and installed new moisture sensing relay in cabinet.",
                "Installed spare submersible motor unit, renewed mechanical seals and power cable gland, and verified rotation."
            ],
            "parts": [
                ["Submersible Stator Rewind Kit", "Upper/Lower Mechanical Seals", "O-Ring Rebuild Set"],
                ["Submersible Motor Assembly", "Cable Entry Seal Kit"],
                ["Replacement Stator Core Assembly", "Moisture Sensor Module"],
                ["Submersible Motor Unit", "Lower Mechanical Seal Assembly"]
            ],
            "downtime": (8.0, 12.0)
        },
        "seal leakage": {
            "symptoms": [
                "Moisture sensor in pump oil chamber triggered high humidity/water interlock alarm on main control panel.",
                "Routine inspection of oil chamber sampling port revealed milky, emulsified oil (`{degree}` water contamination).",
                "Submersible pump seal chamber leak detector alarm active. Small {obs} noticed during pull test.",
                "High water content in barrier oil reservoir. No external leak visible yet but lower mechanical seal compromised."
            ],
            "root_causes": [
                "Lower mechanical seal face scoring caused by solid grit and abrasive slurry passing through pump volute.",
                "Thermal expansion cycles degraded elastomeric bellows of lower mechanical seal after 3 years of submerged duty.",
                "Improper tension on seal spring during previous overhaul allowed fluid separation across stationary face.",
                "Corrosion of lower seal housing lip due to aggressive wastewater chemistry."
            ],
            "actions": [
                "Pulled pump, drained emulsified oil, replaced both upper and lower tandem mechanical seals, and refilled dielectric oil.",
                "Disassembled lower end, renewed double mechanical seal assembly and O-rings, and pressure tested oil chamber to 15 PSI.",
                "Replaced lower silicon carbide seal faces and upper lip seal; flushed and refilled barrier fluid reservoir.",
                "Renewed tandem mechanical seals, replaced corroded seal retainer ring, and verified zero drop on 30-minute pressure decay test."
            ],
            "parts": [
                ["Tandem Mechanical Seal Kit", "Dielectric Barrier Oil (2 Gal)", "Viton O-Ring Pack"],
                ["Double Mechanical Seal Assembly", "Seal Chamber Gasket Set"],
                ["Silicon Carbide Lower Seal Set", "Upper Carbon Seal", "Dielectric Oil"],
                ["Seal Repair Kit", "Retainer Ring", "O-Ring Set"]
            ],
            "downtime": (4.0, 7.5)
        },
        "clogging": {
            "symptoms": [
                "Sump pit level rising above high-water alarm setpoint despite pump running continuously at `{current}` Amps.",
                "Pump motor current drop (`{degree}` below normal load amps) accompanied by zero flow discharge and {adj} casing vibration.",
                "Loud {noise} and churning sound coming from submerged pump volute. Discharge check valve showing zero pressure.",
                "Ops reported pump running hot with severely restricted output flow. Suspect ragball or solid debris blockage in volute."
            ],
            "root_causes": [
                "Accumulation of fibrous wipes, rags, and solid debris wrapped tightly around multi-vane impeller leading edges.",
                "Sump bottom sludge and heavy silt ingestion plugged volute discharge channel during heavy storm inflow.",
                "Large solid debris wedged between impeller shroud and volute tongue, locking impeller partially.",
                "Inlet suction screen completely blinded off by floating debris and grease buildup in wet well."
            ],
            "actions": [
                "Pulled pump out of wet well, manually cleared fibrous ragball from impeller vanes, and flushed volute chamber with high-pressure hose.",
                "Extracted pump unit, dislodged solid wooden debris wedged inside volute, and verified free manual rotation of impeller.",
                "Cleared clogged suction screen and impeller passage; hydro-blasted wet well sump walls to remove grease accumulation.",
                "Disassembled volute casing, removed heavy silt/rag blockage, and checked impeller wear ring clearances."
            ],
            "parts": [
                ["Suction Screen Fasteners", "Volute O-Ring"],
                ["None"],
                ["Volute Gasket Set"],
                ["Wear Ring Set", "Casing O-Ring"]
            ],
            "downtime": (1.5, 4.0)
        },
        "cable damage": {
            "symptoms": [
                "Intermittent phase loss alarms and grounding trips on pump feed. Cable outer sheath shows {adj} abrasion near wet well lip.",
                "Submersible power cable jacket split near guide rail clamp. Insulation resistance between conductors fluctuating severely.",
                "Control panel showing earth fault. Inspection of power cable drop revealed {adj} cuts and exposed copper armor.",
                "Pump lost power suddenly (`0` Amps). Cable strain relief failed allowing cable to rub against concrete pit wall."
            ],
            "root_causes": [
                "Continuous vibration and turbulence caused power cable to chafe against concrete edge of sump pit access hatch.",
                "Improper clamping of cable strain relief allowed cable weight to pull on terminal entry gland, tearing outer polyurethane jacket.",
                "Accidental pinch damage during previous pump lifting and lowering operation along guide rails.",
                "Chemical degradation and hardening of outer cable jacket from long-term immersion in industrial effluent."
            ],
            "actions": [
                "Replaced damaged 50-foot section of submersible power cable, installed new heavy-duty cable entry gland, and secured strain relief.",
                "Spliced and potted cable using marine-grade resin splice kit, installed protective stainless abrasion sleeve over guide rail area.",
                "Installed new multi-conductor submersible power drop cable, renewed terminal gland assembly, and tested continuity.",
                "Renewed power cable assembly, installed rubber guide rail chafing protectors, and re-torqued strain relief clamp."
            ],
            "parts": [
                ["50ft Submersible Power Cable 4/0 AWG", "Cable Entry Gland Kit", "Strain Relief Grip"],
                ["Marine Resin Cable Splice Kit", "Stainless Abrasion Sleeve"],
                ["Submersible Power Drop Cable Assembly", "Terminal Gland O-Ring Set"],
                ["Power Cable Assembly", "Rubber Chafing Guard", "Gland Kit"]
            ],
            "downtime": (3.5, 6.5)
        }
    },
    "Induction Motor": {
        "bearing wear": {
            "symptoms": [
                "Motor drive-end bearing housing temperature reaching `{temp}`\u00b0C. High frequency acoustic vibration (`{vibe}` in/sec RMS) detected.",
                "Loud {adj} whining and {noise} sound emanating from motor non-drive end bearing during operation.",
                "Vibration analysis indicates severe inner race defect frequencies (BPFI) on motor drive-end bearing with `{degree}` harmonics.",
                "Tech noted {adj} grease discoloration leaking from bearing grease relief tube and metallic clattering."
            ],
            "root_causes": [
                "Grease dry-out and thermal degradation due to operating in elevated ambient temperature environment (`> 40\u00b0C`).",
                "Over-greasing by maintenance personnel caused excessive churning heat and blown grease retainer seals.",
                "Shaft voltage discharge (EDM currents) from VFD drive caused fluting and micro-pitting on bearing raceways.",
                "Normal fatigue wear of deep groove ball bearings after exceeding 40,000 hours of continuous operating life."
            ],
            "actions": [
                "De-coupled motor, removed bearing end shields, replaced both DE and NDE bearings with C3 clearance ball bearings, and packed with Polyrex EM.",
                "Replaced drive-end and non-drive-end bearings, installed shaft grounding ring to mitigate VFD bearing currents, and realigned unit.",
                "Replaced worn bearing set, cleaned grease cavities, installed new grease relief valves, and balanced rotor assembly.",
                "Disassembled motor, installed insulated NDE bearing and standard DE bearing, and verified smooth running signatures."
            ],
            "parts": [
                ["SKF 6312-C3 Drive-End Bearing", "SKF 6310-C3 NDE Bearing", "Polyrex EM Grease (1 Tube)"],
                ["DE Ball Bearing", "NDE Insulated Bearing", "AEGIS Shaft Grounding Ring Kit"],
                ["Bearing Kit (DE & NDE)", "Lip Seals", "Bearing Housing Gasket"],
                ["SKF Deep Groove Ball Bearing Set", "Grease Valve Kit"]
            ],
            "downtime": (4.0, 7.5)
        },
        "winding insulation failure": {
            "symptoms": [
                "Motor tripped main overload and instantaneous ground fault protection. Stator shows `{temp}`\u00b0C localized hotspot on IR scan.",
                "Strong {adj} smell of burnt varnish from motor cooling fan shroud. Megger test reads `0.1` Mega-ohms between Phase A and ground.",
                "Phase current imbalance exceeding `22%` (`{current}` Amps Phase A vs normal Phase B/C). Motor running extremely rough.",
                "Main breaker tripped instantly upon energization. Stator surge comparison test confirmed turn-to-turn short in phase coil."
            ],
            "root_causes": [
                "Age-related thermal brittleness of Class F winding insulation accelerated by frequent motor start/stop cycles.",
                "Voltage spikes from VFD switching transients exceeded insulation dielectric breakdown threshold.",
                "Contamination of stator coils with airborne conductive dust and moisture due to missing terminal box gasket.",
                "Overloading motor beyond `1.15` service factor during peak production periods caused sustained overheating of winding copper."
            ],
            "actions": [
                "Removed motor from base plate, transported to electrical rebuild facility for complete Class H stator rewind and VPI dip.",
                "Swapped out failed motor with certified warehouse spare unit; sent damaged stator for rewind and core loss testing.",
                "Replaced motor with premium efficiency spare, installed line reactor on VFD output, and renewed terminal box seals.",
                "Performed complete motor replacement, renewed lead lugs, and verified balance and alignment with driven load."
            ],
            "parts": [
                ["Class H Stator Rewind Service", "Motor Lead Lug Kit", "Terminal Box Gasket"],
                ["Complete Replacement Induction Motor 50HP", "Coupling Key"],
                ["Stator Rewind Kit", "VFD Output Line Reactor", "Terminal Gasket"],
                ["Warehouse Spare Induction Motor Assembly", "Mounting Bolt Set"]
            ],
            "downtime": (8.0, 12.0)
        },
        "overheating": {
            "symptoms": [
                "Motor frame temperature exceeding `{temp}`\u00b0C measured across cooling fins. RTD sensors indicating winding temp near `145\u00b0C` alarm limit.",
                "Thermal overload relay tripped after 3 hours of continuous running. Cooling fan shroud feels {adj} hot to the touch.",
                "Ops reported strong heat waves radiating from motor frame and `{degree}` drop in operating speed (`RPM`).",
                "Stator RTD temperature alarm active. Motor drawing `{current}` Amps (`98%` FLA) with {adj} thermal buildup on frame."
            ],
            "root_causes": [
                "External cooling fins heavily caked with thick industrial dust and grease, reducing convective heat transfer by `> 60%`.",
                "External cooling fan cover grid clogged with lint and debris, blocking cooling airflow across motor frame.",
                "Voltage unbalance of `3.8%` across supply lines caused `35%` increase in localized rotor/stator heating.",
                "Running motor at low RPM (`< 20 Hz`) via VFD without auxiliary blower forced-air cooling."
            ],
            "actions": [
                "De-energized motor, removed fan cover, and thoroughly cleaned cooling fins and fan blades using dry compressed air and degreaser.",
                "Cleared blockage from cooling fan intake grid, washed frame fins, and verified balanced supply voltage (`460V` +/- 1%).",
                "Installed auxiliary cooling blower unit for low-speed VFD operation and cleaned existing motor frame cooling channels.",
                "Corrected upstream tap settings on transformer to balance phase voltage and deep cleaned motor heat sink fins."
            ],
            "parts": [
                ["Industrial Degreaser Solvent (2 Cans)", "Replacement Fan Guard Screws"],
                ["None"],
                ["Auxiliary Forced-Air Blower Kit 460V", "Fan Shroud Mounting Brackets"],
                ["Cooling Fan Blade Assembly", "Shroud Fasteners"]
            ],
            "downtime": (1.5, 4.0)
        },
        "rotor imbalance": {
            "symptoms": [
                "1X RPM radial vibration (`{vibe}` in/sec RMS) dominant across both motor bearing housings. Vibration amplitude increases with motor speed.",
                "High horizontal vibration measured at motor drive-end (`{degree}` above ISO 10816 alarm threshold). Unit humming loudly.",
                "Strong physical vibration felt on motor baseplate. Spectrum analysis confirms pure once-per-revolution imbalance frequency.",
                "Motor shaking severely (`{vibe}` in/sec RMS) right after routine cleaning. No electrical anomalies detected on phase currents."
            ],
            "root_causes": [
                "Loss of balancing weight from cooling fan or rotor end ring due to vibration fatigue over extended service.",
                "Uneven accumulation of heavy dried process cake/dirt inside rotor cooling channels and external fan blades.",
                "Thermal bowing of rotor shaft caused by previous localized stator winding hotspot during high load run.",
                "Slight bending of motor shaft resulting from historical mechanical jam on driven equipment coupling."
            ],
            "actions": [
                "Disassembled cooling fan shroud, cleaned rotor assembly, and performed in-situ two-plane dynamic field balancing using balancing trim weights.",
                "Removed rotor from stator, cleaned debris from cooling slots, checked shaft runout on lathe, and dynamically balanced rotor to G2.5 grade.",
                "Replaced cracked external cooling fan, cleaned rotor end rings, and applied trim balance weights to drive-end balance plane.",
                "Re-balanced rotor assembly in field using dual-channel vibration analyzer, reducing 1X peak below 0.05 in/sec RMS."
            ],
            "parts": [
                ["Dynamic Balancing Trim Weight Kit", "Fan Shroud Fasteners"],
                ["Replacement Cooling Fan Assembly", "Shaft Key", "Balancing Weights"],
                ["Rotor Balancing Clip Set", "External Cooling Fan"],
                ["None"]
            ],
            "downtime": (4.5, 8.5)
        }
    },
    "Air Compressor": {
        "valve failure": {
            "symptoms": [
                "Compressor unable to build discharge pressure above `{press}` PSI. High interstage temperature (`{temp}`\u00b0C) on stage 1 cylinder.",
                "Loud {adj} metallic clicking and {noise} inside compressor cylinder head during compression stroke. Capacity down by `{degree}`.",
                "High discharge temperature trip (`> 110\u00b0C`) activated. Air blowing back through intake air filter assembly during unloader cycle.",
                "Ops noted compressor running continuously without unloading (`{current}` Amps draw) and failing to reach header setpoint."
            ],
            "root_causes": [
                "Fatigue fracture of stainless steel valve plate/reed inside discharge valve assembly due to billions of cyclic flexures.",
                "Carbon deposit buildup on valve seat caused by oil carryover and high operating temperatures, preventing tight valve sealing.",
                "Broken valve spring allowed valve disc to flutter and slam against guard, cracking valve seating surface.",
                "Ingestion of particulate grit through torn air intake filter element eroded suction valve sealing face."
            ],
            "actions": [
                "Isolated compressor, removed cylinder head, and replaced complete suction and discharge valve assemblies and gaskets.",
                "Disassembled valve pockets, cleaned carbon buildup using chemical solvent, and installed new reed valve rebuild kits.",
                "Replaced broken stage 1 and stage 2 discharge valve assemblies, renewed head gaskets, and replaced intake air filter element.",
                "Installed new valve plates, springs, and seats; torqued head bolts to factory specification and tested capacity."
            ],
            "parts": [
                ["Suction and Discharge Valve Assembly Kit", "Cylinder Head Gasket Set"],
                ["Valve Rebuild Kit (Plates, Springs, Seats)", "High-Temp Head Gaskets"],
                ["Stage 1 Discharge Valve Assembly", "Stage 2 Valve Kit", "Intake Filter Element"],
                ["Reed Valve Replacement Pack", "Valve Cover O-Ring Set"]
            ],
            "downtime": (3.5, 6.5)
        },
        "oil contamination": {
            "symptoms": [
                "Oil sight glass shows {adj} dark, foamy oil with heavy sludge formation. Compressor running `{temp}`\u00b0C above normal discharge temp.",
                "High differential pressure alarm (`> 15 PSI`) triggered across air/oil separator element. Excessive oil carryover into plant air header.",
                "Oil analysis report indicates high acid number (TAN > 1.5) and severe particulate depletion of anti-wear additives.",
                "Compressor oil filter bypass indicator tripped red. Tech observed `{degree}` oil varnish buildup inside reservoir sampling port."
            ],
            "root_causes": [
                "Operating compressor past recommended 8,000-hour oil change interval caused thermal oxidation and breakdown of synthetic lubricant.",
                "Ingestion of humid, chemically contaminated intake air from nearby chemical processing bath accelerated oil sludge formation.",
                "Mixing of incompatible lubricant brands during top-off by operations caused chemical precipitation and foaming.",
                "Failure of thermostatic bypass valve caused oil to run continuously chilled, allowing condensate moisture to emulsify with oil."
            ],
            "actions": [
                "Drained degraded compressor oil, flushed oil sump with cleaning solvent, replaced air/oil separator and oil filter, and refilled with synthetic ISO VG 46 oil.",
                "Performed complete oil system flush, replaced spin-on oil filter and separator cartridge, and verified thermostatic valve operation.",
                "Drained contaminated fluid, replaced thermostatic mixing valve element, renewed filters, and filled with certified compressor lubricant.",
                "Flushed reservoir, replaced oil filter and separator element, cleaned thermal bypass valve, and took fresh baseline oil sample."
            ],
            "parts": [
                ["Synthetic Compressor Oil ISO VG 46 (5 Gal)", "Air/Oil Separator Element", "Spin-On Oil Filter"],
                ["Oil Filter Cartridge", "Separator Kit", "Compressor Flushing Fluid (2 Gal)", "Synthetic Lube Oil"],
                ["Thermostatic Bypass Valve Element", "Oil Filter Assembly", "Separator Element", "ISO VG 46 Lube"],
                ["Complete Maintenance Filter & Oil Kit (Separator, Oil Filter, Air Filter, Oil)"]
            ],
            "downtime": (2.0, 4.5)
        },
        "overheating": {
            "symptoms": [
                "High air discharge temperature trip (`{temp}`\u00b0C) shut down compressor package. Oil cooler radiator feels {adj} hot across all passes.",
                "Compressor cycling on high temp interlock (`> 105\u00b0C`). Cooling fan running but `{degree}` temperature drop across aftercooler.",
                "Thermal warning alarm active on compressor controller. Unit operating at `{current}` Amps with {adj} heat buildup inside acoustic enclosure.",
                "Air discharge temp steadily climbing over past 48 hours, reaching `{temp}`\u00b0C during peak shift demands."
            ],
            "root_causes": [
                "External fins of air/oil cooler core heavily fouled with industrial airborne dust and oily mist accumulation.",
                "Thermal bypass valve failed in closed position, preventing hot oil from circulating through external cooler core.",
                "Internal oil cooler passages partially plugged with oil varnish deposits, reducing heat transfer efficiency.",
                "Low oil level in compressor sump due to gradual carryover past aging separator element."
            ],
            "actions": [
                "Pressure washed air/oil cooler radiator exterior fins with biodegradable degreaser and blown dry with low-pressure air.",
                "Replaced faulty thermostatic oil bypass valve assembly, topped off compressor oil level, and cleaned cooler core exterior.",
                "Circulated chemical descaling/de-varnishing agent through internal cooler passages, flushed system, and replaced oil filter.",
                "Cleaned cooler core fins, adjusted cabinet ventilation louvers, and verified discharge temperature stabilized at 82\u00b0C under full load."
            ],
            "parts": [
                ["Coil Cleaning Degreaser (2 Gallons)", "Replacement Cooler Core Gaskets"],
                ["Thermostatic Oil Bypass Valve Kit", "Compressor Oil (1 Gal)", "O-Ring Set"],
                ["De-Varnishing Chemical Flush (5 Gal)", "Spin-On Oil Filter", "Cooler Gasket Kit"],
                ["Cabinet Ventilation Filter Pad", "Oil Top-off Bottle"]
            ],
            "downtime": (2.5, 5.0)
        },
        "belt wear": {
            "symptoms": [
                "Loud {adj} squealing and {noise} sound from compressor drive belt guard during startup and loading cycles.",
                "Belt slip alarm triggered (`{degree}` RPM mismatch between motor and compressor end). Black rubber dust accumulating under drive guard.",
                "Drive belts show {adj} side wear, fraying cords, and glazing across pulley contact surfaces. Tension significantly degraded.",
                "Tech observed visual vibration and whipping of drive belts across sheaves (`{vibe}` in/sec RMS on bearing frame)."
            ],
            "root_causes": [
                "Normal mechanical wear and stretching of V-belts after exceeding 12,000 hours of continuous loading/unloading duty.",
                "Improper initial belt tensioning (`too loose`) allowed slippage and frictional glazing during high torque starts.",
                "Misalignment between motor drive sheave and compressor driven sheave (`> 0.5 degrees`) caused rapid sidewall abrasion.",
                "Oil mist drip from minor shaft seal leak contaminated V-belt rubber, causing softening and loss of grip."
            ],
            "actions": [
                "Locked out unit, removed belt guard, replaced matched set of 4 V-belts, laser aligned sheaves, and tensioned to sonic gauge spec (`45 Hz`).",
                "Replaced worn drive belt set, realigned motor sheave using precision laser tool, and re-tensioned after 24-hour run-in.",
                "Cleaned oil mist off sheave grooves using solvent, installed new matched V-belt set, and adjusted motor slide base tension.",
                "Swapped out glazed V-belts with new matched set, verified pulley groove profiles for wear, and torqued slide rail bolts."
            ],
            "parts": [
                ["Matched Set of 4 V-Belts (VX-120)", "Sheave Bushing Kit"],
                ["Heavy Duty V-Belt Set (3-Pack)", "Solvent Cleaner (1 Can)"],
                ["Cogged V-Belt Matched Set (BX-68)", "Slide Base Bolt Set"],
                ["Replacement Drive Belt Kit", "Sheave Lock Bushings"]
            ],
            "downtime": (1.5, 3.5)
        }
    },
    "Refrigerated Air Dryer": {
        "refrigerant leak": {
            "symptoms": [
                "Air dryer dew point gauge reading `{temp}`\u00b0C (high dew point alarm active). Suction pressure on refrigerant compressor reading near `0` PSI.",
                "Compressor short cycling on low-pressure cutout switch. Tech observed {adj} oil residue on copper brazed joint near evaporator.",
                "Compressed air exiting dryer feels humid (`{degree}` moisture present). Refrigerant sight glass shows bubbles and low charge indicator.",
                "Dryer refrigeration compressor hot to touch (`{temp}`\u00b0C) and tripping on low suction pressure cutoff during afternoon shift."
            ],
            "root_causes": [
                "Vibration fatigue cracked copper capillary tube at brazed connection to hot gas bypass valve manifold.",
                "Corrosion pinhole developed inside air-to-refrigerant heat exchanger due to acidic condensate accumulation.",
                "Fretting wear between rubbing copper refrigerant lines inside cabinet wore through tubing wall over time.",
                "Degraded Schrader access valve core O-ring allowed slow loss of R-134a/R-407C refrigerant charge over past 6 months."
            ],
            "actions": [
                "Recovered remaining refrigerant charge, repaired cracked capillary tube brazed joint with 15% silver solder, evacuated to 500 microns, and weighed in factory charge of R-134a.",
                "Located leak using electronic leak detector, repaired rubbed copper tubing section, replaced liquid line filter drier, evacuated system, and recharged with R-407C.",
                "Replaced leaking Schrader valve cores and service caps, pulled deep vacuum to verify holding, and recharged refrigerant to nameplate specification.",
                "Repaired pinhole braze leak at evaporator inlet header, installed new bi-flow filter drier, and charged unit with precise weight of R-134a."
            ],
            "parts": [
                ["R-134a Refrigerant (5 lbs)", "Liquid Line Filter Drier", "15% Silver Braze Rods"],
                ["R-407C Refrigerant Charge (8 lbs)", "Hermetic Filter Drier", "Copper Tubing Section"],
                ["Schrader Valve Cores & Brass Caps", "R-134a Refrigerant (4 lbs)", "Filter Drier Element"],
                ["Filter Drier Core Assembly", "Braze Alloy", "R-134a Refrigerant Bottle"]
            ],
            "downtime": (3.5, 7.0)
        },
        "condensate drain clog": {
            "symptoms": [
                "Liquid water blowing down downstream compressed air lines (`{degree}` moisture in plant header). Dryer automatic drain valve silent.",
                "Water sight level glass on moisture separator bowl completely full of liquid. Electronic drain solenoid clicking but no water discharging.",
                "High condensate water level alarm triggered on air dryer separator basin. Water pooling (`{degree}`) around bottom cabinet base.",
                "Ops noted heavy liquid water spray when blowing down downstream pneumatic regulator bowls. Dryer separator drain stuck closed."
            ],
            "root_causes": [
                "Accumulation of rust scales, pipe dope, and oily emulsion sludge clogged inlet strainer of electronic zero-loss drain valve.",
                "Solenoid coil burnout on automatic condensate drain valve (`open circuit` measured across coil terminals).",
                "Internal float mechanism of pneumatic zero-loss drain jammed shut due to heavy rust particles from aging inlet piping.",
                "Degradation of drain valve internal diaphragm/seal preventing pilot opening during timed drain discharge cycles."
            ],
            "actions": [
                "Isolated and bypassed drain line, disassembled electronic zero-loss drain valve, cleaned strainer mesh of rust sludge, and rebuilt solenoid valve.",
                "Replaced burned-out 24V solenoid coil and internal diaphragm repair kit on automatic condensate drain assembly; tested manual blowdown.",
                "Replaced jammed internal float assembly with upgraded heavy-duty electronic zero-loss condensate drain trap and flushed separator bowl.",
                "Disassembled and cleaned moisture separator sump, installed new drain solenoid valve rebuild kit, and verified timed discharge cycles."
            ],
            "parts": [
                ["Electronic Zero-Loss Drain Solenoid Valve Rebuild Kit", "Drain Strainer Mesh"],
                ["24V Drain Solenoid Coil", "Diaphragm Repair Kit", "Bowl O-Ring"],
                ["Heavy-Duty Electronic Drain Trap Assembly", "Strain Mesh Filter"],
                ["Automatic Drain Rebuild Kit", "Separator Bowl Gasket"]
            ],
            "downtime": (1.0, 3.0)
        },
        "compressor fault": {
            "symptoms": [
                "Refrigeration compressor tripped internal thermal overload switch. Hermetic shell burning hot (`{temp}`\u00b0C) with zero cooling output.",
                "Loud {adj} humming and `{current}` Amps locked rotor current when compressor attempts to start. Main breaker trips after 3 seconds.",
                "Hermetic compressor making severe {adj} internal clattering {noise}. Suction and discharge pressures equalized while running.",
                "Dryer refrigeration compressor failing to start (`{current}` Amps draw). High dew point alarm (`> 15\u00b0C`) active on panel."
            ],
            "root_causes": [
                "Mechanical seizure of hermetic scroll/reciprocating compressor internal bearings due to prolonged loss of oil return from system.",
                "Electrical burnout of compressor start/run capacitor (`capacitance measured 0 uF vs 45 uF rating`) preventing motor start.",
                "Internal discharge valve reed fracture inside hermetic shell causing complete loss of pumping capacity.",
                "Single-phasing or severe voltage dip on incoming feed damaged hermetic compressor start winding."
            ],
            "actions": [
                "Replaced start and run capacitors along with potential relay; tested hermetic compressor windings (`resistance OK`) and successfully restarted unit.",
                "Recovered refrigerant, cut out mechanically seized hermetic compressor, brazed in exact replacement compressor and filter drier, evacuated, and weighed in fresh R-134a charge.",
                "Replaced failed compressor start kit (capacitor + relay), checked contactor tips, and verified smooth compressor running draw (`6.5 Amps`).",
                "Replaced internal hermetic refrigeration compressor assembly, installed new suction/liquid line filter driers, pulled deep vacuum, and recharged system."
            ],
            "parts": [
                ["Compressor Run Capacitor 45uF", "Start Relay Kit", "Contactor"],
                ["Replacement Hermetic Refrigeration Compressor Assembly", "Bi-Flow Filter Drier", "R-134a Charge (6 lbs)"],
                ["Hard Start Capacitor Kit", "Compressor Contactor 24V"],
                ["Hermetic Scroll Compressor Unit", "Liquid Line Drier", "R-407C Refrigerant (8 lbs)"]
            ],
            "downtime": (4.0, 8.5)
        }
    },
    "Centrifugal Chiller": {
        "refrigerant leak": {
            "symptoms": [
                "Chiller low refrigerant charge warning alarm triggered. Condenser approach temperature `{degree}` elevated (`> 4.5\u00b0C`).",
                "Purge unit running excessively (`> 45 minutes per hour` exhausting non-condensables). Tech noted {adj} oil film near rupture disc flange.",
                "Chiller tripped on low evaporator pressure cutout during pull-down. Sight glass on liquid line shows continuous stream of bubbles.",
                "Evaporator level sensor indicating low charge (`{degree}` drop). Purge pump-out frequency increased `300%` over baseline."
            ],
            "root_causes": [
                "Degraded elastomeric O-ring seal on condenser relief/rupture disc flange assembly allowing gradual low-pressure refrigerant seepage.",
                "Corrosion pinhole in evaporator copper tube sheet bundle caused by winter freeze-thaw or aggressive chilled water treatment.",
                "Thermal expansion cycles loosened flange bolts on compressor suction elbow connection O-ring groove.",
                "Leaking shaft seal on open-drive centrifugal compressor assembly caused by drying out of seal face carbon during extended winter shutdown."
            ],
            "actions": [
                "Performed thorough leak search using heated diode detector, located leak at rupture disc flange, recovered charge, replaced rupture disc and O-ring gasket, evacuated to 300 microns, and re-trimmed R-134a charge.",
                "Eddy current tested evaporator tube bundle, identified 2 leaking copper tubes, plugged tubes using brass tapered drive plugs, evacuated chiller shell, and restored virgin R-134a charge.",
                "Replaced degraded compressor suction elbow O-ring seal and rupture disc assembly, pulled 24-hour deep vacuum test, and charged unit with 120 lbs of R-134a.",
                "Replaced open-drive compressor mechanical shaft seal assembly, renewed oil separation filters, evacuated system, and verified zero leak rate."
            ],
            "parts": [
                ["Carbon Steel Rupture Disc Assembly", "Neoprene Flange O-Ring", "R-134a Refrigerant (120 lbs)"],
                ["Brass Tapered Tube Plugs (4-Pack)", "Epoxy Sealer", "R-134a Top-off Charge (85 lbs)"],
                ["Suction Elbow O-Ring Kit", "Rupture Disc Gasket", "R-134a Refrigerant (100 lbs)"],
                ["Centrifugal Compressor Shaft Seal Assembly", "Oil Filter Element", "R-134a (65 lbs)"]
            ],
            "downtime": (8.0, 12.0)
        },
        "compressor bearing wear": {
            "symptoms": [
                "High oil temperature alarm (`{temp}`\u00b0C) and `{degree}` drop in differential oil pressure across centrifugal compressor thrust bearing.",
                "High frequency vibration (`{vibe}` in/sec RMS) detected on compressor gear case housing. Oil analysis confirms elevated copper (`> 45 ppm`).",
                "Loud {adj} high-pitched whining and {noise} inside compressor housing during guide vane modulation.",
                "Compressor bearing oil delta-P low warning. Tech noted {adj} metal shimmer in oil sump sight glass during run."
            ],
            "root_causes": [
                "Loss of hydrodynamic oil film stability due to refrigerant dilution in oil sump during low-load surge operation.",
                "Normal fatigue wear of journal and thrust hydrodynamic babbitt bearings after 35,000 hours of high-speed centrifugal duty.",
                "Partial restriction in bearing oil supply pressure regulator valve starved thrust bearing during rapid load changes.",
                "Repeated compressor surging over past cooling season subjected thrust bearing to severe axial shock loads."
            ],
            "actions": [
                "Locked out chiller, recovered charge, opened compressor housing, replaced high-speed journal and thrust babbitt bearings, cleaned oil sump, and renewed oil filters and synthetic charge.",
                "Disassembled compressor drive end, installed new precision babbitt bearing set, calibrated oil pressure regulating valve, and performed full oil flush.",
                "Replaced worn high-speed thrust bearing pad assembly, renewed internal oil filter element, and filled compressor with fresh POE oil.",
                "Performed complete compressor top-end overhaul, replacing high-speed shaft bearings and thrust collar; inspected impeller clearances and renewed gaskets."
            ],
            "parts": [
                ["High-Speed Babbitt Journal Bearing Set", "Thrust Bearing Assembly", "POE Compressor Oil (10 Gal)", "Oil Filter Element"],
                ["Precision Thrust Bearing Pad Kit", "Internal Oil Filter Cartridge", "Compressor Gasket Set", "Synthetic POE Lube"],
                ["Centrifugal Bearing Rebuild Kit (Journal & Thrust)", "Oil Sump Gasket Set", "POE Oil Charge (8 Gal)"],
                ["Thrust Collar Assembly", "High-Speed Bearings", "O-Ring Overhaul Kit", "POE Refrigeration Oil"]
            ],
            "downtime": (10.0, 12.0)
        },
        "tube fouling": {
            "symptoms": [
                "Condenser approach temperature elevated to `{temp}`\u00b0C (`normal < 1.5\u00b0C`). Chiller head pressure running `{press}` PSI above design.",
                "Chiller efficiency degraded (`kW/ton up by {degree}`). Condenser water inlet/outlet delta-T reduced to `3.2\u00b0C` (`normal 5.5\u00b0C`).",
                "High condenser pressure warning alarm active on panel. Compressor running at `100%` guide vane opening to satisfy chilled water loop.",
                "Ops noted chiller struggling to maintain `7\u00b0C` chilled water setpoint (`{degree}` deficit) during afternoon peak load due to high head pressure."
            ],
            "root_causes": [
                "Heavy calcium carbonate mineral scale and biological slime deposition inside copper condenser tubes due to cooling tower water chemical treatment lapse.",
                "Accumulation of mud, silt, and cooling tower scale debris blocking water flow across passes inside condenser water boxes.",
                "Bio-fouling and algae growth inside condenser tubes forming insulating biofilm layer after chemical biocide dosing pump failure.",
                "Corrosion oxide layer and scale buildup on internally enhanced copper tube rifling reducing overall heat transfer coefficient by `45%`."
            ],
            "actions": [
                "Isolated condenser water loop, removed end covers, performed mechanical rotary brush tube cleaning across all 450 condenser tubes, and flushed out scale debris.",
                "Circulated inhibited acid descaling solution through condenser bundle for 8 hours, neutralized loop, and mechanically brushed tubes to bare copper.",
                "Removed condenser water heads, cleared heavy silt/debris from pass ribs, brushed tube bundle with nylon/copper brushes, and renewed end cover gaskets.",
                "Performed full mechanical tube brushing of condenser and evaporator tube sheets, flushed bundles with clean water, and calibrated automatic water treatment controller."
            ],
            "parts": [
                ["Condenser Water Box Gaskets (Set of 2)", "Rotary Tube Brushes 3/4-inch (6-Pack)"],
                ["Inhibited Acid Descaling Chemical (20 Gallons)", "Neutralizer Powder", "Head Gasket Set"],
                ["Water Box End Cover Gaskets", "Nylon Replacement Tube Brushes (10-Pack)"],
                ["Neoprene Head Gaskets (Set of 4)", "Heavy-Duty Tube Cleaning Brushes"]
            ],
            "downtime": (6.0, 9.5)
        }
    },
    "Cooling Tower": {
        "fan motor failure": {
            "symptoms": [
                "Cooling tower fan motor tripped VFD/overload breaker. Motor frame burning hot (`{temp}`\u00b0C) with `{degree}` smoke from terminal box.",
                "Loud {adj} grinding {noise} sound from cooling tower fan gearbox/motor coupling. Fan blades spinning erratically.",
                "VFD indicating ground fault trip on cooling tower fan feed. Megger test shows dead short (`0.02 Mega-ohms`) on motor leads.",
                "Cooling tower basin water temperature rising above `32\u00b0C` alarm setpoint (`{degree}` spike). Fan motor stationary (`0 Amps` draw)."
            ],
            "root_causes": [
                "Moisture and corrosive cooling tower mist penetrated motor terminal enclosure, causing insulation breakdown across stator leads.",
                "Severe bearing seizure due to water wash-out of grease in vertical fan motor lower bearing during heavy monsoon/spray conditions.",
                "Phase loss on 460V incoming feed caused single-phasing thermal burnout of cooling tower induction motor windings.",
                "Prolonged operation in saturated 100% humidity environment degraded Class F insulation varnish beyond dielectric limit."
            ],
            "actions": [
                "Removed failed cooling tower fan motor using crane, installed severe-duty TEFC replacement motor, renewed shaft alignment, and sealed terminal box with RTV.",
                "Swapped out burned cooling tower fan motor with spare severe-duty VFD-rated motor, replaced flexible shaft coupling, and verified fan pitch balance.",
                "Installed new vertical fan drive motor, renewed motor shaft seal and rain canopy, greased bearings with waterproof grease, and tested VFD speed steps.",
                "Replaced fan motor and gearbox shaft coupling element, sealed conduit connections against moisture ingress, and performed laser alignment."
            ],
            "parts": [
                ["Severe-Duty TEFC Cooling Tower Motor 25HP", "Composite Coupling Element", "RTV Silicone Sealant"],
                ["Replacement Cooling Tower Induction Motor", "Flexible Drive Shaft Coupling", "Motor Rain Canopy"],
                ["Inverter-Duty Fan Motor Assembly", "Lower Bearing Waterproof Lip Seal", "Mounting Hardware Kit"],
                ["Severe-Duty Fan Motor 30HP", "Shaft Coupling Kit", "Waterproof Conduit Gland Set"]
            ],
            "downtime": (5.0, 9.0)
        },
        "scale buildup": {
            "symptoms": [
                "Heavy white/brown mineral scale (`{degree}` crust thickness) visible on PVC fill media and drift eliminators during weekly inspection.",
                "Cooling tower water distribution nozzles partially clogged with lime crust, causing uneven water channeling across fill pack.",
                "Elevated approach temperature between tower basin water and wet-bulb temp (`> 5.5\u00b0C`). Fill media sagging under weight of scale deposits.",
                "Ops noted {adj} scale shedding from drift eliminators into cold water basin (`{degree}` debris accumulation near suction screen)."
            ],
            "root_causes": [
                "High cycles of concentration (`> 6.0`) operated without adequate bleed-off rate due to stuck automatic conductivity blowdown valve.",
                "Failure of chemical scale inhibitor/dispersant dosing pump allowed calcium carbonate hardness to exceed saturation index.",
                "Seasonal evaporation concentration combined with hard makeup water (`> 250 ppm calcium`) in absence of softening pretreatment.",
                "Improper pH control (`pH > 8.8`) caused rapid precipitation of calcium and magnesium scale across warm PVC fill surfaces."
            ],
            "actions": [
                "Pressure washed PVC fill pack and drift eliminators with low-pressure wide-fan nozzle, repaired conductivity blowdown valve, and calibrated chemical dosing.",
                "Circulated bio-dispersant and mild descaling agent through tower loop for 12 hours, flushed cold water basin, and serviced bleed-off solenoid.",
                "Manually cleaned clogged distribution nozzles, pressure washed top deck and fill media, replaced broken fill sections, and reset blowdown conductivity controller to 1500 uS/cm.",
                "Descaled distribution header and nozzles, vacuumed scale debris from cold water basin, and repaired chemical scale inhibitor dosing pump tubing."
            ],
            "parts": [
                ["Cooling Tower Spray Nozzles (12-Pack)", "Conductivity Blowdown Solenoid Valve Rebuild Kit"],
                ["Cooling Tower Descaling Chemical (15 Gal)", "Bio-Dispersant (5 Gal)", "Replacement PVC Fill Block Sections (4 Bundles)"],
                ["Distribution Nozzle Replacement Set (20-Pack)", "Conductivity Controller Probe", "Chemical Pump Peristaltic Tubing"],
                ["Replacement Fill Media Bundles (2 Packs)", "Drift Eliminator Sections", "Basin Strainer Screen"]
            ],
            "downtime": (3.5, 6.5)
        },
        "water distribution blockage": {
            "symptoms": [
                "Dry patches (`{degree}` un-wetted area) visible across top of PVC fill media. Hot water basin overflowing around distribution basin edges.",
                "Multiple distribution target nozzles completely plugged with debris, causing heavy localized channeling and splashing inside tower.",
                "Cooling efficiency degraded (`{degree}` higher leaving water temp). Inspection showed `{vibe}` in/sec vibration from water hammering in header.",
                "Ops reported water splashing outside tower louvers (`{degree}` drift loss). Top deck distribution basin nozzles 40% blocked with algae/silt."
            ],
            "root_causes": [
                "Accumulation of wind-blown leaves, plastic wrappers, and organic debris in hot water distribution basin plugging nozzle orifices.",
                "Severe algae and biological slime mats broke loose from distribution header piping and lodged inside target spray nozzles.",
                "Rust flakes and pipe corrosion scales from upstream carbon steel condenser water piping carried into tower distribution header.",
                "Broken distribution basin covers allowed direct sunlight ingress, accelerating rapid algae growth that blinded distribution target nozzles."
            ],
            "actions": [
                "Removed hot water basin covers, manually cleared leaves/debris from all distribution nozzles, pressure washed basin, and chlorinated loop.",
                "Disassembled and cleaned 36 target spray nozzles, flushed main distribution header piping, installed new coarse inlet strainer baskets, and shock-chlorinated tower.",
                "Replaced 14 broken or missing distribution nozzles, removed heavy algae mats from hot water basin deck, and installed opaque UV-blocking basin covers.",
                "Manually rodded out plugged distribution basin orifices, flushed piping network with high-pressure hose, and installed upgraded non-clog polypropylene target nozzles."
            ],
            "parts": [
                ["Polypropylene Target Spray Nozzles (15-Pack)", "Basin Cover Fasteners"],
                ["Replacement Distribution Nozzles (24-Pack)", "Coarse Mesh Inlet Strainer Basket", "Shock Biocide (5 Gal)"],
                ["UV-Blocking Basin Cover Panels (Set of 4)", "Target Nozzle Kit (10-Pack)"],
                ["Non-Clog Distribution Nozzle Assembly (18-Pack)", "Basin Sealing Gasket Strip"]
            ],
            "downtime": (2.0, 4.5)
        }
    },
    "Scroll Chiller": {
        "scroll compressor wear": {
            "symptoms": [
                "Scroll compressor making loud {adj} metallic rattling and {noise} sound (`{vibe}` in/sec RMS on frame). Compressor drawing `{degree}` low amps (`45%` FLA).",
                "Chiller circuit B unable to build differential pressure (`discharge/suction pressures nearly equal`). Scroll compressor running hot (`{temp}`\u00b0C).",
                "Internal discharge temperature trip on scroll compressor (`> 125\u00b0C`). Unit making distinct {adj} grinding sound during shutdown spindown.",
                "Scroll compressor amp draw fluctuating erratically (`{current}` Amps). Chiller failing to pull down process loop temperature (`{degree}` deficit)."
            ],
            "root_causes": [
                "Scroll tip seal wear and flank wear caused by liquid refrigerant slugging during low-ambient startup without crankcase heater energized.",
                "Fatigue fracture of internal Oldham coupling ring inside scroll set due to thousands of thermal/pressure cycles.",
                "Prolonged operation with marginal oil return caused metal-to-metal scoring between orbiting and fixed scroll wraps.",
                "Reverse rotation event caused by incorrect phase sequence during temporary generator power feed damaged scroll involute tips."
            ],
            "actions": [
                "Recovered refrigerant circuit B, cut out worn scroll compressor, brazed in exact replacement scroll compressor assembly, replaced liquid line drier, evacuated to 400 microns, and weighed in R-410A charge.",
                "Replaced failed hermetic scroll compressor unit, renewed crankcase heater and contactor, flushed piping, installed new bi-flow filter drier, and recharged system.",
                "Swapped out damaged scroll compressor with factory replacement, installed new phase monitor relay to prevent reverse rotation, pulled deep vacuum, and recharged R-410A.",
                "Replaced scroll compressor assembly, renewed suction accumulator and filter drier, verified crankcase heater continuity, and charged circuit precisely by weight."
            ],
            "parts": [
                ["Replacement Tandem Scroll Compressor Assembly (15HP)", "Bi-Flow Filter Drier Core", "R-410A Refrigerant (25 lbs)"],
                ["Hermetic Scroll Compressor 20HP", "Crankcase Heater Band 240V", "Liquid Line Filter Drier", "R-410A Charge (30 lbs)"],
                ["Scroll Compressor Unit", "Phase Monitor Protection Relay", "Filter Drier", "R-410A Refrigerant Bottle"],
                ["Scroll Compressor Replacement Assembly", "Suction Accumulator Vessel", "Filter Drier Element", "R-410A (28 lbs)"]
            ],
            "downtime": (6.0, 9.5)
        },
        "refrigerant undercharge": {
            "symptoms": [
                "Chiller circuit A short cycling on low-pressure switch (`cutout at {press} PSI`). Clear sight glass showing continuous rapid bubbles.",
                "High superheat reading (`> 18\u00b0C` at compressor suction) and low subcooling (`< 2\u00b0C`). Chiller running `100%` capacity but leaving water `{temp}`\u00b0C high.",
                "Electronic expansion valve (`EEV`) at `100%` open position but evaporator temperature remaining {degree} elevated above setpoint.",
                "Low refrigerant charge alarm active on scroll chiller controller. Tech noted {adj} oil residue on condenser header braze joint."
            ],
            "root_causes": [
                "Micro-leak at copper U-bend braze joint on air-cooled condenser coil due to continuous fan vibration and thermal cycling.",
                "Loose flare nut connection on sight glass or filter drier fitting allowing slow loss of R-410A/R-407C over past cooling season.",
                "Schrader service access valve core failed to seal completely after previous preventive maintenance pressure check.",
                "Pinhole corrosion leak on evaporator brazed plate heat exchanger refrigerant channel caused by aggressive local humidity."
            ],
            "actions": [
                "Performed electronic leak check, located micro-leak at condenser coil U-bend, recovered remaining charge, silver brazed repair, evacuated to 350 microns, and weighed in factory charge of R-410A.",
                "Tightened sight glass and filter drier flare nuts, replaced Schrader valve cores, pulled 12-hour deep vacuum, and recharged circuit A with precise weight of R-410A.",
                "Repaired leaking braze joint on liquid line header, installed new hermetic filter drier, pulled vacuum, and charged unit with 22 lbs of R-410A.",
                "Located pinhole leak at condenser inlet header using nitrogen/hydrogen tracer gas, brazed joint, renewed filter drier, and recharged system."
            ],
            "parts": [
                ["R-410A Refrigerant Charge (22 lbs)", "Liquid Line Filter Drier", "Silver Braze Alloy"],
                ["Schrader Valve Cores & Brass Seal Caps (4-Pack)", "R-410A Refrigerant (18 lbs)", "Flare Gasket Set"],
                ["Hermetic Filter Drier Assembly", "Braze Rods", "R-410A Refrigerant Cylinder"],
                ["Bi-Flow Filter Drier", "R-410A Top-off Charge (25 lbs)", "Service Port Caps"]
            ],
            "downtime": (3.5, 6.0)
        },
        "sensor fault": {
            "symptoms": [
                "Chiller controller displaying erratic leaving chilled water temperature (`reading jumps rapidly between {temp}\u00b0C and -15\u00b0C`). Unit locked out on freeze protection.",
                "Evaporator pressure transducer reading `{press}` PSI offset compared to calibrated mechanical manifold gauge. EEV hunting wildly.",
                "Scroll chiller locked out on false high discharge temperature alarm (`sensor reading 155\u00b0C` while actual pipe temp is `72\u00b0C`).",
                "Ops reported chiller not loading past `50%` capacity due to faulty return water temperature thermistor reading `{degree}` out of calibration."
            ],
            "root_causes": [
                "Moisture ingress into immersion thermistor sensor probe pocket/well caused internal short across NTC thermistor element.",
                "Calibration drift and internal bridge resistor failure inside high-pressure/low-pressure 4-20mA pressure transducer.",
                "Vibration chafing of sensor shielded wiring harness against chiller steel frame caused intermittent ground fault on sensor loop.",
                "Corrosion on multi-pin plug connection at chiller microprocessor board resulting from high ambient cabinet humidity."
            ],
            "actions": [
                "Replaced leaving chilled water NTC thermistor probe, applied thermal paste inside sensor well, and calibrated sensor offset in controller menu.",
                "Replaced faulty suction and discharge pressure transducers, renewed wiring harness connectors, and verified calibration against digital manifold.",
                "Replaced defective discharge temperature thermistor, repaired chafed sensor wiring harness with heat shrink, and cleared controller lockout.",
                "Installed new return water temperature sensor assembly, cleaned microprocessor board edge connectors with contact cleaner, and tested staging."
            ],
            "parts": [
                ["NTC Immersion Thermistor Sensor Probe", "Thermal Conductive Paste"],
                ["Suction/Discharge Pressure Transducer Kit (0-500 PSI)", "Sensor Connector Cable Assembly"],
                ["High Temperature Thermistor Probe", "Heat Shrink Tubing Kit"],
                ["Water Temperature Sensor Assembly", "Electronic Contact Cleaner Spray"]
            ],
            "downtime": (1.0, 3.0)
        }
    },
    "Power Transformer": {
        "oil leakage": {
            "symptoms": [
                "Transformer main oil level gauge showing `{degree}` low level (`near bottom mark`). Noticeable {adj} dielectric oil pooling on concrete pad under radiator banks.",
                "Oil dripping steadily (`3-5 drops per min`) from top cover bushing turret gasket area. Transformer tank exterior coated in {adj} dust and oil.",
                "Buchholz relay minor alarm active (gas/air collection in chamber). Inspection revealed {adj} oil seep along main tank cover bolted flange (`{vibe}` vibration on fins).",
                "Ops flagged oil leakage from radiator drain valve and tap changer gasket. Dielectric oil level dropped `{degree}` below normal indicator mark."
            ],
            "root_causes": [
                "Age-related hardening, shrinkage, and compression set of nitrile rubber gaskets on main tank cover and bushing flanges after 15 years of outdoor exposure.",
                "Thermal expansion and contraction cycles loosened bolted flange connections across cooling radiator bank manifolds.",
                "Corrosion pinhole developed at bottom weld seam of external cooling radiator fin due to water pooling and debris trapping.",
                "Degraded O-ring seal on no-load tap changer shaft assembly allowing slow weepage of insulating mineral oil under static head pressure."
            ],
            "actions": [
                "De-energized and grounded transformer, lowered oil level slightly, re-torqued main cover and bushing flange bolts in crisscross pattern, and topped off with degassed mineral oil.",
                "Isolated transformer, replaced degraded bushing turret gaskets and radiator flange gaskets using nitrile cork sheets, vacuum treated and topped off dielectric oil.",
                "Repaired leaking radiator weld seam using approved epoxy/brazing procedure, replaced tap changer O-ring seal, and refilled transformer with certified Type II dielectric mineral oil.",
                "Re-torqued all exterior radiator and cover flange bolts to 45 ft-lbs, replaced leaking drain valve assembly, topped off insulating oil, and pulled oil sample for DGA test."
            ],
            "parts": [
                ["Nitrile-Cork Transformer Gasket Sheet Kit", "Type II Inhibited Dielectric Mineral Oil (15 Gallons)", "Flange Bolt Set"],
                ["Bushing Turret Gasket Set", "Radiator Flange O-Rings (Pack of 8)", "Dielectric Transformer Oil (25 Gallons)"],
                ["Tap Changer Shaft O-Ring Kit", "Transformer Drain Valve 2-inch", "Inhibited Mineral Oil (10 Gal)"],
                ["Complete Transformer Sealing Gasket Kit", "Dielectric Oil Top-off Drums (20 Gal)"]
            ],
            "downtime": (6.0, 10.5)
        },
        "winding insulation degradation": {
            "symptoms": [
                "Dissolved Gas Analysis (DGA) annual oil sample showed elevated acetylene (`> 15 ppm`) and hydrogen (`> 300 ppm`), indicating internal arcing/partial discharge.",
                "Power factor / Tan-Delta test on transformer windings increased to `1.8%` (`normal < 0.5%`). Furan analysis indicates severe Kraft paper insulation aging (`DP < 250`).",
                "Transformer emitting {adj} buzzing/crackling sound inside tank (`{vibe}` in/sec RMS on shell). Ultrasonic acoustic survey detected partial discharge near HV winding.",
                "Megger insulation resistance between HV and LV windings dropped `{degree}` compared to factory baseline (`reading 250 Mega-ohms at 5kV`)."
            ],
            "root_causes": [
                "Long-term thermal degradation and chemical depolymerization of Kraft paper winding insulation caused by operating at sustained high load temperatures (`> 90\u00b0C`).",
                "Moisture ingress into dielectric oil (`water content > 35 ppm`) absorbed by cellulose paper insulation, drastically reducing breakdown voltage capacity.",
                "Transient overvoltages from switching surges and lightning strikes caused micro-perforations and partial discharge inside inter-turn paper insulation.",
                "Sludge formation from oxidized dielectric oil deposited onto winding ducts, restricting localized natural oil convection and creating severe thermal hotspots."
            ],
            "actions": [
                "Scheduled emergency outage, connected mobile vacuum oil purification/dehydration rig, circulated and dried oil to `< 8 ppm` moisture, and added metal passivator chemical.",
                "Performed on-site vacuum oil processing and Fuller's earth reclamation to remove polar compounds and acids, dried winding cellulose, and re-tested power factor (`Tan-Delta < 0.4%`).",
                "De-energized transformer, performed comprehensive electrical testing (TTR, Winding Resistance, Sweep Frequency Response Analysis), dried oil via vacuum rig, and added antioxidant additives.",
                "Processed transformer dielectric oil through vacuum dehydration unit for 48 hours, replaced silica gel breather desiccant, and recommended load reduction pending complete core/winding overhaul."
            ],
            "parts": [
                ["Fuller's Earth Filter Cartridges (Set of 6)", "Silica Gel Breather Desiccant Charge (10 lbs)", "Oil Passivator Additive (1 Gal)"],
                ["Vacuum Rig Filter Elements", "Type II Dielectric Oil Top-off (30 Gal)", "Indicating Silica Gel Desiccant"],
                ["Inhibited Dielectric Mineral Oil (50 Gal)", "Transformer Breather Assembly", "Antioxidant Oil Additive Package"],
                ["Silica Gel Desiccant Beads (15 lbs)", "Oil Filter Cores", "Gasket Set"]
            ],
            "downtime": (8.0, 12.0)
        },
        "overheating": {
            "symptoms": [
                "Top oil temperature gauge reading `{temp}`\u00b0C (`high alarm setpoint 85\u00b0C`). Winding hot-spot temperature indicator reaching `102\u00b0C` under `85%` load.",
                "Cooling radiator banks extremely hot (`{temp}`\u00b0C measured via IR camera). Multiple forced-air cooling fans not spinning (`0 Amps` fan bank draw).",
                "Transformer tripping on top-stage oil temperature relay during peak afternoon ambient temperature (`{degree}` above design).",
                "Ops reported strong heat waves radiating from transformer tank. Infrared scan showed `{degree}` localized heating around LV bushing terminations (`115\u00b0C`)."
            ],
            "root_causes": [
                "Cooling fan bank contactor failure and tripped motor circuit breakers prevented forced-air cooling (`FA stage`) from engaging during heavy load.",
                "External radiator fins heavily clogged with airborne cottonwood fluff, dust, and industrial dirt, reducing convective heat rejection by `> 50%`.",
                "Severe harmonic current loading (`THD > 15%`) from downstream VFD drives caused elevated eddy current and stray load losses inside transformer core/windings.",
                "Low dielectric oil level in main tank prevented natural circulation (`ONAN`) of hot oil through top radiator headers."
            ],
            "actions": [
                "Replaced defective cooling fan bank contactor and thermal overload relays, pressure washed radiator fins with low-pressure water, and verified all 6 cooling fans operational.",
                "Thoroughly washed exterior radiator cooling fins to remove cottonwood/dirt blockage, replaced 2 burned-out cooling fan motors, and checked oil level indicator.",
                "Replaced faulty cooling fan control thermostat switch, serviced fan bank electrical panel, cleaned radiator fins, and verified top oil temperature dropped to `71\u00b0C`.",
                "Topped off dielectric oil level to normal operating mark, cleaned radiator fin passages, and replaced loose LV bushing internal terminal palm connections."
            ],
            "parts": [
                ["Cooling Fan Contactor 3-Pole 240V", "Thermal Overload Relay", "Cooling Fan Motor 1/2 HP TEAO"],
                ["Replacement Cooling Fan Assemblies (Set of 2)", "Fan Control Thermostat Switch", "Radiator Fin Cleaner"],
                ["Fan Bank Control Relay", "Cooling Fan Motor 460V", "Type II Dielectric Oil (10 Gal)"],
                ["LV Bushing Terminal Palm Clamp Kit", "Fan Contactor Kit"]
            ],
            "downtime": (3.0, 6.5)
        }
    },
    "Main Distribution Panel": {
        "breaker trip failure": {
            "symptoms": [
                "Main molded case circuit breaker (`MCCB`) failed to trip during downstream short circuit event, causing upstream feeder breaker to clear fault.",
                "Electronic trip unit on main breaker showing fault LED flashing. Breaker fails to close or reset (`{degree}` mechanical binding in handle lever).",
                "Routine secondary injection testing revealed feeder breaker long-time and short-time trip units failed to actuate within specified curve (`> 500%` time delay).",
                "Ops reported breaker handle stuck in middle/tripped position (`{degree}` resistance). Internal mechanism clicking but contacts will not latch closed."
            ],
            "root_causes": [
                "Mechanical binding and hardening of factory grease inside breaker operating mechanism due to lack of periodic exercising over 10+ years.",
                "Electronic trip unit (`ETU`) microprocessor failure caused by voltage surge transients on control power feed.",
                "Shunt trip coil burnout (`open circuit`) preventing remote safety interlock system from opening breaker.",
                "Contact welding or severe arcing erosion across primary moving contact pads following repeated high-current fault interruptions."
            ],
            "actions": [
                "De-energized distribution panel, removed failed molded case breaker, installed new exact-replacement MCCB with calibrated electronic trip unit, and tested via secondary injection.",
                "Replaced defective electronic trip unit (`ETU`) module, lubricated mechanical latching mechanism with approved dielectric synthetic grease, and verified trip curve timing.",
                "Swapped out jammed circuit breaker assembly, installed new shunt trip accessory coil, torqued busbar connections to 275 in-lbs, and performed insulation resistance test.",
                "Replaced complete draw-out air circuit breaker (`ACB`) assembly, renewed bus terminal stabs, and verified all protection settings against engineering coordination study."
            ],
            "parts": [
                ["Replacement Molded Case Circuit Breaker (MCCB 400A)", "Busbar Mounting Hardware Kit"],
                ["Electronic Trip Unit Module (ETU Rebuild Kit)", "Synthetic Breaker Lubricating Grease (1 Tube)"],
                ["Draw-Out Circuit Breaker Assembly 800A", "Shunt Trip Coil 120VAC", "Phase Barrier Kit"],
                ["Replacement MCCB 600A Assembly", "Secondary Injection Test Plug Adapter"]
            ],
            "downtime": (4.0, 8.0)
        },
        "loose connections": {
            "symptoms": [
                "Infrared (`IR`) thermography inspection revealed severe hotspot (`{temp}`\u00b0C, `delta-T > 45\u00b0C above ambient`) on Phase B main busbar lug termination.",
                "Loud {adj} buzzing and arcing sound (`{noise}`) heard inside distribution panel enclosure. Localized {adj} discoloration on bus connection bolts.",
                "Voltage imbalance of `{degree}` across panel busbars under heavy load. Noticeable smell of heated ozone/insulation near panel vents.",
                "Phase A terminal lug glowing red under peak shift current (`{current}` Amps). Thermal imaging shows `112\u00b0C` temperature at cable-to-bus bolted joint."
            ],
            "root_causes": [
                "Thermal expansion and contraction cycles over years of fluctuating load current caused gradual loosening of bolted busbar and cable lug mechanical terminations.",
                "Improper initial torque application during installation (`bolts tightened without calibrated torque wrench or Belleville spring washers`).",
                "Vibration transmitted from nearby heavy manufacturing equipment loosened bolted terminal connections on main bus joints over time.",
                "Galvanic corrosion and oxidation between dissimilar metals (`copper cable to aluminum bus lug`) causing high joint contact resistance."
            ],
            "actions": [
                "Scheduled emergency shutdown, disassembled Phase B cable lug and busbar joint, cleaned oxidized contact faces with Scotch-Brite, applied conductive joint compound, and torqued bolts to factory spec (`275 in-lbs`) using Belleville washers.",
                "De-energized main panel, performed complete torquing check across all main bus connections and feeder breaker terminals using calibrated torque wrench, and applied anti-oxidation paste.",
                "Replaced heat-damaged Phase A and B terminal lugs, polished copper bus interfaces, applied electrical joint compound, torqued hardware to specification, and re-scanned with IR camera under load (`joint temp stabilized at 38\u00b0C`).",
                "Cleaned arced busbar contact surfaces, installed new silver-plated copper splice plates and high-tensile hardware with Belleville washers, and verified micro-ohm contact resistance (`< 15 micro-ohms`)."
            ],
            "parts": [
                ["Heavy-Duty Copper Compression Lugs (Set of 3)", "Belleville Spring Washers & Grade 8 Bolts", "Conductive Electrical Joint Compound (1 Tube)"],
                ["Silver-Plated Busbar Splice Plates (2-Pack)", "Anti-Oxidation Compound Paste", "High-Tensile Hardware Kit"],
                ["Replacement Terminal Lugs 500 MCM", "Hardware & Washer Kit", "Electrical Contact Cleaner"],
                ["None"]
            ],
            "downtime": (2.0, 5.0)
        },
        "insulation breakdown": {
            "symptoms": [
                "Main distribution panel tripped incoming feeder phase-to-ground fault protection. Strong {adj} smell of ionized electrical arc and smoke inside cabinet.",
                "Phase-to-phase flashover occurred across main busbar support insulators during humid morning startup (`{degree}` soot deposits across backplane).",
                "Megger insulation resistance check across panel busbars to ground measured `0.05 Mega-ohms` (`critical hazard threshold`).",
                "Loud {adj} tracking and crackling sound heard along red/glastic standoff insulators supporting main copper bus (`{vibe}` vibration)."
            ],
            "root_causes": [
                "Accumulation of conductive industrial dust, carbon soot, and high ambient moisture across busbar standoff insulators formed a tracking path to ground.",
                "Aging and thermal embrittlement of red Glastic/GPO-3 busbar support insulators caused micro-cracks that tracked under high voltage stress.",
                "Entry of rodents/pests into distribution cabinet through unsealed floor conduits caused direct phase-to-ground short across energized bus.",
                "Transient overvoltage strike exceeded dielectric breakdown limit of degraded busbar shrink-tubing insulation."
            ],
            "actions": [
                "Isolated main feed, cleaned soot and carbon tracking from panel interior using dielectric solvent, replaced all 6 Glastic busbar support standoff insulators, and performed 1000V Megger test (`reading > 500 Mega-ohms`).",
                "De-energized panel, replaced flashover-damaged bus support insulators and phase barriers, applied heat-shrink insulating tubing over exposed buswork, and sealed conduit entry points with duct seal.",
                "Replaced tracked busbar standoff insulators, cleaned copper bus surfaces, installed new polycarbonate phase barriers, and verified insulation resistance across all phases before re-energization.",
                "Replaced cracked standoff insulators, re-torqued bus supports, thoroughly vacuumed and solvent cleaned panel cabinet, and installed rodent screens on all cabinet ventilation louvers."
            ],
            "parts": [
                ["Glastic/GPO-3 Busbar Standoff Insulators (6-Pack)", "Dielectric Solvent Cleaner (3 Cans)", "Polycarbonate Phase Barriers (Set of 3)"],
                ["Bus Support Insulator Assembly Kit", "Heavy-Wall Busbar Heat Shrink Tubing (10ft)", "Duct Seal Compound (2 Plugs)"],
                ["Replacement Standoff Insulators (Pack of 8)", "Phase Barrier Kit", "Industrial Contact & Cabinet Cleaner"],
                ["GPO-3 Insulator Set", "Bus Mount Bolts", "Dielectric Cleaning Solvent"]
            ],
            "downtime": (6.0, 11.0)
        }
    },
    "Steam Boiler": {
        "tube leak": {
            "symptoms": [
                "Continuous loss of boiler water level requiring `{degree}` excessive makeup water feed (`makeup pump running near 100%`). High chemical consumption noted.",
                "Loud {adj} hissing and steam escaping sound (`{noise}`) audible inside furnace firebox when burner cycles off. White steam blowing out of stack.",
                "Acoustic tube leak detection alarm triggered. Boiler pressure dropping `{press}` PSI below setpoint despite burner firing at high fire.",
                "Inspection port reveals water dripping onto refractory hearth (`{degree}` pooling). Combustion efficiency analyzer shows `{temp}`\u00b0C drop in flue gas temp with high moisture."
            ],
            "root_causes": [
                "Localized waterside oxygen pitting corrosion inside fire tubes due to intermittent failure of boiler feedwater deaerator / oxygen scavenger chemical dosing.",
                "Fireside acid dew-point corrosion on outer tube walls caused by burning sulfur-bearing fuel during low-load/low-temperature operation.",
                "Thermal fatigue cracking at tube-to-tubesheet rolled/welded joint caused by rapid cold startups and thermal shock.",
                "Waterside scale accumulation (`> 1/16 inch thick`) caused localized insulating effect, leading to tube metal overheating and stress rupture."
            ],
            "actions": [
                "Isolated and cooled down boiler, opened front and rear doors, identified 3 leaking fire tubes using hydrostatic test, reamed out and cut out failed tubes, rolled and beaded in new seamless steel boiler tubes, and hydro-tested to 150 PSI.",
                "Opened fireside doors, plugged 2 leaking tubes using certified tapered steel boiler tube plugs as temporary repair, calibrated oxygen scavenger chemical dosing pump, and scheduled full retubing during summer outage.",
                "Performed complete tube replacement of bottom two passes (18 tubes), renewed front and rear refractory door gaskets, performed boil-out chemical cleaning, and verified zero drop on 4-hour hydro test.",
                "Cut out cracked fire tubes, ground out and re-welded/rolled tube-to-tubesheet joints on adjacent tubes, replaced door gaskets, and adjusted deaerator operating temperature to 105\u00b0C."
            ],
            "parts": [
                ["Seamless Steel Boiler Tubes 2.5-inch OD (Bundle of 4)", "Refractory Door Rope Gasket Kit", "Tubesheet Ferrules"],
                ["Tapered Steel Boiler Tube Plugs (Set of 4)", "High-Temperature Door Gasket Rope", "Oxygen Scavenger Chemical (10 Gal)"],
                ["Replacement Fire Tubes SA-178 (18-Pack)", "Front/Rear Boiler Door Refractory & Gasket Kit"],
                ["Boiler Tube Plug Kit", "Refractory Cement Patch (50 lb Bag)", "Door Sealing Gasket"]
            ],
            "downtime": (10.0, 12.0)
        },
        "burner malfunction": {
            "symptoms": [
                "Flame safeguard controller (`FSG`) locked out on primary flame failure during ignition sequence. Burner blower motor running but zero flame establishment.",
                "Burner flame pulsating and rumbling (`{noise}`) inside combustion chamber (`{vibe}` vibration on front plate). High CO emissions (`> 400 ppm`) on stack analyzer.",
                "Intermittent flame failure lockouts during high-to-low fire modulation transitions. Tech observed {adj} yellow, smoky flame instead of tight blue pattern.",
                "Pilot ignition spark clicking (`{noise}`) but main gas valve fails to open. Flame scanner signal strength reading `{degree}` weak (`< 1.2 Volts DC`)."
            ],
            "root_causes": [
                "UV flame scanner lens heavily fouled with soot and oil film, causing weak flame signal that dropped below holding threshold of safety relay.",
                "Gas pressure regulator diaphragm drift caused improper air-to-fuel ratio (`excessively rich mixture`) leading to flame instability and high CO.",
                "Ignition electrode spark gap misaligned or porcelain insulator cracked, preventing reliable high-voltage pilot ignition arc.",
                "Modulating linkage motor actuator slipped on damper shaft, causing combustion air damper to lag behind fuel valve opening during firing rate changes."
            ],
            "actions": [
                "Cleaned UV flame scanner lens with alcohol swab, adjusted ignition electrode spark gap to 1/8 inch, verified pilot flame signal strength (`3.5V DC`), and checked complete firing sequence.",
                "Replaced defective UV flame scanner head and ignition electrode assembly, tightened and recalibrated air/fuel modulating linkage arms, and set combustion profile using digital flue gas analyzer.",
                "Replaced main gas solenoid valve coil and faulty modulating servo motor, reset gas pressure regulator to 14 inches WC, and performed multi-point combustion efficiency tuning (`O2 set at 3.5%`).",
                "Cleaned burner diffuser and ignition assembly, replaced cracked pilot electrode ceramic, calibrated fuel/air cam profile across all firing rates, and cleared flame safeguard lockout."
            ],
            "parts": [
                ["UV Flame Scanner Sensor Head", "Ignition Electrode & Porcelain Assembly", "High-Voltage Ignition Wire"],
                ["Modulating Servo Actuator Motor", "Gas Solenoid Valve Coil 120V", "Burner Diffuser Gasket"],
                ["Flame Scanner Replacement Unit", "Ignition Transformer 10kV", "Linkage Ball Joints (4-Pack)"],
                ["Pilot Electrode Kit", "UV Scanner Lens Cleaning Swabs", "Burner Front Plate Gasket"]
            ],
            "downtime": (2.5, 5.5)
        },
        "scale buildup": {
            "symptoms": [
                "Boiler stack temperature steadily rising (`reaching {temp}\u00b0C vs design 210\u00b0C at high fire`), indicating severe loss of waterside heat transfer efficiency.",
                "Waterside inspection through handholes reveals `{degree}` thick hard calcium/silicate mineral scale crust on fire tube surfaces and furnace tube sheet.",
                "Boiler making {adj} popping and kettling sounds (`{noise}`) from waterside during high fire operation. Bottom blowdown discharging {adj} heavy scale chips.",
                "Fuel consumption increased by `18%` per ton of steam generated (`{degree}` efficiency drop). Low water cutoff float chamber fouled with sludge accumulation."
            ],
            "root_causes": [
                "Improper functioning of duplex water softener (resin exhausted or regeneration timer failure) allowed hard water (`> 120 ppm total hardness`) directly into boiler feedwater.",
                "Lack of daily bottom blowdown execution by plant operators allowed suspended solids and sludge to bake onto hot tubesheet surfaces.",
                "Under-dosing of internal boiler scale treatment chemical (`phosphate/polymer dispersant`) over past 6 months due to chemical pump air-lock.",
                "High feedwater silica concentration combined with excessive cycles of concentration formed hard, dense silicate scale that cannot be removed by normal blowdown."
            ],
            "actions": [
                "Took boiler offline, opened all handholes and manways, performed high-pressure waterside mechanical rodding/flushing of all tubes, serviced water softener resin, and calibrated chemical feed pumps.",
                "Circulated inhibited sulfamic acid descaling solution through boiler waterside loop for 16 hours, neutralized and flushed until pH neutral, inspected tubes (`scale completely cleared`), and renewed handhole gaskets.",
                "Mechanically scraped tubesheet and lower drum surfaces through handholes, flushed heavy scale debris from bottom header, rebuilt automatic surface blowdown controller, and replaced water softener resin.",
                "Performed chemical boil-out using alkaline/polymer descaling compound, flushed waterside thoroughly, replaced low-water cutoff float bowl assembly, and established rigorous daily blowdown schedule."
            ],
            "parts": [
                ["Inhibited Sulfamic Acid Boiler Descaler (30 Gallons)", "Neutralizing Compound (10 lbs)", "Handhole & Manway Gasket Set (Pack of 12)"],
                ["Water Softener Cation Resin (5 Bags)", "Boiler Handhole Gaskets (Top & Bottom Set)", "Internal Scale Treatment Chemical (15 Gal)"],
                ["Low-Water Cutoff Float Bowl Rebuild Kit", "Manway Spiral Wound Gasket", "Phosphate Scale Inhibitor (10 Gal)"],
                ["Boiler Descaling Acid Flush Kit", "Handhole Gasket Pack (16-Pack)", "Softener Valve Rebuild Kit"]
            ],
            "downtime": (6.5, 10.0)
        },
        "pressure relief valve failure": {
            "symptoms": [
                "Main safety relief valve weeping/simmering continuously (`{degree}` steam discharge through vent pipe to roof). Steam visible around valve discharge funnel.",
                "Relief valve popped off prematurely at `{press}` PSI during normal operation (`nameplate setpoint 150 PSI`). Valve fails to reseat tightly after blowing down.",
                "Safety relief valve leaking {adj} live steam (`{noise}` hissing) across seat during standby pressure. Valve body running extremely hot (`{temp}`\u00b0C).",
                "Annual boiler safety valve pop test failed: valve stuck closed during lever lifting test or opened `18 PSI` above stamped ASME set pressure."
            ],
            "root_causes": [
                "Corrosion, scale, and boiler alkalinity carryover particles lodged between safety valve disc and stainless steel nozzle seat after previous simmer event.",
                "Fatigue relaxation or corrosion of internal safety valve helical compression spring caused reduction in popping set pressure over 5+ years of continuous service.",
                "Improper pipe support on discharge vent piping exerted mechanical binding twisting strain on safety valve body, distorting internal seat alignment.",
                "Normal mechanical seat wear and wire-drawing erosion across sealing faces from prolonged minor steam weeping."
            ],
            "actions": [
                "Isolated boiler, removed leaking safety relief valve, installed certified code-stamped replacement ASME safety relief valve set at 150 PSI, and verified zero leakage under full operating pressure.",
                "Replaced primary and secondary steam safety relief valves with calibrated code-stamped spares, adjusted vent piping expansion slip joint to eliminate mechanical strain, and tested pop pressure.",
                "Swapped out defective safety valve with NBBI certified replacement assembly, renewed flange gaskets and high-tensile studs, and documented ASME pop test during firing startup.",
                "Installed new factory-calibrated and sealed safety relief valve, re-supported discharge vent pipe to ensure zero weight on valve body, and verified reseating tightness."
            ],
            "parts": [
                ["ASME Section I Code-Stamped Safety Relief Valve (1.5x2.5 inch, 150 PSI)", "Spiral Wound Flange Gasket 1.5-inch", "High-Temp Stud Bolt Set"],
                ["Certified Steam Safety Relief Valve Assembly 150 PSI", "Discharge Pipe Drip Pan Elbow", "Flange Gasket Kit"],
                ["NBBI Certified Safety Valve 2-inch", "Spiral Wound Gasket", "High-Tensile Studs & Nuts"],
                ["Replacement ASME Safety Relief Valve", "Flange Mounting Hardware"]
            ],
            "downtime": (2.5, 5.0)
        }
    },
    "Belt Conveyor": {
        "belt misalignment": {
            "symptoms": [
                "Conveyor belt mistracking severely (`{degree}` off-center toward right side). Belt edge rubbing against steel conveyor frame (`{noise}` squealing sound and rubber dust).",
                "Misalignment alignment switch alarm tripped, shutting down conveyor drive. Belt tracking edge frayed (`{degree}` wear) near head pulley area.",
                "Ops noted conveyor belt wandering back and forth across troughing idlers during load surges. Heavy material spillage (`{degree}`) accumulating under carry side.",
                "Belt running `3 inches` off-center at tail pulley return idlers. Rubbing noise (`{noise}`) and {adj} smell of hot rubber near take-up assembly."
            ],
            "root_causes": [
                "Material buildup (sticky wet clay/bulk product) frozen or caked onto head pulley and return idler rolls, creating uneven diameter and forcing belt to track to one side.",
                "Improper tension adjustment on gravity screw take-up assembly (`uneven tension between left and right take-up bearings`).",
                "Structural misalignment or frame skewing caused by forklift impact against conveyor side support legs.",
                "Splice joint cut and joined at a slight diagonal angle (`improper squareness during belt lacing/vulcanizing`), causing rhythmic mistracking every belt revolution."
            ],
            "actions": [
                "Locked out conveyor, manually scraped and cleaned hardened material buildup from head pulley and return idlers, adjusted take-up screw tension equally, and test ran belt to track center.",
                "Installed 3 self-aligning training return idlers along return span, cleaned material off tail pulley wing rolls, squared take-up bearings, and verified belt centered under full load.",
                "Re-squared conveyor structural frame, replaced 4 jammed return idler rollers, adjusted head and tail pulley parallelism using laser square, and fine-tuned tracking.",
                "Scraped caked debris from drive and tail pulleys, adjusted gravity take-up counterweight guides, realigned troughing idler brackets, and verified straight tracking across all zones."
            ],
            "parts": [
                ["Self-Aligning Training Idlers (Set of 3)", "Return Idler Rollers (4-Pack)"],
                ["Heavy-Duty Return Training Roller Assembly (2-Pack)", "Take-up Bearing Adjusting Bolt Kit"],
                ["Troughing Idler Bracket Set", "Replacement Wing Pulley Scraper Blades (2-Pack)"],
                ["Training Idler Set", "Idler Mounting Hardware Kit"]
            ],
            "downtime": (1.5, 4.0)
        },
        "roller bearing failure": {
            "symptoms": [
                "Loud {adj} screeching, grinding, and {noise} sound emanating from carry-side troughing idler roller near Station 14.",
                "Idler roller completely seized (`0 RPM rotation`). Conveyor belt sliding across stationary steel shell (`{degree}` flat spot worn into roller and hot rubber smell).",
                "Thermal inspection (`IR gun`) showed seized return idler bearing reaching `{temp}`\u00b0C. Sparks visible (`{degree}` hazard) under dark operating conditions.",
                "Multiple troughing idlers making {adj} clicking and metallic clattering sounds (`{vibe}` vibration on side rails). Bearing end caps pushed out with rusty grease."
            ],
            "root_causes": [
                "Water and abrasive bulk particulate grit penetrated idler labyrinth seals during high-pressure washdowns, causing bearing grease washout and seizure.",
                "Normal fatigue failure and spalling of internal idler ball bearings after exceeding 25,000 hours of continuous operating life under heavy impact loading.",
                "Material spillage burying return idlers completely, preventing rotation and causing bearings to overheat and lock up.",
                "Severe impact shock loading at transfer chute drop point overloaded standard idler bearings beyond static load rating."
            ],
            "actions": [
                "Locked out conveyor, removed 6 seized and noisy troughing idler assemblies along carry span, and installed new sealed-for-life CEMA C heavy-duty idler rollers.",
                "Replaced 4 seized return idlers and 2 impact bed idlers under transfer point, cleared spilled material from under structure, and verified smooth, quiet rotation.",
                "Swapped out 8 worn troughing and return rollers across Section B, upgraded loading zone to heavy-duty rubber-disc impact idlers, and aligned brackets.",
                "Performed complete idler walkaround audit, replacing 12 seized or noisy idler rollers across carry and return spans, and cleared material buildup around tail area."
            ],
            "parts": [
                ["CEMA C Troughing Idler Rollers 35-Degree (Set of 6)", "Return Idler Rollers 4-inch (4-Pack)"],
                ["Heavy-Duty Impact Troughing Idler Assemblies (Set of 2)", "Return Rollers (4-Pack)", "Idler Mounting Brackets"],
                ["Replacement Sealed Idler Rollers (Pack of 8)", "Impact Roller Kit (4-Pack)"],
                ["CEMA D Heavy-Duty Idler Roller Set (10-Pack)", "Return Idler Mounting Clips"]
            ],
            "downtime": (2.0, 5.0)
        },
        "belt tear": {
            "symptoms": [
                "Longitudinal rip (`{degree}` length, ~4 feet long) gouged into top rubber cover of conveyor belt near loading transfer chute.",
                "Belt edge torn and fraying (`{degree}` internal fabric carcass cords exposed and catching on conveyor frame brackets).",
                "Mechanical belt rip detector interlock tripped, stopping conveyor immediately. Inspection revealed {adj} puncture hole (`3x5 inch`) through entire belt thickness.",
                "Ops reported top cover rubber delaminating (`{degree}` separation) and severe edge gouging along 15 feet of conveyor belt carrying surface."
            ],
            "root_causes": [
                "Sharp piece of tramp metal or structural steel bracket broke off and wedged between skirt board and belt surface at loading chute, gouging belt during transit.",
                "Severe impact from oversized frozen boulders dropped from 8-foot height at transfer point exceeded belt carcass puncture resistance.",
                "Mechanical fastener/lacing splice pulled apart and caught on fixed belt scraper blade, ripping belt edge open.",
                "Skirt board sealing rubber improperly adjusted (`steel backing clamp dropped down`), cutting into moving belt cover like a chisel."
            ],
            "actions": [
                "Locked out unit, trimmed frayed belt edges, repaired 4-foot longitudinal top cover gouge using cold-cure urethane repair compound and rubber repair strips, and readjusted skirt board clamps.",
                "Cut out damaged 10-foot section of conveyor belt, installed new belt insert section using heavy-duty mechanical Flexco plate fasteners, and checked skirt board clearance.",
                "Performed hot vulcanized splice repair on torn belt section, removed jammed tramp metal from transfer chute, and installed new heavy-duty urethane skirt board sealing strips.",
                "Repaired puncture and edge tear using cold vulcanizing patch kit, ground smooth, replaced damaged belt cleaner blade, and verified 3/8-inch skirt board clearance."
            ],
            "parts": [
                ["Cold-Cure Urethane Belt Repair Compound Kit (2 Packs)", "Heavy-Duty Rubber Patch Strips", "Urethane Skirt Board Sealing Rubber (20ft)"],
                ["Conveyor Belt Replacement Section (3-ply, 12ft)", "Flexco Bolt Solid Plate Fasteners (Box of 25)", "Skirt Clamps"],
                ["Hot Vulcanizing Splice Kit & Gum Rubber", "Primary Belt Cleaner Scraper Blade", "Urethane Skirt Strip"],
                ["Belt Repair Cold Vulcanizing Kit", "Flexco Mechanical Fastener Set", "Rubber Skirt Rubber (15ft)"]
            ],
            "downtime": (4.5, 9.0)
        },
        "motor overload": {
            "symptoms": [
                "Conveyor drive motor tripped VFD/thermal overload relay (`motor current spiked to {current} Amps vs 32A FLA`). Drive pulley stationary while motor humming.",
                "High torque alarm active on conveyor drive controller. Motor frame temperature `{temp}`\u00b0C (`{degree}` overheating). Conveyor struggling to start under load.",
                "Conveyor stalled completely during heavy surge loading. Fluid coupling thermal fuse plug melted, discharging coupling oil (`{degree}` pool on floor).",
                "Drive motor drawing continuous `{current}` Amps (`115%` rating). Gearbox output shaft rotating sluggishly with {adj} laboring noise (`{noise}`)."
            ],
            "root_causes": [
                "Conveyor overloaded beyond maximum design capacity (`surge loading from upstream bin discharge exceeding 600 TPH`).",
                "Severe mechanical binding and increased drag caused by multiple seized idler rollers and caked material dragging against bottom belt return span.",
                "Tail pulley or take-up assembly jammed with packed solid material, creating immense frictional drag against belt movement.",
                "Faulty or misadjusted motor thermal overload relay setting (`set too low at 80% FLA`) or loose phase connection causing phase current unbalance."
            ],
            "actions": [
                "Cleared excess surge material load from belt carrying surface, freed up 6 jammed idler rollers under skirt board, reset motor thermal overload relay, and verified normal running draw (`28 Amps`).",
                "Shoveled out heavy material spillage burying tail pulley and return belt span, replaced 4 locked-up return idlers, refilled fluid coupling with fresh ISO VG 32 oil, and installed new thermal fuse plug.",
                "Cleared mechanical jam inside head pulley discharge chute, re-torqued motor terminal connections, checked gearbox oil level, and verified VFD current stability across full speed range.",
                "Excavated packed material from tail take-up frame, lubricated take-up slide ways, replaced 5 dragging idler rollers, and tested conveyor startup under standard load."
            ],
            "parts": [
                ["Fluid Coupling Thermal Fuse Plug 140\u00b0C", "ISO VG 32 Fluid Coupling Oil (2 Gallons)", "Replacement Return Idlers (4-Pack)"],
                ["Replacement Return Idlers (Set of 6)", "Motor Terminal Lug Kit"],
                ["Thermal Overload Relay Element", "Take-up Slide Lubricant (1 Can)", "Troughing Idler Rollers (4-Pack)"],
                ["Fluid Coupling Fusible Plug", "Return Rollers (5-Pack)", "Gearbox Top-off Oil"]
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
            "Gradual performance degradation (`{degree}` loss of output) and {obs} noted by rounds technician."
        ],
        "root_causes": [
            "Normal mechanical friction and surface fatigue over extended continuous operating hours.",
            "Gradual degradation of lubrication film and accumulation of airborne industrial particulates over time.",
            "Cyclic operational stress and minor environmental corrosion after multi-year service life.",
            "Routine wear and tear of consumable elastomeric and mechanical contact elements."
        ],
        "actions": [
            "Disassembled worn subassembly, replaced degraded mechanical wearing elements, lubricated moving joints, and verified operation.",
            "Renewed worn contact parts, tightened mounting hardware, performed full lubrication service, and tested unit under load.",
            "Replaced worn mechanical components, cleaned operating assembly, calibrated stroke/linkage, and restored to service.",
            "Swapped out worn operating parts with new factory spares, renewed seals, and checked running signatures."
        ],
        "parts": [
            ["Standard Mechanical Wear Kit", "O-Ring and Seal Set", "Synthetic Grease"],
            ["Replacement Linkage Assembly", "Gasket Kit", "Fastener Set"],
            ["Wear Ring & Seal Kit", "General Maintenance Lubricant"],
            ["None"]
        ],
        "downtime": (1.5, 4.5)
    },
    "sensor malfunction": {
        "symptoms": [
            "Local panel display reading erratic/unstable process values (`reading fluctuating between {temp}`\u00b0C and 0\u00b0C`). False interlock trip occurred.",
            "Control system reporting loss of sensor signal (`4-20mA loop current reading 0mA`). Unit locked out on sensor diagnostic alarm.",
            "Process transmitter reading `{press}` PSI offset from local calibrated mechanical gauge. Controller hunting wildly.",
            "Sensor calibration fault active on PLC interface. Tech observed {adj} corrosion around transmitter field junction box (`{degree}` moisture)."
        ],
        "root_causes": [
            "Moisture and condensation ingress inside sensor field housing caused internal short circuit across transmitter electronic circuitry.",
            "Vibration-induced fatigue breakage of sensor internal lead wiring at terminal block inside junction box.",
            "Normal sensor sensing element calibration drift exceeding +/- 5% error tolerance after 3 years of process exposure.",
            "Corrosion on multi-pin cable connector caused by exposure to ambient washdown chemicals and high humidity."
        ],
        "actions": [
            "Replaced defective field sensor transmitter, renewed waterproof wiring gland and terminal connectors, and calibrated zero/span via HART communicator.",
            "Repaired broken lead wiring inside junction box, installed new moisture-sealed transmitter probe, and verified PLC loop reading.",
            "Swapped out faulty sensor element, cleaned cable connector pins with contact cleaner, applied dielectric grease, and cleared alarm.",
            "Installed new calibrated process transmitter, renewed conduit weather seal, and performed 3-point loop calibration check."
        ],
        "parts": [
            ["Replacement Process Transmitter Probe", "Waterproof Cable Gland", "Terminal Block"],
            ["Calibrated Sensor Assembly", "Electronic Contact Cleaner", "Dielectric Grease"],
            ["Field Sensor Replacement Unit", "Conduit Sealing Fitting"],
            ["4-20mA Sensor Transmitter", "HART Communication Patch Cable"]
        ],
        "downtime": (0.5, 2.5)
    },
    "overheating": {
        "symptoms": [
            "Unit exterior casing running hot (`{temp}`\u00b0C measured via infrared thermometer). Thermal warning indicator active on local panel.",
            "High temperature alarm tripped unit offline after 4 hours of operation. Cooling airflow feels {adj} weak across ventilation slots.",
            "Ops reported heat waves and {adj} smell of hot metal near unit enclosure (`{degree}` temperature elevation).",
            "Surface temperature reached `105\u00b0C` (`normal < 75\u00b0C`). Current draw normal (`{current}` Amps) but {adj} heat buildup present."
        ],
        "root_causes": [
            "External cooling slots and heat sink surfaces heavily blocked with industrial dust and lint, preventing adequate convective heat dissipation.",
            "Internal cooling fan motor failure or broken fan blade reduced airflow across operating components by `> 70%`.",
            "Operating unit continuously at peak maximum load during high summer ambient temperatures (`> 38\u00b0C`).",
            "Partial restriction in auxiliary cooling supply line caused elevated operating equilibrium temperatures."
        ],
        "actions": [
            "De-energized unit, thoroughly vacuumed and compressed-air cleaned cooling slots and internal heat sink surfaces, and verified temperature drop.",
            "Replaced defective internal cooling fan assembly, washed exterior cooling fins with degreaser, and verified adequate ventilation.",
            "Cleaned blocked ventilation channels, adjusted enclosure airflow louvers, and verified operating temperature stabilized below 72\u00b0C under full load.",
            "Flushed auxiliary cooling loop, cleaned fan shroud intake grid, and replaced degraded cooling fan blade."
        ],
        "parts": [
            ["Replacement Cooling Fan Assembly", "Degreaser Solvent (1 Can)"],
            ["Enclosure Cooling Fan 120V", "Filter Media Pad"],
            ["Cooling Fan Shroud & Blade Kit"],
            ["None"]
        ],
        "downtime": (1.5, 4.0)
    },
    "loose fittings": {
        "symptoms": [
            "Noticed {adj} vibration (`{vibe}` in/sec RMS) and {obs} originating from exterior mounting hardware and connecting pipe/conduit fittings.",
            "Minor fluid weepage and {adj} rattling (`{noise}`) observed at structural and pipe connections (`{degree}` loose play).",
            "Routine walkaround inspection identified loose hold-down bolts and bracket fittings (`{degree}` movement under operating vibration).",
            "Ops flagged {adj} clattering sound (`{noise}`) during unit startup. Inspection showed 3 mounting fasteners backed out significantly."
        ],
        "root_causes": [
            "Continuous operational vibration over extended runtime caused un-locking and gradual backing out of mechanical threaded fasteners.",
            "Improper torque application during previous maintenance overhauls (`fasteners not tightened to specified torque values or missing lock washers`).",
            "Thermal expansion and contraction cycles across dissimilar materials caused clamping force relaxation on bolted connections.",
            "Normal settling of mounting base pads and vibration transmitted from adjacent heavy rotating machinery."
        ],
        "actions": [
            "De-energized unit, inspected all structural and pipe fittings, applied medium-strength threadlocker, and torqued all hardware to engineering specifications using Belleville washers.",
            "Replaced worn/missing fasteners, installed split lock washers, re-torqued baseplate hold-down bolts, and verified zero vibration play.",
            "Tightened loose conduit and piping union fittings, replaced damaged gaskets, re-torqued mounting brackets, and checked alignment.",
            "Performed complete structural torquing check across unit, installed vibration-damping Belleville spring washers, and renewed hardware."
        ],
        "parts": [
            ["Grade 8 Fastener & Lock Washer Kit", "Loctite 242 Medium Strength Threadlocker (1 Bottle)"],
            ["Belleville Spring Washer Pack (20-Pack)", "Stainless Steel Bolt Set"],
            ["Replacement Union Fittings & Gaskets", "Structural Fastener Assortment Kit"],
            ["None"]
        ],
        "downtime": (1.0, 2.5)
    }
}

# Synonyms for randomized word substitution in symptom templates to ensure immense NLP variation
SYNONYMS = {
    "{adj}": ["severe", "slight", "intermittent", "excessive", "abnormal", "high", "unusual", "gradual", "heavy", "distinct", "persistent", "significant"],
    "{obs}": ["vibration", "leaking fluid", "pressure drop", "temperature spike", "rattling sound", "smoke/fumes", "erratic amp draw", "flow reduction", "thermal buildup", "acoustic noise"],
    "{noise}": ["grinding", "high-pitched squealing", "thumping", "metallic clattering", "buzzing/humming", "cavitation crackling", "hissing", "rumbling", "screeching", "clicking"],
    "{degree}": ["moderate", "severe", "slight", "noticeable", "extreme", "marked", "drastic", "minor", "sharp", "concerning"],
    "{temp}": [lambda: str(random.randint(75, 118)), lambda: str(random.randint(82, 105)), lambda: str(random.randint(90, 125))],
    "{press}": [lambda: str(random.randint(12, 48)), lambda: str(random.randint(15, 35)), lambda: str(random.randint(20, 60))],
    "{vibe}": [lambda: f"{random.uniform(0.18, 0.55):.2f}", lambda: f"{random.uniform(0.22, 0.48):.2f}", lambda: f"{random.uniform(0.15, 0.42):.2f}"],
    "{current}": [lambda: str(random.randint(38, 185)), lambda: str(random.randint(45, 140)), lambda: str(random.randint(65, 210))]
}

def generate_symptom_text(template, rel_id=None):
    """
    Substitutes placeholders with randomized synonyms and numerical values.
    Optionally appends a realistic related asset reference if rel_id is present.
    """
    text = template
    for key, values in SYNONYMS.items():
        while key in text:
            choice = random.choice(values)
            val_str = choice() if callable(choice) else choice
            text = text.replace(key, val_str, 1)
            
    if rel_id and random.random() < 0.95: # If related asset is passed, almost always append a natural reference
        phrase = random.choice(RELATIONSHIP_PHRASES).format(rel_id=rel_id)
        text = text.rstrip(".") + "." + phrase
    return text

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
                
            # Pick template and substitute
            symptom_template = random.choice(fm_data["symptoms"])
            symptom_desc = generate_symptom_text(symptom_template, rel_id=selected_rel_id)
            
            root_cause = random.choice(fm_data["root_causes"])
            action_taken = random.choice(fm_data["actions"])
            
            parts_choice = random.choice(fm_data["parts"])
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
    df_logs.to_csv(combined_csv_path, index=False, encoding="utf-8")
    print(f"\nSuccessfully saved combined work orders CSV to: {combined_csv_path}")
    
    # Save one CSV per asset_id
    rows_per_asset = {}
    for aid, group in df_logs.groupby("asset_id"):
        # Sort each asset's CSV chronologically as well
        group_sorted = group.sort_values(by="date")
        asset_csv_path = os.path.join(output_dir, f"{aid}_logs.csv")
        group_sorted.to_csv(asset_csv_path, index=False, encoding="utf-8")
        rows_per_asset[aid] = len(group_sorted)
        
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

if __name__ == "__main__":
    main()
